import { test, expect, Page } from "@playwright/test";
import path from "node:path";
const stamp = Date.now().toString();
async function login(page: Page, account = "karan") {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill(`${account}@profitlens.local`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Business data, connected." }),
  ).toBeVisible();
  await expect(page.getByText("Loading workspace records…")).not.toBeVisible();
}
test("authenticated workspace and manual business-record editing", async ({
  page,
}) => {
  await login(page);
  await expect(page.locator(".chart-bar").first()).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, 0, 0)",
  );
  await page.screenshot({
    path: "test-results/workspace-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Customers", exact: true }).click();
  await page.getByRole("button", { name: "Add customer", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Customer ID", { exact: true }).fill(`WEB-${stamp}`);
  await dialog
    .getByLabel("Customer name")
    .fill(`Browser test customer ${stamp}`);
  await dialog.getByLabel("Industry").fill("Synthetic services");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("button", {
      name: `Browser test customer ${stamp}`,
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Invoices", exact: true }).click();
  await page.getByRole("button", { name: "Add invoice", exact: true }).click();
  await dialog
    .getByLabel("Invoice ID", { exact: true })
    .fill(`WEB-INV-${stamp}`);
  await dialog
    .getByRole("combobox", { name: "Customer ID", exact: true })
    .selectOption(`WEB-${stamp}`);
  await dialog.getByLabel("Billing month").fill("2026-09");
  await dialog.getByLabel("Subtotal (before tax/discount)").fill("1500.50");
  await dialog.getByLabel("Invoice total").fill("1500.50");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(
    page.getByRole("button", { name: `WEB-INV-${stamp}`, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: `WEB-INV-${stamp}`, exact: true })
    .click();
  await dialog.getByLabel("Discount", { exact: true }).fill("100");
  await dialog.getByLabel("Invoice total").fill("1400.50");
  await dialog.getByRole("button", { name: "Save record" }).click();
  await expect(
    page
      .getByRole("row")
      .filter({
        has: page.getByRole("button", {
          name: `WEB-INV-${stamp}`,
          exact: true,
        }),
      })
      .getByText("INR 1,400.50", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Sign in to your workspace" }),
  ).toBeVisible();
});

test("CSV errors, preview, persistent confirmation and retry", async ({
  page,
}) => {
  await login(page);
  await page.getByRole("button", { name: "Imports", exact: true }).click();
  await page.getByLabel("Record type").selectOption("invoices");
  await page
    .getByLabel("CSV file")
    .setInputFiles(path.resolve("../../data/demo/invalid_invoices.csv"));
  await page
    .getByRole("button", { name: "Preview import", exact: true })
    .click();
  await expect(page.getByText(/total must equal/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm import", exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Record type").selectOption("expenses");
  const content = `expense_id,customer_id,billing_period,category,amount,currency\nWEB-EXP-${stamp},C001,2026-09,Hosting,125.50,INR\n`;
  await page.getByLabel("CSV file").setInputFiles({
    name: "browser-expenses.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(content),
  });
  await page
    .getByRole("button", { name: "Preview import", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirm import", exact: true })
    .click();
  await expect(page.getByText(/Import confirmed: 1 inserted/)).toBeVisible();
  await page.getByLabel("CSV file").setInputFiles({
    name: "browser-expenses.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(content),
  });
  await page
    .getByRole("button", { name: "Preview import", exact: true })
    .click();
  await expect(
    page.getByText(/Repeating this import will not duplicate/),
  ).toBeVisible();
  await page.getByRole("button", { name: "Expenses", exact: true }).click();
  await page
    .getByRole("button", { name: `WEB-EXP-${stamp}`, exact: true })
    .click();
  await expect(
    page.getByText("browser-expenses.csv · Row 2", { exact: true }),
  ).toBeVisible();
});

test("private PDF upload, source evidence and reviewed monthly terms", async ({
  page,
}) => {
  await login(page);
  await page.getByRole("button", { name: "Contracts", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Customer", exact: true })
    .selectOption("C001");
  await page
    .getByLabel("Contract PDF")
    .setInputFiles(path.resolve("../../data/demo/contract_C001.pdf"));
  await page
    .getByRole("button", { name: "Upload contract", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Page 1", { exact: true })).toBeVisible();
  await dialog.getByLabel("Effective from").fill("2026-09-01");
  await dialog.getByLabel("Effective to").fill("2027-02-28");
  await dialog.getByLabel("Monthly rate").fill("10000");
  await dialog.getByLabel("Monthly discount").fill("0");
  await dialog.getByRole("button", { name: "Confirm reviewed terms" }).click();
  await expect(dialog.getByText("reviewed", { exact: true })).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await dialog.getByRole("link", { name: "Download PDF" }).click();
  expect((await downloaded).suggestedFilename()).toBe("contract_C001.pdf");
  await page.screenshot({
    path: "test-results/contract-review.png",
    fullPage: true,
  });
});

test("analyst sees assigned customers and cannot access restricted data", async ({
  page,
}) => {
  await login(page, "analyst");
  await expect(
    page.getByRole("button", { name: "Imports", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Team access", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Customers", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Northstar Studio", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Harbor Retail", exact: true }),
  ).toHaveCount(0);
  const response = await page.request.get(
    "/api/workspaces/demo-org/records/customers/C002",
  );
  expect(response.status()).toBe(404);
  const other = await page.request.get(
    "/api/workspaces/other-org/records/customers",
  );
  expect(other.status()).toBe(404);
  await page
    .getByRole("button", { name: "Northstar Studio", exact: true })
    .click();
  await expect(
    page.getByRole("dialog").getByRole("button", { name: "Save record" }),
  ).toHaveCount(0);
});

test("mobile workspace has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await expect(
    page.getByRole("button", { name: "Import business data" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await expect(page.locator(".chart-bar").first()).toHaveCSS(
    "transform",
    "matrix(1, 0, 0, 1, 0, 0)",
  );
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "test-results/workspace-mobile.png",
    fullPage: true,
  });
});
