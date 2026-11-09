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
const workbook = 'cpc3-notes-xlsx-20250630';
const listing = 'cpc3-correspondence-listing-20261109';
const status = 'cpc3-hs2022-status-202605';
const guidance = 'hs2022-wco-who-medical-supplies';
const chapter = 'hs2022-chapter68';
const legacy = 'cpc21-hs2017-unsd-correspondence';
const id = code => 'CPC:3.0:' + code;
const hsId = code => 'HS:2022:' + code;
const ice = ['1', '17', '174', '1740', '17400'];
const edibleIce = ['2', '22', '222', '2227', '22270'];
const dryIce = ['3', '34', '342', '3421', '34210'];
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
  async function search(codes) {
    await evaluate(`(() => {
      const input = document.querySelector('#search');
      input.value = ${json(codes.at(-1))};
      input.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    assert.match(await text('#count'), /匹配 1 项/);
    await click(linksTo('#results', id(codes.at(-1))));
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
  assert.match(await text('#coverage'), /4586 个源节点 · 5 级目录 · 8 个已定位说明条目/);
  assert.match(await text('#coverage'), /69 条 HS 2022 原文引用/);
  assert.match(await text('header'), /CPC 分类对象为产品与服务，ISIC 分类对象为经济活动/);
  await click('#release-status summary');
  assert.match(await text('#release-status'), /未列出完整的 CPC 3\.0 与 HS 2022 对应表/);
  await openOriginal('#unsd-listing', listing, { mode: 'html', elementId: 'corresp-cpc' });
  await openOriginal('#release-status a:not(#unsd-listing)', status, { mode: 'pdf', pdfPage: 46 });
  await click('#release-status summary');

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

  await click(linksTo('#exclusions', id('34210')));
  await expectNode(dryIce);
  assert.match(await text('#detail > h2'), /^34210 .*carbon dioxide/);
  assert.match(await text('#structure-source'), /第 1419 行/);
  assert.match(await text('#note-status'), /仅列标题/);
  assert.equal(await exists('#note-text'), false);
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 160 });
  await click(linksTo('#exclusion-backlinks', id('17400')));
  await expectNode(ice);
  console.log('Passed: 17400 → dry ice 34210, title-only source PDF, stable path and backlink.');

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

  for (const codes of [ice, edibleIce]) await search(codes);
  console.log('Passed: original 17400/22270 routes and PDF pages 63/101.');

  const titleEntries = [
    { codes: ['4', '48', '481', '4816', '48160'], page: 264, row: 2598,
      title: /excluding protective masks having neither mechanical parts nor replaceable filters/ },
    { codes: ['2', '27', '271', '2719', '27190'], page: 127, row: 1058,
      title: /Other made-up textile articles/ },
    { codes: ['3', '37', '379', '3799', '37990'], page: 187, row: 1741,
      title: /non-electrical articles of graphite or other carbon/ },
    { codes: ['4', '46', '469', '4695', '46950'], page: 254, row: 2502,
      title: /articles of graphite or other carbon of a kind used for electrical purposes/ }
  ];
  for (const { codes, page, row, title } of titleEntries) {
    await search(codes);
    assert.match(await text('#detail > h2'), title);
    assert.ok((await text('#structure-source')).includes('第 ' + row + ' 行'));
    assert.match(await text('#note-status'), /仅列标题/);
    assert.match(await text('#pending-scope'), /归属待核|子类待核/);
    assert.equal(await exists('#note-text'), false);
    assert.equal(await exists('#exclusions'), false);
    await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: page });
  }
  await search(['8', '89', '892', '8920', '89200']);
  assert.match(await text('#detail > h2'), /plastic manufacturing services/);
  assert.match(await text('#structure-source'), /第 4241 行/);
  assert.match(await text('#note-text'), /manufacturing services of plastic parts[\s\S]*carbon fibre[\s\S]*for third parties/);
  assert.match(await text('#pending-scope'), /产出制品的产品子类待核/);
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 487 });
  console.log('Passed: protective-mask and carbon scope, pending product placement and PDF pages 127/187/254/264/487.');

  async function openHs(group, code) {
    await click(linksTo(group, hsId(code)));
    await until(() => evaluate('document.querySelector("#node-id")?.innerText === ' + json(hsId(code))), hsId(code));
    assert.match(await text('#detail'), /HS 分类对象为贸易商品/);
  }
  async function backToCpc(codes) {
    await click(linksTo('#hs-backlinks', id(codes.at(-1))));
    await expectNode(codes);
  }
  const masks = titleEntries[0].codes;
  const textiles = titleEntries[1].codes;
  const carbon = titleEntries[2].codes;
  await search(masks);
  assert.match(await text('#hs-review'), /第 2598 行无明确 HS 2022 引用/);
  assert.match(await text('#hs-findings [data-status=excluded_from_cpc]'), /同时无机械部件和可换滤芯/);
  await openOriginal('#review-workbook a', workbook);
  await openHs('#hs-findings', '6307.90');
  assert.match(await text('#detail > h2'), /纺织口罩示例/);
  await openOriginal('#hs-original a', guidance, { mode: 'pdf', pdfPage: 3 });
  assert.match(await text('#hs-backlinks'), /48160 · CPC 原文排除/);
  assert.match(await text('#hs-backlinks'), /27190 · 当前对应待核/);
  await backToCpc(textiles);
  assert.match(await text('#legacy-hs'), /HS:2017:6307\.90 ↔ CPC:2\.1:27190 · HS partial=0 · CPC partial=1/);
  await openOriginal('#legacy-hs a', legacy);
  await openHs('#hs-findings', '6307.90');
  await backToCpc(masks);
  await openHs('#hs-findings', '9020.00');
  assert.match(await text('#detail > h2'), /带机械部件或可更换滤芯/);
  await backToCpc(masks);
  await openHs('#hs-findings', '4818.90');
  assert.match(await text('#detail > h2'), /纸或纤维素口罩示例（多数国家）/);
  await openHs('#detail', '4818');
  await backToCpc(['3', '32', '321', '3219', '32193']);
  assert.match(await text('#official-hs-notes'), /官方定义引用 · CPC3!C1289/);
  await openOriginal('#official-hs-notes a[download]', workbook);
  await openHs('#official-hs-notes', '4818');
  await backToCpc(['3', '32', '321', '3219', '32193']);
  console.log('Passed: textile, paper and respirator boundaries, historical partial flags, and a current UNSD heading reference.');

  await search(carbon);
  assert.match(await text('#legacy-hs'), /HS:2017:6815\.99 ↔ CPC:2\.1:37990 · HS partial=0 · CPC partial=1/);
  for (const [code, label] of [['6815.11', /碳纤维本体/], ['6815.12', /碳纤维织物/],
    ['6815.13', /其他碳纤维制品.*非电气/], ['6815.19', /该非电气用组中的其他项/]]) {
    await openHs('#hs-findings', code);
    assert.match(await text('#detail > h2'), label);
    const rows = await text('#hs-version-rows');
    if (code === '6815.19') assert.match(rows, /HS 2017 6815\.10/);
    else assert.match(rows, /ex6815\.99（旧子目部分对应）/);
    if (code === '6815.12') {
      await openOriginal('#hs-original a', chapter, { mode: 'pdf', pdfPage: 4 });
      await openOriginal('#hs-table-i', 'hs2022-to-hs2017-wco-table-i', { mode: 'pdf', pdfPage: 17 });
      await openOriginal('#hs-table-ii', 'hs2017-to-hs2022-wco-table-ii', { mode: 'pdf', pdfPage: 11 });
    }
    await backToCpc(carbon);
    assert.match(await text('#hs-review'), /第 1741 行无明确 HS 2022 引用/);
  }
  await openHs('#hs-findings', '6815.13');
  await backToCpc(titleEntries[3].codes);
  assert.match(await text('#hs-findings'), /电气用范围.*非电气用边界/);
  await search(['8', '89', '892', '8920', '89200']);
  assert.match(await text('#hs-findings [data-status=service_context]'), /受托塑料件制造服务/);
  assert.equal(await exists('#hs-findings a'), false);
  await search(['4', '46', '465', '4653', '46532']);
  assert.match(await text('#official-hs-notes'), /官方定义引用[\s\S]*9405\.39[\s\S]*官方排除引用[\s\S]*9405\.31/);
  console.log('Passed: four carbon subheadings, both original WCO tables, partial semantics, and separate electrical/service scopes.');

  await navigate(path.join(root, view), '#' + encodeURIComponent(id('22270')));
  await expectNode(edibleIce);
  await click('nav[aria-label="产品与服务导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "02-products"'), 'products registry return');
  assert.equal(await evaluate('document.querySelector("#isic-pilot").hidden'), true);
  console.log('Passed: stable deep link and registry return.');

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
