// Retake the README screenshots from a real `ridi-check demo` report.
//   ridi-check demo /tmp/ridi-demo
//   node tools/make_screenshots.js /tmp/ridi-demo/ridi-out/report.html docs/img
// Needs Playwright (`npm install playwright`). The pictures show the demo's synthetic data.
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [report, out] = process.argv.slice(2);
  if (!report || !out) { console.error('usage: node tools/make_screenshots.js REPORT.html OUT_DIR'); process.exit(2); }
  const url = 'file://' + path.resolve(report);
  const browser = await chromium.launch();

  const desktop = await browser.newContext({ viewport: { width: 1000, height: 1200 }, deviceScaleFactor: 2, colorScheme: 'light', locale: 'en-US' });
  const page = await desktop.newPage();
  await page.goto(url); await page.waitForSelector('.tile');
  // From the top of the page to the end of the rates panel.
  const end = await page.evaluate(() => Math.ceil(document.querySelectorAll('main section')[1].getBoundingClientRect().bottom + window.scrollY + 20));
  await page.screenshot({ path: path.join(out, 'report.png'), clip: { x: 0, y: 0, width: 1000, height: end }, fullPage: true });
  // The first case to review, with its passages open.
  await page.locator('#c-0 details.ctx summary').click();
  await page.locator('#c-0').screenshot({ path: path.join(out, 'report-case.png') });

  const phone = await browser.newContext({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 2, colorScheme: 'dark', locale: 'ar-SA' });
  const small = await phone.newPage();
  await small.goto(url); await small.waitForSelector('.tile');
  await small.screenshot({ path: path.join(out, 'report-phone-ar.png') });
  await browser.close();
})();
