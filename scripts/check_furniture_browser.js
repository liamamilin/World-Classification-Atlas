// Furniture acceptance cases against the generated pages in a real offline Chromium browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { root, href, until, buildRegistry, withOfflineBrowser } = require('./offline_browser');
const checkNaceIsic = require('./check_furniture_nace_isic');

const registry = 'data/reports/registry.html';
const old = 'FR_NAF:Rev.2:31.01Z';
const current = 'FR_NAF:2025:31.00G';
const whole = 'urn:atlas:concept:df67a84e-39ed-547f-b0f1-8d1dfbf6233e';
const part = 'urn:atlas:concept:a62f38d1-7dd9-52ae-b515-2d39384f83ac';
const json = JSON.stringify;

async function run(temp, { page, evaluate, text, exists, linksTo, click, navigate, expand, openOriginal, openClaim }) {
  async function expectNode(id, title, scheme) {
    await until(() => evaluate('document.querySelector("#detail > small")?.innerText === ' + json(id)), id);
    assert.match(await text('#detail > h2'), title);
    assert.equal(await evaluate('document.querySelector("#scheme").value'), scheme);
    assert.ok(await exists('#tree a[aria-current]' + href(id)), id + ' selected in the tree');
  }
  const toNode = async (group, id, title, scheme) => {
    await click(linksTo(group, id));
    await expectNode(id, title, scheme);
  };

  await navigate(path.join(root, registry));
  await evaluate(`(() => {
    const filter = document.querySelector('#domain');
    filter.value = '01-economy';
    filter.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  await click('#furniture-entry a');
  await until(() => exists('#tree a'), 'furniture directory');
  assert.equal(await evaluate('navigator.onLine'), false);

  const wholeTitle = /木制店铺柜台和展柜整品制造中的内置件装配/;
  const partTitle = /木制店铺家具内置部件制造/;
  await toNode('nav', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  assert.equal(await exists(linksTo('#approved-backlinks', part)), false);
  await toNode('#approved-backlinks', whole, wholeTitle, 'atlas');
  assert.match(await text('#approved-bindings'), /FR_NAF:Rev\.2:31\.01Z · broadMatch/);
  assert.match(await text('#approved-bindings'), /FR_NAF:2025:31\.00G · broadMatch/);
  await openClaim('#approved-bindings', 'FN001', 'naf-rev2-cpf21-notes-2020', { pdfPage: 422, mode: 'pdf' });
  await toNode('#approved-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  await toNode('#pending-backlinks', part, partTitle, 'atlas');
  assert.match(await text('#candidate-bindings'), /FR_NAF:Rev\.2:31\.01Z · 未批准关系/);
  assert.match(await text('#candidate-bindings'), /"relation": null/);
  assert.match(await text('#candidate-bindings'), /"status": "pending_specialist_scope"/);
  assert.match(await text('#approved-bindings'), /FR_NAF:2025:31\.00G · broadMatch/);
  assert.equal(await exists(linksTo('#approved-bindings', old)), false);
  await openClaim('#approved-bindings', 'FN003', 'naf-2025-notes-2025', {
    pdfPage: 160, mode: 'pdf', excerpt: 'la fabrication de composants intégrés pour meubles de magasin'
  });
  await toNode('#candidate-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  await evaluate('history.back()');
  await expectNode(part, partTitle, 'atlas');
  await toNode('#approved-bindings', current, /^31\.00G /, 'FR_NAF:2025');
  await toNode('#approved-backlinks', part, partTitle, 'atlas');
  await toNode('#approved-bindings', current, /^31\.00G /, 'FR_NAF:2025');
  await toNode('#approved-backlinks', whole, wholeTitle, 'atlas');
  await toNode('#approved-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  console.log('Passed: both directions of reviewed and pending bindings, stable history, PDF pages 422 and 160.');

  for (const [resource, locator, from, to, title, scheme] of [
    ['naf-rev2-to-2025-202610', 'NAF rév. 2 vers NAF 2025 · 第 383 行', old, current, /^31\.00G /, 'FR_NAF:2025'],
    ['naf-2025-to-rev2-202610', 'correspondance inversée NAF · 第 382 行', current, old, /^31\.01Z /, 'FR_NAF:Rev.2']
  ]) {
    const index = await evaluate(`Array.from(document.querySelectorAll('#official-rows > details'))
      .findIndex(node => node.firstElementChild.innerText.startsWith(${json(from + ' → ' + to + ' · ')}) &&
        node.querySelector('.reference')?.textContent.includes(${json(locator)}))`);
    assert.ok(index >= 0, locator);
    const details = '#official-rows > details:nth-of-type(' + (index + 1) + ')';
    await click(details + ' > summary');
    const opened = details + '[open]';
    assert.match(await text(opened + ' > pre'), /"publisher_mapping_type": "Multiple"/);
    assert.match(await text(opened + ' > summary'), /relatedMatch/);
    assert.ok((await text(opened + ' > .reference')).includes(locator));
    await openOriginal(opened + ' > .reference a', resource);
    await toNode(opened, to, title, scheme);
  }
  console.log('Passed: NAF official rows 383 and 382 and both workbook downloads match their pins.');
  await checkNaceIsic({ page, evaluate, text, exists, click, toNode, expand, openClaim, openOriginal });
  await click('nav[aria-label="经济活动导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "01-economy"'), 'registry return');
  console.log('Passed: registry return restores the economy filter.');

  const fixture = path.join(temp, 'fixture');
  for (const file of ['data/registry', 'data/source-candidates.csv', 'data/resources.lock.json',
    'data/reports/furniture-alignment.json']) {
    fs.cpSync(path.join(root, file), path.join(fixture, file), { recursive: true });
  }
  fs.mkdirSync(path.join(fixture, 'data/local'), { recursive: true });
  for (const raw of ['data/raw', 'data/local/raw']) fs.symlinkSync(path.join(root, raw), path.join(fixture, raw), 'dir');
  const fixtureRegistry = path.join(fixture, registry);
  const entry = '#furniture-entry';
  async function unavailable(query, message) {
    buildRegistry(fixture);
    await navigate(fixtureRegistry, '?domain=01-economy&fixture=' + query);
    assert.match(await text(entry), message);
    assert.match(await text(entry), /python3 -m atlas_sources furniture\s+python3 -m atlas_sources report/);
    assert.equal(await exists(entry + ' a'), false);
  }
  await unavailable('missing-view', /本地家具浏览页尚未生成/);
  const staleView = path.join(fixture, 'data/local/economy/furniture/index.html');
  fs.mkdirSync(path.dirname(staleView), { recursive: true });
  fs.writeFileSync(staleView, 'stale test page');
  await unavailable('stale-view', /本地家具浏览页需要更新/);
  fs.unlinkSync(path.join(fixture, 'data/local/raw'));
  await unavailable('missing-assets', /本地家具资料缺失或校验失败/);
  assert.match(await text(entry), /python3 -m atlas_sources collect/);
  console.log('Passed: missing page, stale page and missing raw snapshots show recovery instructions.');
}


withOfflineBrowser(run).catch(error => { console.error(error); process.exitCode = 1; });
