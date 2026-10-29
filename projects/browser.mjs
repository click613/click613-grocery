// Browser for the "second platform" store readers (fetch_v2.mjs). GitHub version, replaces the Tab browser door.
// Default: a local headless Chromium (Playwright) on the GitHub runner, nothing to configure.
// Optional: if the repo secrets BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID are set, a Browserbase cloud browser is used
// instead (that is what these readers used before; some store sites put a Cloudflare check in front that a cloud browser passes more often).
// No logins, no CAPTCHA solving: a reader that meets a robot check fails and that store keeps its previous prices.
import { chromium } from "playwright";

const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36";

export async function openBrowser(tag) {
  const key = process.env.BROWSERBASE_API_KEY, project = process.env.BROWSERBASE_PROJECT_ID;
  if (key && project) {
    const r = await fetch("https://api.browserbase.com/v1/sessions", {
      method: "POST", headers: { "X-BB-API-Key": key, "Content-Type": "application/json" },
      body: JSON.stringify({ projectId: project, keepAlive: false, timeout: 1800, userMetadata: { site: String(tag || "grocery") } }) });
    if (!r.ok) throw new Error("browserbase session " + r.status + " " + (await r.text()).slice(0, 200));
    const s = await r.json();
    const browser = await chromium.connectOverCDP(s.connectUrl);
    const context = browser.contexts()[0] || await browser.newContext();
    const page = context.pages()[0] || await context.newPage();
    return { browser, context, page, close: () => browser.close() };
  }
  const browser = await chromium.launch({ headless: true, args: ["--disable-blink-features=AutomationControlled", "--no-sandbox"] });
  const context = await browser.newContext({ userAgent: UA, locale: "en-US", timezoneId: "America/New_York", viewport: { width: 1366, height: 900 } });
  await context.addInitScript(() => { Object.defineProperty(navigator, "webdriver", { get: () => undefined }); });
  const page = await context.newPage();
  return { browser, context, page, close: () => browser.close() };
}
