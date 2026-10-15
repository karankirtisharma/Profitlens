import { test, expect } from "@playwright/test";

test("profitability, reviewed evidence and honest offline AI status", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Business data, connected." }),
  ).toBeVisible();
  await page
    .getByLabel("Workspace", { exact: true })
    .selectOption("evaluation-demo");
  await expect(page.getByText("Loading workspace records…")).not.toBeVisible();
  const bot = page.getByRole("button", {
    name: "ProfitLens chatbot",
    exact: true,
  });
  await bot.click();
  const popup = page.getByRole("region", { name: "ProfitLens assistant" });
  await expect(popup).toContainText("AI setup required");
  await page.keyboard.press("Escape");
  await expect(popup).not.toBeVisible();
  await expect(bot).toBeFocused();
  await bot.click();
  await popup.getByLabel("Message ProfitLens").fill("Hello");
  await popup.getByRole("button", { name: "Send message" }).click();
  await expect(popup.getByRole("alert")).toContainText("AI is not configured");
  await expect(popup.getByLabel("Message ProfitLens")).toHaveValue("Hello");
  await popup.getByRole("button", { name: "Close chat" }).click();
  await expect(popup).not.toBeVisible();
  await page.getByRole("button", { name: "Profitability & evidence" }).click();
  await page.getByLabel("Analysis customer").selectOption("EVAL-01");
  await page.getByLabel("Analysis month").fill("2026-09");
  await page
    .getByRole("button", { name: "Load analysis", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Profitability results" }),
  ).toContainText("800.00 INR");
  await expect(
    page.getByRole("heading", { name: "pricing mismatch", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Business question")
    .fill("What does the payroll monthly delivery agreement cover?");
  await page.getByRole("button", { name: "Find contract evidence" }).click();
  await expect(
    page.getByRole("link", { name: "EVAL-01-current.pdf · page 1" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Generate with configured AI" })
    .click();
  await expect(
    page.getByRole("heading", { name: "provider unavailable", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Load history" }).click();
  await expect(page.getByText("Recent investigations loaded.")).toBeVisible();
  // A finance-only question reaches the provider without demanding a contract.
  await page.getByLabel("Investigation evidence").selectOption("financial");
  await page.getByLabel("Analysis customer").selectOption("EVAL-11");
  await page
    .getByRole("button", { name: "Load analysis", exact: true })
    .click();
  await page
    .getByLabel("Business question")
    .fill("What is the recorded revenue?");
  await page
    .getByRole("button", { name: "Generate with configured AI" })
    .click();
  await expect(
    page.getByRole("heading", { name: "provider unavailable", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Cost coverage is not confirmed/)).toBeVisible();
  await page.screenshot({
    path: "test-results/analysis-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect
    .poll(() =>
      page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth + 1,
      ),
    )
    .toBe(true);
  await page.screenshot({
    path: "test-results/analysis-mobile.png",
    fullPage: true,
  });
  await page.getByLabel("Investigation evidence").scrollIntoViewIfNeeded();
  await expect(page.getByLabel("Investigation evidence")).toBeInViewport();
  await page.screenshot({ path: "test-results/analysis-mobile-evidence.png" });
  await page
    .getByRole("region", { name: "Profitability results" })
    .scrollIntoViewIfNeeded();
  await expect(
    page.getByRole("region", { name: "Profitability results" }),
  ).toContainText("1000.00 INR");
  await page.screenshot({ path: "test-results/analysis-mobile-financial.png" });
});
