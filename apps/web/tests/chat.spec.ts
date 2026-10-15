import { test, expect } from "@playwright/test";

test("in-popup conversation, follow-up, citations, context reset and mobile layout", async ({
  page,
}) => {
  // UI contract test only: backend/provider correctness is covered separately.
  const sent: Record<string, unknown>[] = [];
  await page.route("**/api/workspaces/*/ai/status", (route) =>
    route.fulfill({ json: { configured: true, model: "test-model" } }),
  );
  await page.route("**/api/workspaces/*/chat", async (route) => {
    sent.push(route.request().postDataJSON());
    await route.fulfill({
      json: {
        reply:
          sent.length === 1
            ? "**Contribution** is 800.00 INR. This is not net profit."
            : "That is the amount remaining after recorded delivery costs.",
        insufficient_evidence: false,
        billing_period: "2026-09",
        profitability_status: "confirmed",
        notice: "Figures and quotations checked. Review the interpretation.",
        scope_label: "All accessible customers",
        cards: [
          { label: "Contribution", value: "800.00 INR", tone: "positive" },
        ],
        actions: [
          {
            view: "invoices",
            label: "Open invoice INV-01-9",
            customer_id: "EVAL-01",
            billing_period: "2026-09",
            record_id: "INV-01-9",
          },
          {
            view: "analysis",
            label: "Review customer",
            customer_id: "EVAL-01",
            billing_period: "2026-09",
          },
        ],
        sources: [
          {
            source_id: "sample",
            filename: "Current contract.pdf",
            page: 1,
            source_url:
              "/api/workspaces/evaluation-demo/contracts/example/file#page=1",
            quote: "Monthly service delivery agreement.",
            evidence_status: "outside_selected_period",
          },
        ],
        findings: [],
        record_ids: { invoices: ["I-01"], expenses: ["E-01"] },
      },
    });
  });
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page
    .getByLabel("Workspace", { exact: true })
    .selectOption("evaluation-demo");
  await expect(page.getByText("Loading workspace records…")).not.toBeVisible();
  await page
    .getByRole("button", { name: "ProfitLens chatbot", exact: true })
    .click();
  const popup = page.getByRole("region", { name: "ProfitLens assistant" });
  await expect(popup.getByLabel("Chat customer")).not.toBeVisible();
  const input = popup.getByLabel("Message ProfitLens");
  await input.fill("What is the contribution?");
  await input.press("Enter");
  await expect(popup.getByRole("article", { name: "AI reply" })).toContainText(
    "800.00 INR",
  );
  await popup.getByText("View supporting records").click();
  await expect(
    popup.getByRole("link", { name: "Current contract.pdf · page 1" }),
  ).toHaveAttribute("href", /\/contracts\/example\/file#page=1$/);
  await expect(popup).toContainText("Invoices: I-01");
  await expect(popup).toContainText(
    "Outside the selected month · reference only",
  );
  await input.fill("Explain that simply");
  await popup.getByRole("button", { name: "Send message" }).click();
  await expect(popup.getByRole("article", { name: "AI reply" })).toHaveCount(2);
  expect(sent[1].history).toHaveLength(2);
  expect(sent[1].automatic).toBe(true);
  expect(sent[1].customer_id).toBeNull();
  expect(sent[1].billing_period).toBeNull();
  await expect(popup.locator(".chat-formatted strong").first()).toHaveText(
    "Contribution",
  );
  await expect(popup.locator(".chat-tone-positive").first()).toContainText(
    "800.00 INR",
  );
  await expect(
    page.getByRole("heading", { name: "Business data, connected." }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/chat-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(popup).toBeVisible();
  const box = await popup.boundingBox();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(390);
  await expect(
    popup.getByRole("button", { name: "Send message" }),
  ).toBeInViewport();
  await page.screenshot({ path: "test-results/chat-mobile.png" });
  await popup
    .getByRole("button", { name: "Open invoice INV-01-9" })
    .first()
    .click();
  await expect(
    page.getByRole("dialog").getByLabel("Subtotal (before tax/discount)"),
  ).toHaveValue("1200.00");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close", exact: true })
    .click();
  await page
    .getByRole("button", { name: "ProfitLens chatbot", exact: true })
    .click();
  await popup.getByRole("button", { name: "Review customer" }).first().click();
  await expect(popup).not.toBeVisible();
  await expect(page.getByLabel("Analysis customer")).toHaveValue("EVAL-01");
  await expect(page.getByLabel("Analysis month")).toHaveValue("2026-09");
  await page
    .getByRole("button", { name: "ProfitLens chatbot", exact: true })
    .click();
  await popup.getByRole("button", { name: "Use manual filters" }).click();
  await popup.getByLabel("Chat customer").selectOption("EVAL-02");
  await expect(popup.getByRole("article")).toHaveCount(0);
  await input.fill("Hello");
  await input.press("Shift+Enter");
  await expect(input).toHaveValue("Hello\n");
  await input.press("Escape");
  await expect(popup).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "ProfitLens chatbot", exact: true }),
  ).toBeFocused();
});
