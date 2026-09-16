import { test, expect, type Page } from "@playwright/test";

async function registerCompany(
  page: Page,
  data: { companyName: string; email: string; password: string }
) {
  await page.goto("/company/register");
  await page.getByLabel(/company name/i).fill(data.companyName);
  await page.getByLabel(/email/i).fill(data.email);
  await page.getByLabel(/password/i).fill(data.password);
  await page.getByRole("button", { name: /register/i }).click();
  await page.waitForURL("/company/dashboard");
}

test.describe("Company post-job flow", () => {
  test("register company, post a job, see it in dashboard", async ({ page }) => {
    const company = {
      companyName: `E2E Corp ${Date.now()}`,
      email: `company-${Date.now()}@test.com`,
      password: "password123",
    };

    await registerCompany(page, company);
    await expect(page).toHaveURL(/\/company\/dashboard/);

    // Navigate to post a job
    await page.goto("/company/jobs/new");
    await page.getByLabel(/job title/i).fill("Senior Playwright Engineer");
    await page.getByLabel(/description/i).fill("Test-driven development at scale.");
    await page.getByRole("button", { name: /post job/i }).click();

    // Should redirect to jobs list or dashboard
    await expect(page).toHaveURL(/\/company\/jobs/);
    await expect(page.getByText("Senior Playwright Engineer")).toBeVisible();
  });
});
