import { test, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function openFinance(page: Page, account = "karan") {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill(`${account}@profitlens.local`);
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Business data, connected.",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page
    .getByRole("button", { name: "Revenue & costs", exact: true })
    .click();
  await expect(page.getByLabel("Billing month", { exact: true })).toBeVisible();
}

test("revenue/cost report explains exact inputs, missing data and source navigation", async ({
  page,
}) => {
  await openFinance(page);
  await page.getByLabel("Customer", { exact: true }).selectOption("W4-EXACT");
  const card = page.locator(".finance-customer");
  await expect(
    card.getByRole("heading", { name: "Exact amounts (synthetic)" }),
  ).toBeVisible();
  await expect(card.locator("dd")).toHaveText(["INR 850.00", "INR 200.30"]);
  await page
    .getByText("Calculation and sources for W4-EXACT", { exact: true })
    .click();
  await expect(card.getByText("INR 90.00", { exact: true })).toBeVisible();
  await expect(
    card.getByText("synthetic-week4-invoices.csv · row 2", { exact: true }),
  ).toBeVisible();
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.getByRole("button", { name: "W4-I-EXACT", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Invoices", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("dialog").getByLabel("Subtotal (before tax/discount)"),
  ).toHaveValue("1000.50");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Revenue & costs", exact: true })
    .click();
  await page.getByLabel("Customer", { exact: true }).selectOption("W4-MISSING");
  await expect(card.locator("dd")).toHaveText(["INR 500.00", "Unavailable"]);
  await expect(card.getByText("missing costs", { exact: true })).toBeVisible();
  await page.getByLabel("Customer", { exact: true }).selectOption("W4-ZERO");
  await expect(card.locator("dd")).toHaveText(["INR 0.00", "INR 0.00"]);
  await expect(card.getByText("zero revenue", { exact: true })).toBeVisible();
  await page.getByLabel("Billing month", { exact: true }).fill("2026-08");
  await expect(card.locator("dd")).toHaveText(["Unavailable", "Unavailable"]);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Billing month", { exact: true }).fill("2026-09");
  await page.getByLabel("Customer", { exact: true }).selectOption("W4-EXACT");
  await expect(card.locator("dd")).toHaveText(["INR 850.00", "INR 200.30"]);
  await page
    .getByText("Calculation and sources for W4-EXACT", { exact: true })
    .click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "test-results/finance-mobile.png",
    fullPage: true,
  });
});

test("analyst financial report is limited to assigned customers", async ({
  page,
}) => {
  await openFinance(page, "analyst");
  await expect(page.locator(".finance-customer")).toHaveCount(1);
  await expect(page.locator(".finance-customer")).toContainText("C001");
  await expect(
    page.getByLabel("Customer", { exact: true }).locator("option"),
  ).toHaveCount(2);
  const response = await page.request.get(
    "/api/workspaces/demo-org/finance?customer_id=W4-EXACT",
  );
  expect(response.status()).toBe(404);
});
