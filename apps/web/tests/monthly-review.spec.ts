import { test, expect } from "@playwright/test";

test("monthly review explains recorded changes and preserves exact evidence filters", async ({
  page,
}, testInfo) => {
  // Synthetic API fixture tests presentation and drill-down wiring, not backend arithmetic.
  let reviewRequests = 0;
  await page.route("**/api/workspaces/*/source-review?*", async (route) => {
    reviewRequests++;
    const url = new URL(route.request().url());
    const base = url.pathname.replace("/source-review", "/facts");
    const source = (start: string, end: string, counterparty?: string) => {
      const query = new URLSearchParams({
        start,
        end,
        kind: "expenditure",
        currency: "INR",
      });
      if (counterparty !== undefined) query.set("counterparty", counterparty);
      return `${base}?${query}`;
    };
    const empty = url.searchParams.get("period") === "2030-01";
    await route.fulfill({
      json: {
        period: empty ? "2030-01" : "2026-09",
        previous_period: empty ? "2029-12" : "2026-08",
        kind: "expenditure",
        currency: "INR",
        comparable: !empty,
        change: empty ? null : "119.00",
        current: {
          amount: empty ? null : "199.00",
          count: empty ? 0 : 3,
          source_url: source("2026-09-01", "2026-09-30"),
        },
        previous: {
          amount: empty ? null : "80.00",
          count: empty ? 0 : 1,
          source_url: source("2026-08-01", "2026-08-31"),
        },
        drivers: empty
          ? []
          : [
              {
                counterparty: "Acme & Co",
                label: "Acme & Co",
                status: "comparable",
                current: "120.00",
                previous: "80.00",
                change: "40.00",
                current_count: 2,
                previous_count: 1,
                current_source_url: source(
                  "2026-09-01",
                  "2026-09-30",
                  "Acme & Co",
                ),
                previous_source_url: source(
                  "2026-08-01",
                  "2026-08-31",
                  "Acme & Co",
                ),
              },
              {
                counterparty: "New supplier",
                label: "New supplier",
                status: "current_only",
                current: "79.00",
                previous: null,
                change: null,
                current_count: 1,
                previous_count: 0,
                current_source_url: source(
                  "2026-09-01",
                  "2026-09-30",
                  "New supplier",
                ),
                previous_source_url: source(
                  "2026-08-01",
                  "2026-08-31",
                  "New supplier",
                ),
              },
            ],
        driver_group_count: empty ? 0 : 2,
        missing_dates: 2,
        unknown_counterparty_records: 0,
        current_month_incomplete: empty,
        notice:
          "Recorded amounts only. Missing records are not zero, and this comparison is not net profit.",
        review_prompts: empty
          ? []
          : [
              "Check whether both months contain the complete spending export before deciding why the recorded amount changed.",
            ],
      },
    });
  });
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
  const review = page.getByRole("region", {
    name: "Monthly business review",
    exact: true,
  });
  await expect(review).toBeVisible();
  expect(reviewRequests).toBe(0);
  await review.getByLabel("Review month", { exact: true }).fill("2026-09");
  await review.getByRole("button", { name: "Run review", exact: true }).click();
  await expect(review.getByText("INR 119.00", { exact: true })).toBeVisible();
  await expect(
    review.getByText("No records — unavailable", { exact: true }),
  ).toBeVisible();
  await expect(
    review.getByRole("cell").filter({ hasText: "Not comparable" }),
  ).toBeVisible();
  await expect(review).toContainText("Missing records are not zero");
  await review.screenshot({ path: testInfo.outputPath("monthly-review.png") });
  const requested = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return (
      url.pathname.endsWith("/facts") &&
      url.searchParams.get("counterparty") === "Acme & Co"
    );
  });
  await review
    .getByRole("button", {
      name: "Inspect selected records for Acme & Co",
      exact: true,
    })
    .click();
  const sourceRequest = new URL((await requested).url());
  expect(sourceRequest.searchParams.get("start")).toBe("2026-09-01");
  expect(sourceRequest.searchParams.get("end")).toBe("2026-09-30");
  expect(sourceRequest.searchParams.get("currency")).toBe("INR");
  expect(sourceRequest.searchParams.get("kind")).toBe("expenditure");
  await expect(page.getByLabel("From date", { exact: true })).toHaveValue(
    "2026-09-01",
  );
  await expect(page.getByLabel("To date", { exact: true })).toHaveValue(
    "2026-09-30",
  );
  await review.getByLabel("Review month", { exact: true }).fill("2030-01");
  await expect(review.getByText("INR 119.00", { exact: true })).toHaveCount(0);
  await review.getByRole("button", { name: "Run review", exact: true }).click();
  await expect(
    review.getByText("Comparison unavailable", { exact: true }),
  ).toBeVisible();
  await expect(
    review.getByText("No records — unavailable", { exact: true }),
  ).toHaveCount(2);
  await expect(review).toContainText("future or partial period");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
