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
    page.getByRole("heading", { name: "Financial activity", exact: true }),
  ).toBeVisible();
}

test("intro plays on every visit and after sign-in, and can be skipped", async ({
  page,
}) => {
  await page.goto("/");
  const intro = page.getByRole("dialog", { name: "ProfitLens introduction" });
  await expect(intro).toBeVisible();
  await intro.getByRole("button", { name: "Skip intro" }).click();
  await ready(page);
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
  await expect(intro).toBeVisible();
  await page.keyboard.press("Escape");
  await ready(page);
  const sound = page.getByRole("button", { name: "Sound effects" });
  await expect(sound).toHaveAttribute("aria-pressed", "false");
  await sound.click();
  await expect(sound).toHaveAttribute("aria-pressed", "true");
  await credentials(page);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(intro).toBeVisible();
  await intro.getByRole("button", { name: "Skip intro" }).click();
  await ready(page);
  await expect(
    page.getByRole("heading", { name: "Financial activity", exact: true }),
  ).toBeVisible();
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
    page.getByRole("button", { name: "Sound effects" }),
  ).toBeVisible();
  await credentials(page);
  await page.getByLabel("Password", { exact: true }).press("Enter");
  await expect(
    page.getByRole("heading", { name: "Financial activity", exact: true }),
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
  const response = await page.request.get("/api/workspaces/demo-org/dashboard");
  const summary = await response.json();
  await page.getByText("Record inventory & coverage", { exact: true }).click();
  await expect(
    page.getByRole("button", {
      name: `Invoice records: ${summary.counts.invoices}`,
      exact: true,
    }),
  ).toBeVisible();
  await page.getByLabel("Chart range", { exact: true }).selectOption("12");
  await expect(page.getByLabel("Chart range", { exact: true })).toHaveValue(
    "12",
  );
  await expect(
    page.getByText(
      "Actual recorded periods. Missing months are not filled with zero.",
    ),
  ).toBeVisible();
  await page
    .getByRole("button", {
      name: `Invoice records: ${summary.counts.invoices}`,
      exact: true,
    })
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
    page.getByRole("heading", { name: "Financial activity", exact: true }),
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
    page.getByRole("region", { name: "Financial trends" }),
  ).toHaveCount(0);
  await page.unroute("**/api/workspaces/demo-org/records/invoices?limit=200");
  await page.getByRole("button", { name: "Refresh data" }).click();
  await expect(
    page.getByRole("heading", { name: "Financial activity", exact: true }),
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
    page.getByRole("heading", { name: "Financial activity", exact: true }),
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
