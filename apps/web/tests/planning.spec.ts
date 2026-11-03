import { test, expect } from "@playwright/test";

test("recurring review and purchase order conversion work with existing ledgers", async ({
  page,
}, testInfo) => {
  test.setTimeout(120000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Workspace sections" }),
    stamp = Date.now().toString();
  await expect(
    page.getByRole("heading", { name: "Financial activity", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("focus-dashboard.png"),
    fullPage: true,
  });
  await nav
    .getByRole("button", { name: "Recurring invoices", exact: true })
    .click();
  await page.getByRole("button", { name: "New schedule", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Reference", { exact: true }).fill("R" + stamp);
  await dialog
    .getByLabel("Schedule name", { exact: true })
    .fill("Synthetic UI retainer " + stamp);
  await dialog.getByLabel("Customer", { exact: true }).selectOption("C001");
  await dialog.getByLabel("Start date", { exact: true }).fill("2026-10-01");
  await dialog
    .getByLabel("End date (optional)", { exact: true })
    .fill("2026-10-01");
  await dialog.getByLabel("subtotal", { exact: true }).fill("100");
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await page
    .getByRole("button", { name: "Generate due drafts", exact: true })
    .click();
  const row = page
    .getByRole("row")
    .filter({ hasText: "Synthetic UI retainer " + stamp })
    .filter({
      has: page.getByRole("button", { name: "Review draft", exact: true }),
    });
  await row.getByRole("button", { name: "Review draft", exact: true }).click();
  await dialog
    .getByRole("button", { name: "Confirm & issue invoice", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(
    page
      .getByRole("row")
      .filter({ hasText: "Synthetic UI retainer " + stamp })
      .filter({
        has: page.getByRole("button", { name: "View invoices", exact: true }),
      }),
  ).toContainText("issued");
  const origin = new URL(page.url()).origin;
  const vendor = await page.request.post(
    "/api/workspaces/demo-org/operations/vendors",
    {
      headers: { Origin: origin },
      data: { vendor_id: "V" + stamp, name: "Synthetic PO supplier" },
    },
  );
  expect(vendor.ok()).toBe(true);
  await nav
    .getByRole("button", { name: "Purchase orders", exact: true })
    .click();
  await page
    .getByRole("button", { name: "New purchase order", exact: true })
    .click();
  await dialog.getByLabel("Reference", { exact: true }).fill("PO" + stamp);
  await dialog.getByLabel("Vendor", { exact: true }).selectOption("V" + stamp);
  await dialog.getByLabel("Order date", { exact: true }).fill("2026-10-01");
  await dialog
    .getByLabel("description 1", { exact: true })
    .fill("Support service");
  await dialog.getByLabel("unit_price 1", { exact: true }).fill("250");
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  const po = page.getByRole("row").filter({ hasText: "PO" + stamp });
  await po.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(po).toContainText("approved");
  await po
    .getByRole("button", { name: "Record matching bill", exact: true })
    .click();
  await dialog
    .getByLabel("Supplier bill reference", { exact: true })
    .fill("B" + stamp);
  await dialog.getByLabel("Bill date", { exact: true }).fill("2026-10-05");
  await dialog.getByLabel("Already paid", { exact: true }).fill("50");
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(po).toContainText("billed");
  await nav
    .getByRole("button", { name: "Receivables & payables", exact: true })
    .click();
  await expect(
    page.getByRole("row").filter({ hasText: "B" + stamp }),
  ).toContainText("200.00");
  await page.setViewportSize({ width: 390, height: 844 });
  await nav.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Financial activity", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("focus-mobile.png"),
    fullPage: true,
  });
});
