import { expect, test } from "@playwright/test";

test("section search navigates by business terms and remains usable on mobile", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator('[data-intro-ready="true"]')).toBeVisible();
  await page.getByLabel("Email address").fill("karan@profitlens.local");
  await page
    .getByLabel("Password", { exact: true })
    .fill("browser-test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const nav = page.getByRole("navigation", { name: "Workspace sections" });
  await expect(nav).toBeVisible();
  const search = nav.getByRole("searchbox", { name: "Find a section" });
  await search.fill("billing");
  await expect(
    nav.getByRole("button", { name: "Invoices", exact: true }),
  ).toBeVisible();
  await expect(
    nav.getByRole("button", { name: "Customers", exact: true }),
  ).toHaveCount(0);
  await search.press("Enter");
  await expect(
    nav.getByRole("button", { name: "Invoices", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  await expect(search).toHaveValue("");
  await search.fill("unmatchedsectionxyz");
  await expect(nav.getByRole("status")).toContainText("No matching sections");
  await search.press("Escape");
  await expect(
    nav.getByRole("button", { name: "Customers", exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await search.fill("clients");
  await nav.getByRole("button", { name: "Customers", exact: true }).click();
  await expect(
    nav.getByRole("button", { name: "Customers", exact: true }),
  ).toHaveAttribute("aria-current", "page");
  expect(
    await nav.evaluate((element) => element.scrollWidth <= element.clientWidth),
  ).toBe(true);
});
