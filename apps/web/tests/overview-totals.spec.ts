import { expect, test } from "@playwright/test";

test("overview renders authoritative totals instead of the loaded record preview", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/workspaces/demo-org/dashboard", async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    await route.fulfill({
      response,
      json: {
        ...data,
        counts: {
          ...data.counts,
          invoices: 501,
          expenses: 207,
          contracts: 203,
          reviewed_contracts: 2,
        },
        record_months: [
          { billing_period: "2026-11", invoice_count: 501, expense_count: 207 },
        ],
      },
    });
  });
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const invoices = page.getByRole("button", {
    name: "View invoice records",
    exact: true,
  });
  await expect(invoices.locator(".metric-value")).toHaveText("501");
  await expect(invoices.locator(".metric-origin")).toContainText(
    "of 501 sources loaded",
  );
  await expect(
    page
      .getByRole("button", { name: "View expense records", exact: true })
      .locator(".metric-value"),
  ).toHaveText("207");
  await expect(
    page
      .getByRole("button", { name: "View contract documents", exact: true })
      .locator(".metric-value"),
  ).toHaveText("203");
  await expect(
    page.getByRole("button", {
      name: "Nov 26: 501 invoices, 207 expenses",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".evidence-count strong")).toHaveText("2/203");
  await expect(
    page.getByText(
      "Counts include all accessible workspace records, not just the loaded preview.",
      { exact: false },
    ),
  ).toBeVisible();
});
