// Optional browser integration check. Requires caller-provided playwright-core and Chrome.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { execFileSync } = require('node:child_process');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');

(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-proxy-server']});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1050}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    if (process.env.BRIDGE_MODE === '1') {
      await page.route('**/*', async route => {
        const request = route.request();
        const url = new URL(request.url());
        if (url.origin !== 'http://127.0.0.1:8000') return route.abort();
        if (url.pathname.startsWith('/api/')) {
          const result = JSON.parse(execFileSync('python', ['scripts/browser_bridge.py'], {
            input: JSON.stringify({method: request.method(), path: url.pathname, data: request.postDataJSON()}), encoding: 'utf8', env: process.env,
          }));
          return route.fulfill({status: result.status, contentType: 'application/json', body: JSON.stringify(result.body)});
        }
        const assets = {'/': ['web/index.html', 'text/html'], '/app.js': ['web/app.js', 'text/javascript'], '/styles.css': ['web/styles.css', 'text/css']};
        const asset = assets[url.pathname];
        return asset ? route.fulfill({contentType: asset[1], body: fs.readFileSync(asset[0])}) : route.fulfill({status: 404, body: 'Not found'});
      });
    }
    await page.goto('http://127.0.0.1:8000/');
    await page.locator('#app:not([hidden])').waitFor();
    await page.locator('nav a[data-view="content"]').click();
    await page.locator('#caption').fill('Browser test: book a fresh look this week.');
    await page.getByRole('button', {name: 'Save draft'}).click();
    await page.getByRole('button', {name: 'Approve draft'}).click();
    await page.getByRole('button', {name: 'Simulate publish'}).click();
    await page.locator('nav a[data-view="leads"]').click();
    await page.locator('input[name="name"]').fill('Fictional browser customer');
    await page.locator('select[name="post_id"]').selectOption({index: 1});
    await page.locator('form[data-form="lead"] button[type="submit"]').click();
    await page.getByText('Demo lead recorded. No message was sent.', {exact: true}).waitFor();
    await page.locator('nav a[data-view="revenue"]').click();
    await page.locator('#sale-post').selectOption({index: 1});
    await page.locator('#sale-lead').selectOption({index: 1});
    await page.locator('#amount').fill('1499.50');
    await page.getByRole('button', {name: 'Record demo sale'}).click();
    await page.getByRole('button', {name: 'Demo refund'}).waitFor();
    const paid = await page.evaluate(async () => (await fetch('/api/state')).json());
    assert.equal(paid.dashboard.revenue_paise, 149950);
    assert.equal(paid.dashboard.published_count, 1);
    assert.equal(paid.dashboard.leads_count, 1);
    await page.getByRole('button', {name: 'Demo refund'}).click();
    await page.getByText('Reversal recorded', {exact: true}).waitFor();
    const refunded = await page.evaluate(async () => (await fetch('/api/state')).json());
    assert.equal(refunded.dashboard.revenue_paise, 0);
    assert.equal(refunded.ledger.length, 2);
    assert.equal(refunded.ledger.reduce((sum, row) => sum + row.amount_paise, 0), 0);
    await page.locator('nav a[data-view="roadmap"]').click();
    assert.equal(await page.locator('.phase').count(), 11);
    await page.locator('nav a[data-view="overview"]').click();
    fs.mkdirSync('artifacts', {recursive: true});
    await page.screenshot({path: 'artifacts/demo-desktop.png', fullPage: true});
    await page.setViewportSize({width: 360, height: 800});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, 'Mobile page overflow');
    await page.screenshot({path: 'artifacts/demo-mobile.png', fullPage: true});
    assert.deepEqual(errors, []);
    console.log(`PASS (${process.env.BRIDGE_MODE === '1' ? 'intercepted transport to actual backend service; no live HTTP' : 'live local HTTP'}): browser draft → approval → simulated publish → lead → sale → refund; 11 roadmap phases; 360px reflow; no JS errors.`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
