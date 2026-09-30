/* End-to-end review: npm install playwright, then node scripts/verify_web_ui.cjs URL OUTPUT_DIR [ALGORITHM].
   Requires installed Google Chrome and an isolated MUSTACHE_PROJECTS_DIR on the server. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const base = process.argv[2] || 'http://127.0.0.1:5000';
const output = path.resolve(process.argv[3] || 'ui-review');
const algorithm = process.argv[4] || 'core-sg';
if (!['core-sg', 'hdbscan'].includes(algorithm)) throw new Error('Choose core-sg or hdbscan.');
fs.mkdirSync(output, { recursive: true });
const report = { algorithm, assertions: [], errors: [], responses: [] };
function check(name, condition, detail = '') {
  report.assertions.push({ name, passed: !!condition, detail });
  if (!condition) throw new Error(`${name}: ${detail}`);
}
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1200 }, acceptDownloads: true });
  const page = await context.newPage();
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('console', event => { if (event.type() === 'error') report.errors.push(event.text()); });
  page.on('response', response => { if (response.status() >= 400) report.responses.push({ url: response.url(), status: response.status() }); });
  page.on('dialog', dialog => dialog.accept());
  try {
    for (const route of ['/', '/datasets', '/projects', '/settings']) {
      await page.goto(base + route, { waitUntil: 'networkidle' });
      check(`content on ${route}`, (await page.locator('body').innerText()).length > 100);
      const images = await page.evaluate(() => [...document.images].map(i => ({ alt: i.alt, width: i.naturalWidth })));
      check(`images on ${route}`, images.every(i => i.width > 0), JSON.stringify(images));
    }
    await page.goto(base + '/?sample_dataset=iris', { waitUntil: 'networkidle' });
    const form = page.locator('#batch-form');
    await form.waitFor({ state: 'visible' });
    check('fresh browser defaults to CORE-SG', await form.locator('[name=algorithm]').inputValue() === 'core-sg');
    await form.locator('[name=algorithm]').selectOption(algorithm);
    await form.locator('[name=metric]').selectOption('manhattan');
    for (const [name, value] of Object.entries({ min_mpts: '2', max_mpts: '10', step: '2' })) await form.locator(`[name=${name}]`).fill(value);
    const batchResponse = page.waitForResponse(r => r.url().endsWith('/batch'));
    await form.locator('[type=submit]').click();
    const response = await batchResponse, data = await response.json();
    check('batch succeeds', response.ok(), JSON.stringify(data.error));
    await page.waitForFunction(() => document.querySelector('#hai-heatmap .heatmaplayer') && document.querySelector('#reachability-container .js-plotly-plot'));
    const expected = { 'proj-algorithm': algorithm === 'core-sg' ? 'CORE-SG' : 'HDBSCAN', 'proj-min-mpts': '2', 'proj-max-mpts': '10', 'proj-step': '2', 'proj-metric': 'manhattan', 'proj-points': '150' };
    for (const [id, value] of Object.entries(expected)) check(`sidebar ${id}`, (await page.locator('#' + id).innerText()) === value);
    check('exact HAI identified', (await page.locator('#hai-method-note').innerText()).startsWith('Exact HAI'));
    check('representative explained', (await page.locator('#reachability-container').innerText()).includes('Representative hierarchy (medoid)'));
    check('reachability corresponds to each mpts', Object.entries(data.results).every(([k, r]) => r.reachability_data.mpts === Number(k) && r.reachability_data.metric === 'manhattan'));
    await page.locator('a[href="#hai-heatmap"]').click();
    check('panel link preserves analysis', await page.locator('#hai-heatmap .heatmaplayer').count() === 1);
    // Plotly emits branch clicks; test exact descendant membership, not line pixels.
    const rootMembers = await page.evaluate(() => {
      const d = document.getElementById('meta-dendrogram');
      const root = d.data.reduce((a, b) => a.meta.mpts_values.length > b.meta.mpts_values.length ? a : b);
      d.emit('plotly_click', { points: [{ data: root }] });
      return window.getSelectedMpts();
    });
    check('root branch selects every requested hierarchy', JSON.stringify(rootMembers) === JSON.stringify(data.analysis.ordered_mpts));
    await page.waitForFunction(() => document.getElementById('cache-indicator').textContent.startsWith('1 meta-clusters'));
    check('manual root has one representative', await page.locator('.reachability-plot-wrapper').count() === 1);
    await page.locator('#inspect-mpts').selectOption('4');
    await page.locator('#inspect-hierarchy').click();
    await page.waitForFunction(() => document.querySelector('#hierarchy-detail-plot .barlayer'));
    check('any hierarchy can be inspected', (await page.locator('#hierarchy-detail-title').innerText()).includes('mpts = 4'));
    await page.locator('#hierarchyDetailModal .close').click();
    await page.locator('#btn-clear-selection').click();
    check('manual selection clears', await page.locator('#selected-branches-badge').isHidden());
    const cutResponse = page.waitForResponse(r => r.url().endsWith('/cut_dendrogram'));
    await page.locator('#meta-selection-mode').selectOption('threshold');
    const partition = await (await cutResponse).json();
    await page.waitForFunction(() => document.getElementById('meta-dendrogram').layout.shapes.length === 1);
    check('threshold partition has aligned labels', partition.meta_labels.length === data.analysis.ordered_mpts.length);
    // Include a root selection in the persisted project.
    await page.evaluate(() => {
      const d = document.getElementById('meta-dendrogram');
      const root = d.data.reduce((a, b) => a.meta.mpts_values.length > b.meta.mpts_values.length ? a : b);
      d.emit('plotly_click', { points: [{ data: root }] });
    });
    await page.locator('#btn-save-top').click();
    await page.locator('#main-save-proj-name').fill('Scientific review — Iris Manhattan');
    const saveResponse = page.waitForResponse(r => r.url().endsWith('/api/projects/save'));
    await page.getByRole('button', { name: 'Save project', exact: true }).click();
    const saved = await (await saveResponse).json();
    check('saved project created', !!saved.project?.id);
    await page.goto(base + '/?project_id=' + saved.project.id, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => document.querySelector('#hai-heatmap .heatmaplayer') && document.querySelector('#reachability-container .js-plotly-plot'));
    for (const [id, value] of Object.entries(expected)) check(`restored ${id}`, (await page.locator('#' + id).innerText()) === value);
    check('restored manual mode', await page.locator('#meta-selection-mode').inputValue() === 'manual');
    check('restored manual medoid', await page.locator('.reachability-plot-wrapper').count() === 1);
    check('restored selected hierarchy count', (await page.evaluate(() => window.getSelectedMpts())).length === rootMembers.length);
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#btn-export-csv').click();
    const download = await downloadPromise;
    await download.saveAs(path.join(output, 'selected_clusters.csv'));
    check('CSV exported all selected mpts', rootMembers.every(k => fs.readFileSync(path.join(output, 'selected_clusters.csv'), 'utf8').includes('Cluster_mpts_' + k)));
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    await page.addStyleTag({ content: 'body { filter: grayscale(1); }' });
    await page.screenshot({ path: path.join(output, 'grayscale.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + '/?project_id=' + saved.project.id, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => document.querySelector('#hai-heatmap .heatmaplayer'));
    const widths = await page.evaluate(() => [document.body.scrollWidth, window.innerWidth]);
    check('mobile no page overflow', widths[0] <= widths[1] + 2, JSON.stringify(widths));
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    check('no browser JS errors', report.errors.length === 0, JSON.stringify(report.errors));
    check('no failed asset/API responses', report.responses.length === 0, JSON.stringify(report.responses));
    report.project_id = saved.project.id;
  } finally {
    fs.writeFileSync(path.join(output, 'verification.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
