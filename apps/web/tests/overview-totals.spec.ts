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
  await page.getByText("Record inventory & coverage", { exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Invoice records: 501", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Expense records: 207", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Contract documents: 203", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("2 reviewed of 203 optional documents"),
  ).toBeVisible();
});
