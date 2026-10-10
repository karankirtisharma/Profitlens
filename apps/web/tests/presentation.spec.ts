import { test, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function ready(page: Page) {
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
}
async function credentials(page: Page) {
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
}
async function login(page: Page) {
  await page.goto("/");
  await ready(page);
  await credentials(page);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Records by billing month" }),
  ).toBeVisible();
}

test("intro can be skipped and replayed, appears only once per session, and restores focus", async ({
  page,
}) => {
  await page.goto("/");
  const intro = page.getByRole("dialog", { name: "ProfitLens introduction" });
  await expect(intro).toBeVisible();
  await intro.getByRole("button", { name: "Skip intro" }).click();
  await ready(page);
  await page.screenshot({
    path: "test-results/login-desktop.png",
    fullPage: true,
  });
  await page.getByLabel("Password", { exact: true }).fill("preview-password");
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute(
    "type",
    "text",
  );
  await page.getByRole("button", { name: "Hide password" }).click();
  await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute(
    "type",
    "password",
  );
  await page.reload();
  await ready(page);
  await expect(intro).toHaveCount(0);
  const replay = page.getByRole("button", { name: "Replay logo intro" });
  await replay.click();
  await expect(intro).toBeVisible();
  await page.keyboard.press("Escape");
  await ready(page);
  await expect(replay).toBeFocused();
});

test("reduced-motion and keyboard users can sign in, navigate and close a focused dialog", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await ready(page);
  await expect(
    page.getByRole("dialog", { name: "ProfitLens introduction" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Replay logo intro" }),
  ).toHaveCount(0);
  await credentials(page);
  await page.getByLabel("Password", { exact: true }).press("Enter");
  await expect(
    page.getByRole("heading", { name: "Records by billing month" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Customers", exact: true }).focus();
  await page.keyboard.press("Enter");
  const add = page.getByRole("button", { name: "Add customer", exact: true });
  await add.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", {
    name: "Add customer",
    exact: true,
  });
  await expect(dialog).toBeVisible();
  await expect(dialog).toHaveCSS("opacity", "1");
  await expect(
    dialog.getByRole("button", { name: "Close", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(add).toBeFocused();
});

test("overview counts and chart values match the scoped API, with working chart range and navigation", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page);
  await expect(
    page.getByText("Synthetic demo data", { exact: true }),
  ).toBeVisible();
  const [customers, invoices, expenses, contracts] = await Promise.all(
    [
      "records/customers",
      "records/invoices?limit=200",
      "records/expenses?limit=200",
      "contracts",
    ].map(async (endpoint) => {
      const response = await page.request.get(
        `/api/workspaces/demo-org/${endpoint}`,
      );
      expect(response.ok()).toBe(true);
      return response.json();
    }),
  );
  for (const [label, value] of [
    ["View customers", customers.length],
    ["View invoice records", invoices.length],
    ["View expense records", expenses.length],
    ["View contract documents", contracts.length],
  ] as const) {
    await expect(
      page
        .getByRole("button", { name: label, exact: true })
        .locator(".metric-value"),
    ).toHaveText(String(value));
  }
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await expect(
    page
      .getByRole("button", { name: "View invoice records", exact: true })
      .locator(".metric-value"),
  ).toHaveText(String(invoices.length));
  const lastMonth = [...invoices, ...expenses]
    .map((record) => record.billing_period as string)
    .sort()
    .at(-1)!;
  const invoiceCount = invoices.filter(
    (record: { billing_period: string }) => record.billing_period === lastMonth,
  ).length;
  const expenseCount = expenses.filter(
    (record: { billing_period: string }) => record.billing_period === lastMonth,
  ).length;
  const label = new Intl.DateTimeFormat("en", {
    month: "short",
    year: "2-digit",
    timeZone: "UTC",
  }).format(new Date(`${lastMonth}-01T00:00:00Z`));
  const monthButton = page.getByRole("button", {
    name: `${label}: ${invoiceCount} invoices, ${expenseCount} expenses`,
    exact: true,
  });
  await monthButton.click();
  await expect(monthButton).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("Chart month range").selectOption("12");
  await expect(page.getByLabel("Chart month range")).toHaveValue("12");
  await expect(
    page.getByText(/Record counts, not financial performance/),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "View invoice records", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Add invoice", exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("login, overview and record dialog pass automated WCAG checks", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await ready(page);
  const audit = async () => {
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(result.violations).toEqual([]);
  };
  await audit();
  await credentials(page);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Records by billing month" }),
  ).toBeVisible();
  await audit();
  await page.getByRole("button", { name: "Invoices", exact: true }).click();
  await page.getByRole("button", { name: "Add invoice", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await audit();
});

test("load failures hide overview totals, show a useful error and recover with Refresh", async ({
  page,
}) => {
  await login(page);
  await page.route(
    "**/api/workspaces/demo-org/records/invoices?limit=200",
    (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Records are temporarily unavailable. Try refreshing.",
        }),
      }),
  );
  await page.getByRole("button", { name: "Refresh data" }).click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Records are temporarily unavailable" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "View invoice records" }),
  ).toHaveCount(0);
  await page.unroute("**/api/workspaces/demo-org/records/invoices?limit=200");
  await page.getByRole("button", { name: "Refresh data" }).click();
  await expect(
    page.getByRole("heading", { name: "Records by billing month" }),
  ).toBeVisible();
});

test("login and records remain usable on a narrow screen", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto("/");
  await ready(page);
  await page.screenshot({
    path: "test-results/login-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await credentials(page);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Records by billing month" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Invoices", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Add invoice", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/records-mobile.png",
    fullPage: true,
  });
});
