// CPC source catalogue acceptance in a real Chromium session with networking disabled.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { root, until, buildRegistry, withOfflineBrowser } = require('./offline_browser');

const registry = 'data/reports/registry.html';
const view = 'data/local/products/cpc/index.html';
const report = 'data/reports/cpc-offline.json';
const structure = 'cpc3-structure';
const notes = 'cpc3-notes-20250630';
const id = code => 'CPC:3.0:' + code;
const ice = ['1', '17', '174', '1740', '17400'];
const edibleIce = ['2', '22', '222', '2227', '22270'];
const json = JSON.stringify;

async function run(temp, { evaluate, text, exists, linksTo, click, navigate, openOriginal }) {
  async function expectNode(codes) {
    const code = codes.at(-1);
    await until(() => evaluate('document.querySelector("#node-id")?.innerText === ' + json(id(code))), id(code));
    assert.equal(await evaluate('decodeURIComponent(location.hash.slice(1))'), id(code));
    assert.deepEqual(await evaluate('Array.from(document.querySelectorAll("#ancestors > li"), node => node.dataset.code)'), codes);
  }
  async function walk(codes) {
    for (const code of codes.slice(0, -1)) {
      const branch = '#tree details[data-code="' + code + '"]';
      await until(() => exists(branch + ' > summary'), code + ' branch');
      await click(branch + ' > summary');
      await until(() => exists(branch + '[open] > ul'), code + ' children');
    }
    await click(linksTo('#tree', id(codes.at(-1))));
    await expectNode(codes);
  }

  await navigate(path.join(root, registry));
  await evaluate(`(() => {
    const filter = document.querySelector('#domain');
    filter.value = '02-products';
    filter.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  assert.equal(await evaluate('document.querySelector("#isic-pilot").hidden'), true);
  await click('#cpc-entry a');
  await until(() => exists('#tree > li'), 'CPC catalogue from registry');
  assert.equal(await evaluate('navigator.onLine'), false);
  assert.match(await text('#coverage'), /4586 个源节点 · 5 级目录 · 2 个已定位说明条目/);
  assert.match(await text('header'), /CPC 分类对象为产品与服务，ISIC 分类对象为经济活动/);

  await walk(ice);
  assert.match(await text('#detail > h2'), /^17400 Ice and snow$/);
  assert.match(await text('#structure-source'), /第 531 行/);
  assert.match(await text('#note-text'), /natural ice and snow[\s\S]*artificially frozen water/);
  assert.match(await text('#note-text'), /edible ice, cf\. 22270[\s\S]*dry ice .*cf\. 34210/);
  assert.deepEqual(await evaluate(`Array.from(document.querySelectorAll('#exclusions a'),
    link => decodeURIComponent(link.hash.slice(1)))`), [id('22270'), id('34210')]);
  await openOriginal('#structure-source a', structure);
  console.log('Passed: source CSV download matches the locked snapshot.');
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 63 });

  await click(linksTo('#exclusions', id('22270')));
  await expectNode(edibleIce);
  assert.match(await text('#detail > h2'), /^22270 Ice cream and other edible ice$/);
  assert.match(await text('#structure-source'), /第 781 行/);
  assert.match(await text('#note-status'), /仅列标题/);
  assert.equal(await exists('#note-text'), false);
  assert.equal(await exists('#exclusions'), false);
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 101 });
  await click(linksTo('#exclusion-backlinks', id('17400')));
  await expectNode(ice);
  await walk(edibleIce);

  for (const codes of [ice, edibleIce]) {
    await evaluate(`(() => {
      const input = document.querySelector('#search');
      input.value = ${json(codes.at(-1))};
      input.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    assert.match(await text('#count'), /匹配 1 项/);
    await click(linksTo('#results', id(codes.at(-1))));
    await expectNode(codes);
  }
  await navigate(path.join(root, view), '#' + encodeURIComponent(id('22270')));
  await expectNode(edibleIce);
  await click('nav[aria-label="产品与服务导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "02-products"'), 'products registry return');
  assert.equal(await evaluate('document.querySelector("#isic-pilot").hidden'), true);
  console.log('Passed: CPC five-level tree, two stable code paths, search, exclusions, CSV and PDF pages 63/101, registry return.');

  const fixture = path.join(temp, 'fixture');
  const copy = file => fs.cpSync(path.join(root, file), path.join(fixture, file), { recursive: true });
  for (const file of ['data/registry', 'data/source-candidates.csv', 'data/resources.lock.json']) copy(file);
  const baseline = JSON.parse(fs.readFileSync(path.join(root, report), 'utf8'));
  for (const input of baseline.inputs) copy(path.dirname(input.path));
  async function registryState(state, expected) {
    buildRegistry(fixture);
    await navigate(path.join(fixture, registry), '?domain=02-products&fixture=' + state);
    assert.match(await text('#cpc-entry'), expected);
    assert.equal(await exists('#cpc-entry a'), state === 'ready');
  }
  await registryState('not-generated', /浏览页尚未生成/);
  execFileSync('python3', ['-m', 'atlas_sources', '--root', fixture, 'cpc'], { cwd: root });
  for (const file of [view, report]) {
    assert.ok(fs.readFileSync(path.join(fixture, file)).equals(fs.readFileSync(path.join(root, file))), file);
  }
  await registryState('ready', /打开 CPC 3\.0 离线目录/);
  fs.appendFileSync(path.join(fixture, view), '<!-- stale test page -->');
  await registryState('stale', /浏览页需要更新/);
  const missing = baseline.inputs.find(input => input.resource_id === notes).path;
  fs.unlinkSync(path.join(fixture, missing));
  await registryState('missing-notes', /资料缺失或校验失败/);
  assert.match(await text('#cpc-entry'), /python3 -m atlas_sources collect/);
  console.log('Passed: 2/2 clean rebuild outputs are byte-identical and catalogue readiness states are correct.');
}

withOfflineBrowser(run).catch(error => { console.error(error); process.exitCode = 1; });
