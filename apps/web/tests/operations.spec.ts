import { expect, test, type Page } from "@playwright/test";

test("document and report hubs keep evidence workflows easy to find", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Workspace sections" });
  await nav.getByLabel("Find a section").fill("documents");
  await nav.getByRole("button", { name: "Documents", exact: true }).click();
  const library = page.getByRole("region", { name: "Document library" });
  await expect(library).toBeVisible();
  await expect(library.getByText("Loading documents…")).not.toBeVisible();
  await expect(library.getByRole("alert")).toHaveCount(0);
  await library
    .getByLabel("Find a document")
    .fill("not-a-real-file-unique-lookup");
  await expect(
    library.getByText("No documents match.", { exact: false }),
  ).toBeVisible();
  await library.getByLabel("Find a document").clear();
  await library
    .getByLabel("Document type", { exact: true })
    .selectOption("Contract");
  await expect(
    library.getByRole("link", { name: /^Download / }).first(),
  ).toBeVisible();
  const href = await library
    .getByRole("link", { name: /^Download / })
    .first()
    .getAttribute("href");
  const download = await page.request.get(href!);
  expect(download.status()).toBe(200);
  expect(download.headers()["content-type"]).toContain("application/pdf");
  await nav.getByRole("button", { name: "Reports", exact: true }).click();
  const reports = page.getByRole("region", { name: "Report library" });
  await expect(reports).toBeVisible();
  await reports.getByRole("button", { name: /Receivables & payables/ }).click();
  await expect(page.locator(".ops-panel")).toBeVisible();
  await nav.getByRole("button", { name: "Reports", exact: true }).click();
  await reports
    .getByRole("button", { name: /Monthly business review/ })
    .click();
  await expect(
    page.getByRole("region", { name: "Monthly business review", exact: true }),
  ).toBeVisible();
});

async function navigate(page: Page, label: string) {
  const nav = page.getByRole("navigation", { name: "Workspace sections" });
  await nav.getByRole("button", { name: label, exact: true }).click();
  await expect(page.locator(".ops-panel")).toBeVisible();
  await expect(
    page.locator(".ops-panel").getByText("Loading workspace records…"),
  ).not.toBeVisible();
}

test("operational records connect vendor bills, partial payments and reviewed receivables", async ({
  page,
}, testInfo) => {
  test.setTimeout(90_000);
  const stamp = Date.now().toString();
  const vendor = `UI-V-${stamp}`;
  const bill1 = `UI-B1-${stamp}`;
  const bill2 = `UI-B2-${stamp}`;
  const payment = `UI-P-${stamp}`;
  const invoice = `UI-I-${stamp}`;
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Vendors", exact: true }),
  ).toBeVisible();
  await navigate(page, "Vendors");
  await page.getByRole("button", { name: "New vendor", exact: true }).click();
  let dialog = page.getByRole("dialog");
  await dialog.getByLabel("Vendor ID", { exact: true }).fill(vendor);
  await dialog
    .getByLabel("Vendor name", { exact: true })
    .fill(`Synthetic UI supplier ${stamp}`);
  await dialog.getByLabel("Email (optional)").fill("test@example.invalid");
  await dialog
    .getByRole("button", { name: "Save record", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: vendor, exact: true }),
  ).toBeVisible();
  await navigate(page, "Items");
  await page.getByRole("button", { name: "New item", exact: true }).click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Item ID", { exact: true }).fill(`UI-ITEM-${stamp}`);
  await dialog
    .getByLabel("Item or service name")
    .fill("Synthetic review service");
  await dialog.getByLabel("Unit price", { exact: true }).fill("250.50");
  await dialog
    .getByRole("button", { name: "Save record", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  const itemRow = page.getByRole("row").filter({
    has: page.getByRole("button", { name: `UI-ITEM-${stamp}`, exact: true }),
  });
  await expect(itemRow).toContainText("INR 250.50");
  await itemRow.getByRole("button", { name: "Edit", exact: true }).click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Unit price", { exact: true }).fill("275.50");
  await dialog
    .getByRole("button", { name: "Save record", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(itemRow).toContainText("INR 275.50");
  await navigate(page, "Bills");
  for (const [id, total] of [
    [bill1, "100.00"],
    [bill2, "50.00"],
  ]) {
    await page.getByRole("button", { name: "New bill", exact: true }).click();
    dialog = page.getByRole("dialog");
    await dialog.getByLabel("Bill ID", { exact: true }).fill(id);
    await dialog.getByLabel("Vendor", { exact: true }).selectOption(vendor);
    await dialog.getByLabel("Issue date", { exact: true }).fill("2026-01-01");
    await dialog.getByLabel("Due date (optional)").fill("2026-01-31");
    await dialog.getByLabel("Total payable", { exact: true }).fill(total);
    await dialog.getByLabel("Already paid before tracking").fill("0.00");
    await dialog.getByRole("checkbox").check();
    await dialog
      .getByRole("button", { name: "Save record", exact: true })
      .click();
    await expect(dialog).not.toBeVisible();
    await expect(
      page.getByRole("button", { name: id, exact: true }),
    ).toBeVisible();
  }
  await navigate(page, "Payments");
  await page
    .getByRole("button", { name: "Record payment", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Payment ID", { exact: true }).fill(payment);
  await dialog.getByLabel("Payment direction").selectOption("made");
  await dialog.getByLabel("Payment date", { exact: true }).fill("2026-02-01");
  await dialog.getByLabel("Bill 1", { exact: true }).selectOption(bill1);
  await dialog.getByLabel("Allocated amount 1").fill("30.00");
  await dialog.getByRole("button", { name: "Add allocation" }).click();
  await dialog.getByLabel("Bill 2", { exact: true }).selectOption(bill2);
  await dialog.getByLabel("Allocated amount 2").fill("20.00");
  await dialog
    .getByRole("button", { name: "Save record", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(
    page.getByRole("row").filter({
      has: page.getByRole("button", { name: payment, exact: true }),
    }),
  ).toContainText("INR 50.00");
  await navigate(page, "Receivables & payables");
  const payables = page.getByRole("region", { name: "Vendor payables" });
  await expect(
    payables
      .getByRole("row")
      .filter({ has: page.getByRole("button", { name: bill1, exact: true }) }),
  ).toContainText("INR 70.00");
  await expect(
    payables
      .getByRole("row")
      .filter({ has: page.getByRole("button", { name: bill2, exact: true }) }),
  ).toContainText("INR 30.00");
  await page.screenshot({
    path: testInfo.outputPath("operations-balances.png"),
    fullPage: true,
  });

  // Seed one explicitly synthetic verified invoice through the authenticated API;
  // the opening-balance review and subsequent settlement run through the UI.
  const origin = new URL(page.url()).origin;
  const workspaceId = await page
    .getByLabel("Workspace", { exact: true })
    .inputValue();
  const base = `/api/workspaces/${encodeURIComponent(workspaceId)}`;
  const customers = await (
    await page.request.get(`${base}/records/customers`)
  ).json();
  const response = await page.request.post(`${base}/records/invoices`, {
    headers: { Origin: origin },
    data: {
      invoice_id: invoice,
      customer_id: customers[0].customer_id,
      billing_period: "2026-01",
      currency: "INR",
      subtotal: "125.00",
      discount: "0",
      tax: "0",
      refund: "0",
      total: "125.00",
    },
  });
  expect(response.ok()).toBeTruthy();
  await page
    .locator(".ops-panel")
    .getByRole("button", { name: "Refresh", exact: true })
    .click();
  await expect(
    page.locator(".ops-panel").getByText("Loading workspace records…"),
  ).not.toBeVisible();
  await page
    .getByRole("button", { name: "Review invoice balance", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Invoice", { exact: true }).selectOption(invoice);
  await dialog.getByLabel("Already paid before tracking").fill("25.00");
  await dialog.getByRole("checkbox").check();
  await dialog
    .getByRole("button", { name: "Confirm reviewed balance", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  const receivables = page.getByRole("region", {
    name: "Customer receivables",
  });
  await expect(
    receivables.getByRole("row").filter({
      has: page.getByRole("button", { name: invoice, exact: true }),
    }),
  ).toContainText("INR 100.00");
  await navigate(page, "Payments");
  await page
    .getByRole("button", { name: "Record payment", exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog.getByLabel("Payment ID", { exact: true }).fill(`UI-R-${stamp}`);
  await dialog.getByLabel("Invoice 1", { exact: true }).selectOption(invoice);
  await dialog.getByLabel("Allocated amount 1").fill("40.00");
  await dialog
    .getByRole("button", { name: "Save record", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await navigate(page, "Receivables & payables");
  await expect(
    page
      .getByRole("region", { name: "Customer receivables" })
      .getByRole("row")
      .filter({
        has: page.getByRole("button", { name: invoice, exact: true }),
      }),
  ).toContainText("INR 60.00");
  await navigate(page, "Payments");
  await page
    .getByRole("button", { name: `UI-R-${stamp}`, exact: true })
    .click();
  dialog = page.getByRole("dialog");
  await dialog
    .getByRole("button", { name: "Void recorded payment", exact: true })
    .click();
  await expect(dialog).toContainText(
    "It does not cancel a bank transfer or issue a refund.",
  );
  await dialog
    .getByLabel("Reason for voiding")
    .fill("Synthetic browser test: incorrect recorded receipt.");
  await dialog.getByRole("checkbox").check();
  await dialog
    .getByRole("button", { name: "Confirm void", exact: true })
    .click();
  await expect(dialog).not.toBeVisible();
  await expect(
    page.getByRole("row").filter({
      has: page.getByRole("button", { name: `UI-R-${stamp}`, exact: true }),
    }),
  ).toContainText("void");
  await navigate(page, "Receivables & payables");
  await expect(
    page
      .getByRole("region", { name: "Customer receivables" })
      .getByRole("row")
      .filter({
        has: page.getByRole("button", { name: invoice, exact: true }),
      }),
  ).toContainText("INR 100.00");
});
