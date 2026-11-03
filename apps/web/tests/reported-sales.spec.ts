import { test, expect } from "@playwright/test";

test("source-first CSV mapping, signed amounts, monthly drill-down and original evidence", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("other@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your business, in focus." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Source data & insights", exact: true })
    .click();
  const name = `source-${Date.now()}.csv`;
  await page
    .getByLabel("Original CSV, TSV, XLSX, JSON or text PDF")
    .setInputFiles({
      name,
      mimeType: "text/csv",
      buffer: Buffer.from(
        `Date,Amount,Supplier,OriginalNote\n2026-01-15,100.00,Vendor-${name},keep me\n2026-02-10,-20.00,Vendor-${name},credit\n`,
      ),
    });
  await page
    .getByRole("button", { name: "Extract and retain original", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: `2. Review mapping: ${name}` }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Preview normalized records",
      exact: true,
    }),
  ).toBeDisabled();
  await page
    .getByLabel("Record meaning", { exact: true })
    .selectOption("expenditure");
  await page
    .getByRole("button", { name: "Preview normalized records", exact: true })
    .click();
  await expect(
    page.getByText("2 records · 0 issues", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Confirm reviewed mapping", exact: true })
    .click();
  await expect(
    page.getByText("Source import confirmed. Original data retained.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: /2026-02 · expenditure/ }).click();
  await expect(page.getByLabel("From date")).toHaveValue("2026-02-01");
  await expect(
    page.getByText("INR -20.00", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("row")
    .filter({ hasText: `Vendor-${name}` })
    .getByRole("button", { name: "Source row 2 ↗", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: `Evidence: ${name}` }),
  ).toBeVisible();
  await expect(
    page.getByText("Download unchanged original", { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("reported sales preview, confirmation, adaptive overview and source inspection", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("other@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your business, in focus." }),
  ).toBeVisible();
  const account = await (await page.request.get("/api/auth/me")).json();
  const org = account.workspaces[0].id;
  const origin = new URL(page.url()).origin;
  const id = `SALE${Date.now()}`;
  const customer = await page.request.post(
    `/api/workspaces/${org}/records/customers`,
    {
      headers: { Origin: origin },
      data: { customer_id: id, name: "Reported sales test" },
    },
  );
  expect(customer.status()).toBe(201);
  await page.getByRole("button", { name: "Imports", exact: true }).click();
  await page.getByLabel("Record type").selectOption("invoices");
  await page.getByLabel("CSV file").setInputFiles({
    name: "reported-sales.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      `invoice_id,customer_id,billing_period,currency,total,amount_basis,source_rows\n${id},${id},2026-09,INR,123.45,reported_sales,42;43\n`,
    ),
  });
  await page
    .getByRole("button", { name: "Preview import", exact: true })
    .click();
  await page.getByRole("button", { name: /Confirm.*import/i }).click();
  await expect(page.getByText(/Import confirmed/i)).toBeVisible();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Reported sales" }),
  ).toBeVisible();
  await expect(page.getByText(/costs and tax breakdown unknown/)).toBeVisible();
  await page
    .getByRole("button", { name: /Inspect reported sales records/ })
    .click();
  await page.getByRole("button", { name: id, exact: true }).click();
  await expect(page.getByText(/Reported sales amount. Tax/)).toBeVisible();
  await page
    .getByText("Original imported values and source references")
    .click();
  await expect(page.locator("pre")).toContainText("42;43");
  await expect(page.getByLabel("Tax", { exact: true })).toHaveCount(0);
});

test("bank TSV keeps money in and money out separate and opens readable evidence", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("other@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page
    .getByRole("button", { name: "Source data & insights", exact: true })
    .click();
  const name = `bank-${Date.now()}.tsv`;
  await page
    .getByLabel("Original CSV, TSV, XLSX, JSON or text PDF")
    .setInputFiles({
      name,
      mimeType: "text/tab-separated-values",
      buffer: Buffer.from(
        `Date\tCredit\tDebit\tDescription\tSourceNote\n2026-08-03\t125.50\t\tReceipt-${name}\tSynthetic bank fixture\n2026-08-04\t\t25.25\tPayment-${name}\tNot an expense classification\n`,
      ),
    });
  await page
    .getByRole("button", { name: "Extract and retain original", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: `2. Review mapping: ${name}` }),
  ).toBeVisible();
  await page
    .getByLabel("Record meaning", { exact: true })
    .selectOption("cash_inflow");
  await page.getByLabel("Amount derivation").selectOption("bank_columns");
  await expect(
    page.getByLabel("Money received (bank credit) source column"),
  ).toHaveValue("Credit");
  await expect(
    page.getByLabel("Money paid (bank debit) source column"),
  ).toHaveValue("Debit");
  await page
    .getByRole("button", { name: "Preview normalized records", exact: true })
    .click();
  await expect(
    page.getByText("2 records · 0 issues", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Confirm reviewed mapping", exact: true })
    .click();
  await expect(
    page.getByText("Source import confirmed. Original data retained.", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByLabel("Financial meaning", { exact: true })
    .selectOption("cash_outflow");
  const row = page.getByRole("row").filter({ hasText: `Payment-${name}` });
  await expect(row).toContainText("25.25");
  await row
    .getByRole("button", { name: "Source row 2 ↗", exact: true })
    .click();
  const dialog = page.getByRole("dialog", { name: `Evidence: ${name}` });
  await expect(
    dialog.getByRole("heading", { name: "How this figure was obtained" }),
  ).toBeVisible();
  await expect(dialog).toContainText("not proof of revenue or expense");
  await expect(dialog).toContainText("Not an expense classification");
  await expect(
    dialog.getByRole("link", { name: "Download unchanged original" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
});
