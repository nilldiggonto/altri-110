import { expect, test, type Browser, type Page } from "@playwright/test"

// Changes must reach the other browser "within about a second"; allow some CI slack.
const SYNC_MS = 2_000
// Set E2E_FORCE_FAIL=1 to make the follower expect the wrong section (produces a failure trace).
const WRONG = process.env.E2E_FORCE_FAIL === "1"

async function signIn(browser: Browser, name: string): Promise<Page> {
  // A separate context per user: own cookies, storage and WebSocket, like a second browser.
  const ctx = await browser.newContext()
  const page = await ctx.newPage()
  await page.goto("/login")
  await page.locator("ul button", { hasText: name }).click()
  await page.waitForURL("**/teams/**")
  return page
}

test("facilitator advances the agenda and the second browser follows", async ({ browser }) => {
  const facilitator = await signIn(browser, "Blake Brooks") // Team Member, team_lead
  const follower = await signIn(browser, "Casey Cho") // Team Member, team_lead

  await facilitator.goto("/teams/team_lead/meeting")
  await facilitator.getByRole("button", { name: "Start meeting" }).click()
  await expect(facilitator.getByText("Now: Scorecard")).toBeVisible()

  // The follower joins late and gets the current state.
  await follower.goto("/teams/team_lead/meeting")
  await follower.getByRole("button", { name: "Join meeting" }).click()
  await expect(follower.getByText("Now: Scorecard")).toBeVisible()
  await expect(follower.getByRole("button", { name: /^Next:/ })).toHaveCount(0) // only the facilitator advances

  await facilitator.getByRole("button", { name: "Next: IDS" }).click()
  await expect(follower.getByText(WRONG ? "Now: Conclude" : "Now: IDS")).toBeVisible({ timeout: SYNC_MS })

  // A refresh mid-meeting keeps the section.
  await follower.reload()
  await expect(follower.getByText("Now: IDS")).toBeVisible()

  await facilitator.getByRole("button", { name: "Next: Conclude" }).click()
  await expect(follower.getByText("Now: Conclude")).toBeVisible({ timeout: SYNC_MS })

  await facilitator.getByRole("button", { name: "End meeting" }).first().click()
  await facilitator.getByRole("dialog").getByRole("button", { name: "End meeting" }).click()
  await expect(follower.getByText("Meeting summary")).toBeVisible({ timeout: SYNC_MS })
})
