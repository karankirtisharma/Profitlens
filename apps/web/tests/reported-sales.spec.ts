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
    page.getByRole("heading", { name: "Business data, connected." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Source data & insights", exact: true })
    .click();
  const name = `source-${Date.now()}.csv`;
  await page.getByLabel("Original CSV, XLSX, JSON or text PDF").setInputFiles({
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
    page.getByRole("heading", { name: `Review mapping: ${name}` }),
  ).toBeVisible();
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
    page.getByRole("heading", { name: "Business data, connected." }),
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
    page.getByRole("heading", { name: "Reported sales by month" }),
  ).toBeVisible();
  await expect(
    page.getByText(
      "Contracts not provided. Optional for sales reporting; pricing compliance unavailable.",
    ),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /Inspect sales invoice sources/ })
    .click();
  await page.getByRole("button", { name: id, exact: true }).click();
  await expect(page.getByText(/Reported sales amount. Tax/)).toBeVisible();
  await page
    .getByText("Original imported values and source references")
    .click();
  await expect(page.locator("pre")).toContainText("42;43");
  await expect(page.getByLabel("Tax", { exact: true })).toHaveCount(0);
});
