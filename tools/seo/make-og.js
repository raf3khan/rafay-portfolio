// Renders the 1200x630 social share images in og/ from tools/seo/og-cards.json.
// Run locally: node tools/seo/make-og.js  (needs Playwright with Chromium).
// To add a tool: add an entry to og-cards.json, run this, commit og/<name>.png.
const { chromium } = require("playwright");
const path = require("path");
const cards = require("./og-cards.json");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  const tpl = "file://" + path.join(__dirname, "og-card.html");
  for (const [name, c] of Object.entries(cards)) {
    await page.goto(tpl + "?" + new URLSearchParams(c));
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(__dirname, "..", "..", "og", name + ".png") });
    console.log("og/" + name + ".png");
  }
  await browser.close();
})();
