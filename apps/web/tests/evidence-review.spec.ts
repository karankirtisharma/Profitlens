import { test, expect } from "@playwright/test";

test("source chatbot citations open readable evidence and preserve aggregate scope", async ({
  page,
}) => {
  await page.route("**/api/workspaces/*/ai/status", (r) =>
    r.fulfill({ json: { configured: true, model: "ui-test" } }),
  );
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
  const me = await (await page.request.get("/api/auth/me")).json();
  const base = `/api/workspaces/${me.workspaces[0].id}`;
  const headers = { Origin: new URL(page.url()).origin };
  const uploaded = await page.request.post(`${base}/sources`, {
    headers,
    multipart: {
      file: {
        name: "citation.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(
          `Date,Amount,Memo\n2026-11-01,15.25,citation-${Date.now()}\n`,
        ),
      },
    },
  });
  expect(uploaded.ok()).toBeTruthy();
  const doc = await uploaded.json();
  const preview = await (
    await page.request.post(`${base}/sources/${doc.id}/preview`, {
      headers,
      data: {
        kind: "expenditure",
        currency: "INR",
        columns: { date: "Date", amount: "Amount", description: "Memo" },
      },
    })
  ).json();
  expect(preview.issues).toEqual([]);
  expect(
    (
      await page.request.post(`${base}/sources/${doc.id}/confirm`, {
        headers,
        data: { preview_token: preview.preview_token },
      })
    ).ok(),
  ).toBeTruthy();
  const facts = await (
    await page.request.get(
      `${base}/facts?kind=expenditure&start=2026-11-01&end=2026-11-30`,
    )
  ).json();
  const fact = facts.rows.find(
    (f: { document_id: string }) => f.document_id === doc.id,
  );
  // Only AI prose is mocked; evidence and authorization use the real local API.
  await page.route("**/api/workspaces/*/chat", (r) =>
    r.fulfill({
      json: {
        reply: "Inspect this recorded expenditure; profit is unavailable.",
        insufficient_evidence: true,
        billing_period: "2026-11",
        profitability_status: "source_observations_only",
        notice: "UI fixture",
        sources: [
          {
            source_id: "row",
            filename: "citation.csv",
            page: null,
            source_url: `${base}/facts/${fact.id}`,
            quote: "15.25 INR recorded",
            evidence_status: "source_observation",
          },
          {
            source_id: "group",
            filename: "November expenditure",
            page: null,
            source_url: `${base}/facts?kind=expenditure&start=2026-11-01&end=2026-11-30`,
            quote: "Authorized records",
            evidence_status: "source_observation",
          },
        ],
        findings: [],
        record_ids: { invoices: [], expenses: [] },
      },
    }),
  );
  await page
    .getByRole("button", { name: "ProfitLens chatbot", exact: true })
    .click();
  const popup = page.getByRole("region", { name: "ProfitLens assistant" });
  await popup.getByLabel("Message ProfitLens").fill("Explain the source");
  await popup.getByRole("button", { name: "Send message" }).click();
  await popup.getByText("View supporting records").click();
  await popup.getByRole("link", { name: "citation.csv", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Evidence: citation.csv" });
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByRole("heading", { name: "How this figure was obtained" }),
  ).toBeVisible();
  await expect(
    dialog.getByRole("link", { name: "Download unchanged original" }),
  ).toHaveAttribute("href", `${base}/sources/${doc.id}/file`);
  await page.screenshot({ path: "test-results/source-evidence-dialog.png" });
  await dialog.getByRole("button", { name: "Close", exact: true }).click();
  await popup.getByRole("link", { name: "November expenditure" }).click();
  await expect(popup).not.toBeVisible();
  await expect(page.getByLabel("From date")).toHaveValue("2026-11-01");
  await expect(page.getByLabel("To date")).toHaveValue("2026-11-30");
});

test("pricing is readable and clearly a proposal with no purchase flow", async ({
  page,
}) => {
  await page.goto("/pricing");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Explore", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Review", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Collaborate", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("note")).toContainText("Pricing preview only");
  await page.screenshot({
    path: "test-results/pricing-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/pricing-mobile.png",
    fullPage: true,
  });
});
