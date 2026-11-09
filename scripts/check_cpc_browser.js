// CPC source catalogue acceptance in a real Chromium session with networking disabled.
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { root, until, buildRegistry, withOfflineBrowser } = require('./offline_browser');

const registry = 'data/reports/registry.html';
const view = 'data/local/products/cpc/index.html';
const report = 'data/reports/cpc-offline.json';
const directory = 'data/atlas/products/trade-goods-directory.json';
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
  async function expectNode(codes, hash = id(codes.at(-1))) {
    const code = codes.at(-1);
    await until(() => evaluate('document.querySelector("#node-id")?.innerText === ' + json(id(code))), id(code));
    assert.equal(await evaluate('decodeURIComponent(location.hash.slice(1))'), hash);
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
  assert.match(await text('#coverage'), /4586 个源节点 · 5 级目录 · 13 个已定位说明条目/);
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
  async function backToNote(codes, column = 'C', group = '#hs-official-backlinks') {
    const noteId = id(codes.at(-1)) + ':HS2022:' + column + ':1';
    await click(linksTo(group, noteId));
    await expectNode(codes, noteId);
    assert.equal(await evaluate('document.activeElement.id'), noteId);
  }
  async function evidenceCard(id) {
    const card = '.wco-evidence details[data-evidence-id=' + json(id) + ']';
    await click(card + ' > summary');
    assert.ok(await exists(card + '[open]'));
    return card;
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
  assert.equal(await exists('#hs-official-backlinks a'), false);
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
  await backToNote(['3', '32', '321', '3219', '32193']);
  assert.match(await text('#official-hs-notes'), /官方定义引用 · CPC3!C1289/);
  await openOriginal('#official-hs-notes a[download]', workbook);
  await openHs('#official-hs-notes', '4818');
  await backToNote(['3', '32', '321', '3219', '32193']);
  console.log('Passed: textile, paper and respirator boundaries, historical partial flags, and a current UNSD heading reference.');

  await search(carbon);
  assert.match(await text('#legacy-hs'), /HS:2017:6815\.99 ↔ CPC:2\.1:37990 · HS partial=0 · CPC partial=1/);
  for (const [code, label] of [['6815.11', /碳纤维本体/], ['6815.12', /碳纤维织物/],
    ['6815.13', /其他碳纤维制品.*非电气/], ['6815.19', /该非电气用组中的其他项/]]) {
    await openHs('#hs-findings', code);
    assert.match(await text('#detail > h2'), label);
    assert.equal(await exists('#hs-official-backlinks a'), false);
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
  const christmas = ['4', '46', '465', '4653', '46532'];
  await search(christmas);
  assert.match(await text('#official-hs-notes'), /官方定义引用[\s\S]*9405\.39[\s\S]*官方排除引用[\s\S]*9405\.31/);
  console.log('Passed: four carbon subheadings, both original WCO tables, partial semantics, and separate electrical/service scopes.');

  await openHs('#official-hs-notes [data-kind=exclusion]', '9405.31');
  assert.match(await text('#hs-official-backlinks'), /46532 · 官方排除引用[\s\S]*46533 · 官方定义引用/);
  await openOriginal('#hs-structure-source a[download]', 'hs2022-unsd-structure');
  assert.deepEqual(await evaluate('Array.from(document.querySelectorAll("#ancestors > li"), node => node.dataset.code)'),
    ['XX', '94', '9405', '9405.31']);
  await backToNote(christmas, 'D');
  await openOriginal('#official-hs-notes [data-kind=exclusion] .reference-review a', 'hs2022-chapter94',
    { mode: 'pdf', pdfPage: 4 });

  await search(['1', '11', '110', '1103', '11031']);
  await openHs('#official-hs-notes', '2701.12');
  assert.match(await text('#hs-official-backlinks'), /11012 · 官方定义引用[\s\S]*11031 · 官方定义引用/);
  const coalNote = await evidenceCard('HS:2022:27:WCO:subheading-note-2');
  assert.match(await text(coalNote + ' pre'), /a dry, mineral-matter-free basis[\s\S]*exceeding 14 %[\s\S]*5,833 kcal\/kg/);
  await openOriginal(coalNote + ' a[target]', 'hs2022-chapter27', { mode: 'pdf', pdfPage: 1 });
  const coalGroup = await evidenceCard('HS:2022:2701:WCO:unagglomerated-coal');
  assert.match(await text(coalGroup + ' pre'), /not agglomerated[\s\S]*2701\.19[\s\S]*2701\.20/);
  assert.equal(await exists(linksTo(coalGroup, hsId('2701.20'))), false);
  await openOriginal(coalGroup + ' a[target]', 'hs2022-chapter27', { mode: 'pdf', pdfPage: 2 });
  await backToNote(['1', '11', '110', '1101', '11012']);
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 55 });
  await openHs('#official-hs-notes .reference-targets', '2701.12');
  await backToNote(['1', '11', '110', '1103', '11031']);
  await click('#historical-energy > summary');
  assert.match(await text('#historical-energy pre'), /HS 2017[\s\S]*0210\s+Sub-bituminous coal[\s\S]*2702\.10\*/);
  await openOriginal('#historical-energy a', 'siec1-escm-historical-coal', { mode: 'pdf', pdfPage: 47 });
  assert.match(await text('#legacy-hs'), /HS:2017:2702\.10 ↔ CPC:2\.1:11030/);
  const lignite = await evidenceCard('HS:2022:2702:WCO:lignite');
  await openHs(lignite, '2702.10');
  assert.match(await text('#hs-official-backlinks'), /11032 · 官方定义引用/);
  assert.doesNotMatch(await text('#hs-official-backlinks'), /11031/);
  await click('#choose-cpc');
  await until(() => exists('#choose-cpc[aria-current="page"]'), 'CPC catalogue after HS boundary');

  await search(['3', '35', '352', '3527', '35273']);
  const targets = () => evaluate('Array.from(document.querySelectorAll(".reference-targets a"), a => a.innerText)');
  assert.deepEqual(await targets(), ['3002.41', '3002.42', '3002.49', '3002.51', '3002.59'].map(x => 'HS 2022 ' + x));
  await openOriginal('#official-hs-notes .reference-review a', 'hs2022-chapter30', { mode: 'pdf', pdfPage: 3 });

  const motorcycle = ['4', '49', '499', '4991', '49913'];
  await search(motorcycle);
  assert.match(await text('#official-hs-notes [data-kind=inclusion]'), /8711\.90 的具体范围待核/);
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 276 });
  assert.match(await text('#legacy-hs'), /HS:2017:8711\.90 ↔ CPC:2\.1:49913/);
  await openHs('#official-hs-notes .reference-targets', '8711.90');
  const motorcycleHeading = await evidenceCard('HS:2022:8711:WCO:heading');
  assert.match(await text(motorcycleHeading), /side-cars[\s\S]*8711\.60\s+- With electric motor[\s\S]*8711\.90\s+- Other/);
  await openOriginal(motorcycleHeading + ' .wco-passage:nth-of-type(1) a', 'hs2022-chapter87', { mode: 'pdf', pdfPage: 4 });
  await openOriginal(motorcycleHeading + ' .wco-passage:nth-of-type(2) a', 'hs2022-chapter87', { mode: 'pdf', pdfPage: 5 });
  const chapterNote = await evidenceCard('HS:2022:87:WCO:chapter-note-4');
  await openOriginal(chapterNote + ' a[target]', 'hs2022-chapter87', { mode: 'pdf', pdfPage: 1 });
  const rules = await evidenceCard('HS:2022:WCO:GIR:6');
  await openOriginal(rules + ' a', 'hs2022-wco-interpretation-rules', { mode: 'pdf', pdfPage: 1 });
  await backToNote(motorcycle);
  await openHs('#official-hs-notes .reference-targets', '8711.90');
  await evidenceCard('HS:2022:8711:WCO:heading');
  await openHs(motorcycleHeading, '8711.60');
  await backToNote(motorcycle);

  const octopus = ['2', '21', '212', '2126', '21267'];
  await search(octopus);
  assert.match(await text('#official-hs-notes'), /0307\.53 → 待核 · HS 2022 无该代码/);
  assert.deepEqual(await targets(), ['HS 2022 0307.59']);
  assert.match(await text('#octopus-correction-audit'), /仅返回 4379[\s\S]*03239[\s\S]*仍列 0307\.53/);
  for (const [index, resource, elementId] of [
    [1, 'cpc3-corrections-register-20261109', 'searchResult'],
    [2, 'cpc3-correction-4379', 'PrintDivID'],
    [3, 'cpc3-detail-21267-20261109', 'PrintDivID']
  ]) {
    await openOriginal('#octopus-correction-audit a:nth-of-type(' + index + ')', resource, { mode: 'html', elementId });
  }
  await openOriginal('#note-source a', notes, { mode: 'pdf', pdfPage: 79 });
  await openOriginal('#official-hs-notes .reference-review a:not([href^="#"])', 'hs2022-chapter03',
    { mode: 'pdf', pdfPage: 11 });
  await openHs('#official-hs-notes .reference-review', '0307.52');
  assert.equal(await exists('#hs-official-backlinks a'), false);
  assert.match(await text('#hs-candidate-backlinks'), /21267 · Atlas 待核候选/);
  const octopusGroup = await evidenceCard('HS:2022:0307:WCO:octopus');
  assert.match(await text(octopusGroup + ' pre'), /0307\.51[\s\S]*0307\.52\s+-- Frozen[\s\S]*0307\.59/);
  const powders = await evidenceCard('HS:2022:03:WCO:chapter-note-3');
  await openOriginal(powders + ' .wco-passage:nth-of-type(1) a', 'hs2022-chapter03', { mode: 'pdf', pdfPage: 1 });
  await openOriginal(powders + ' .wco-passage:nth-of-type(2) a', 'hs2022-chapter03', { mode: 'pdf', pdfPage: 12 });
  await openHs(powders, '0309.90');
  assert.doesNotMatch(await text('#hs-official-backlinks'), /21267/);
  const powderBoundary = await evidenceCard('HS:2022:03:WCO:chapter-note-3');
  assert.match(await text(powderBoundary + ' pre'), /03\.05 to 03\.08 do not cover/);
  await openHs(powderBoundary, '0309');
  await searchHs('030752', '0307.52');
  await evidenceCard('HS:2022:0307:WCO:octopus');
  await openHs(octopusGroup, '0307.59');
  await backToNote(octopus);
  await openHs('#official-hs-notes .reference-review', '0307.52');
  await backToNote(octopus, 'C', '#hs-candidate-backlinks');
  console.log('Passed: UNSD correction audit, WCO group and note originals, and historical versus current scope paths.');

  const baseline = JSON.parse(fs.readFileSync(path.join(root, report), 'utf8'));
  const references = baseline.hs_review.official_note_references;
  assert.equal(references.length, 69);
  assert.equal(references.reduce((sum, ref) => sum + ref.target_ids.length, 0), 184);
  const failures = await evaluate(`(() => {
    const refs = ${json(references.map(ref => ({ id: ref.id, kind: ref.kind, targets: ref.target_ids })))};
    const links = group => Array.from(group.querySelectorAll('a'), a => decodeURIComponent(a.hash.slice(1)));
    const errors = [];
    for (const ref of refs) {
      renderSelection(ref.id);
      const row = document.getElementById(ref.id);
      if (row?.dataset.kind !== ref.kind || JSON.stringify(links(row.querySelector('.reference-targets'))) !==
          JSON.stringify(ref.targets)) errors.push(ref.id);
      for (const target of ref.targets) {
        renderSelection(target);
        const back = document.querySelector('#hs-official-backlinks');
        if (!back || !Array.from(back.children).some(item => item.dataset.kind === ref.kind &&
            links(item).includes(ref.id))) errors.push(target + ' → ' + ref.id);
      }
    }
    return errors;
  })()`);
  assert.deepEqual(failures, []);
  console.log('Passed: all 69 worksheet clauses and all 184 resolved forward/reverse links; absent and candidate codes kept separate.');

  await navigate(path.join(root, view), '#' + encodeURIComponent(id('22270')));
  await expectNode(edibleIce);
  await click('nav[aria-label="产品与服务导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "02-products"'), 'products registry return');
  assert.equal(await evaluate('document.querySelector("#isic-pilot").hidden'), true);
  await click('#hs-entry');
  await until(() => exists('#tree[aria-label="HS 2022 四级源目录"]'), 'HS catalogue from registry');
  assert.match(await text('#detail'), /6957 个源节点/);
  await click('#tree details[data-code="XX"] > summary');
  await until(() => exists('#tree details[data-code="94"]'), 'WCO section XX includes chapter 94');
  await openHs('#tree', 'XX');
  await openOriginal('#hs-structure-source a', 'hs2022-wco-contents', { mode: 'pdf', pdfPage: 5 });
  async function searchHs(query, code) {
    await evaluate(`(() => {
    const input = document.querySelector('#search');
    input.value = ${json(query)};
    input.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
    await openHs('#results', code);
  }
  await searchHs('940531', '9405.31');
  await searchHs('30.01', '3001');
  await click('nav[aria-label="产品与服务导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "02-products"'), 'HS registry return');
  console.log('Passed: stable deep link and registry return.');

  const goods = JSON.parse(fs.readFileSync(path.join(root, directory), 'utf8'));
  const bySlug = new Map(goods.nodes.map(node => [node.code, node]));
  const bindingSelector = (group, binding) => group + ' li[data-binding-id=' + json(binding.id) + ']';
  const bindingFor = (concept, source) => concept.binding_ids.map(id => goods.bindings[id])
    .find(binding => binding.source_id === source);
  async function expectGoods(concept) {
    await until(() => evaluate('document.querySelector("#node-id")?.innerText === ' + json(concept.id)), concept.code);
    assert.equal(await evaluate('decodeURIComponent(location.hash.slice(1))'), concept.id);
  }
  async function searchGoods(query, concept) {
    await evaluate(`(() => {
      const input = document.querySelector('#search');
      input.value = ${json(query)};
      input.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    await click(linksTo('#results', concept.id));
    await expectGoods(concept);
  }
  async function backToGoods(concept, binding) {
    await click(bindingSelector('#atlas-backlinks', binding) + ' > a');
    await expectGoods(concept);
  }
  assert.deepEqual(goods.summary.node_status, { navigation: 8, reviewed: 6, pending: 5 });
  assert.deepEqual(goods.summary.binding_status, { reviewed: 14, pending: 11 });
  await click('#atlas-goods-entry');
  await until(() => exists('#choose-atlas[aria-current="page"]'), 'Atlas goods from registry');
  assert.match(await text('#detail'), /6 个已审商品范围 · 5 个待核范围/);
  const reviewedGoods = bySlug.get('tree-lights-led-only');
  for (const slug of ['trade-goods', 'lighting', 'tree-lights']) {
    const branch = '#tree details[data-code=' + json(slug) + ']';
    await click(branch + ' > summary');
    await until(() => exists(branch + '[open] > ul'), slug + ' children');
  }
  await click(linksTo('#tree', reviewedGoods.id));
  await expectGoods(reviewedGoods);
  assert.deepEqual(await evaluate('Array.from(document.querySelectorAll("#ancestors > li"), node => node.dataset.code)'),
    ['trade-goods', 'lighting', 'tree-lights', 'tree-lights-led-only']);
  assert.match(await text('#atlas-node-status'), /已审商品范围/);

  const excluded = bindingFor(reviewedGoods, id('46532'));
  const excludedRow = bindingSelector('#atlas-bindings', excluded);
  assert.match(await text(excludedRow), /已审 · 排除/);
  await click(excludedRow + ' > details > summary');
  await openOriginal(excludedRow + ' details a[download]', workbook);
  await openOriginal(excludedRow + ' details a:not([download])', 'hs2022-chapter94', { mode: 'pdf', pdfPage: 4 });
  await click(excludedRow + ' > a');
  await expectNode(christmas, excluded.source_clause_id);
  assert.match(await text(bindingSelector('#atlas-backlinks', excluded)), /已审 · 排除/);
  await backToGoods(reviewedGoods, excluded);

  const hsBinding = bindingFor(reviewedGoods, hsId('9405.31'));
  await openHs('#atlas-bindings', '9405.31');
  assert.match(await text(bindingSelector('#atlas-backlinks', hsBinding)), /范围等价/);
  await backToGoods(reviewedGoods, hsBinding);
  assert.match(await text(bindingSelector('#atlas-bindings', bindingFor(reviewedGoods, id('46533')))), /来源范围更宽/);

  const lighting = ['4', '46', '465', '4653'];
  for (const [code, slug, parent, page] of [
    ['9405.11', 'ceiling-wall-led-only', 'ceiling-wall-lights', 3],
    ['9405.21', 'table-floor-led-only', 'table-floor-lights', 4]
  ]) {
    const concept = bySlug.get(slug);
    await searchGoods(code, concept);
    assert.deepEqual(await evaluate('Array.from(document.querySelectorAll("#ancestors > li"), node => node.dataset.code)'),
      ['trade-goods', 'lighting', parent, slug]);
    const cpcBinding = bindingFor(concept, id('46533'));
    const cpcRow = bindingSelector('#atlas-bindings', cpcBinding);
    assert.match(await text(cpcRow), /已审 · 来源范围更宽/);
    await click(cpcRow + ' > details > summary');
    await openOriginal(cpcRow + ' details a:not([download])', 'hs2022-chapter94', { mode: 'pdf', pdfPage: page });
    await click(cpcRow + ' > a');
    await expectNode([...lighting, '46533'], cpcBinding.source_clause_id);
    await backToGoods(concept, cpcBinding);
    await openHs('#atlas-bindings', code);
    assert.match(await text('#hs-official-backlinks'), /46533 · 官方定义引用/);
    await backToGoods(concept, bindingFor(concept, hsId(code)));
  }

  const held = bySlug.get('other-led-scope-review');
  await searchGoods('9405.42', held);
  assert.match(await text('#atlas-node-status'), /待核范围/);
  assert.match(await text('#atlas-bindings'), /限定非 LED 专用[\s\S]*9405\.42 却明确限定 LED 专用/);
  assert.equal(await exists('#atlas-bindings [data-status=reviewed]'), false);
  const heldCpc = bindingFor(held, id('46539'));
  const heldRow = bindingSelector('#atlas-bindings', heldCpc);
  await click(heldRow + ' > details > summary');
  const heldEvidence = heldRow + ' details a';
  await openOriginal(heldEvidence + '[href$=".xlsx"]', workbook);
  await openOriginal(heldEvidence + '[href$=".csv"]', structure);
  await openOriginal(heldEvidence + '[href$="chapter94.pdf#page=4"]', 'hs2022-chapter94', { mode: 'pdf', pdfPage: 4 });
  await openOriginal(heldEvidence + '[href$="20250630.pdf#page=253"]', notes, { mode: 'pdf', pdfPage: 253 });
  await openOriginal(heldEvidence + '[href$="46539-20261109.html#PrintDivID"]',
    'cpc3-detail-46539-20261109', { mode: 'html', elementId: 'PrintDivID' });
  await openOriginal(heldEvidence + '[href$="20261109.html#searchResult"]',
    'cpc3-corrections-register-20261109', { mode: 'html', elementId: 'searchResult' });
  await openHs('#atlas-bindings', '9405.42');
  assert.match(await text('#hs-official-backlinks'), /46539 · 官方定义引用/);
  assert.match(await text('#hs-official-backlinks'), /范围对应待核/);
  await backToGoods(held, bindingFor(held, hsId('9405.42')));
  await click(heldRow + ' > a');
  await expectNode([...lighting, '46539'], heldCpc.source_clause_id);
  assert.match(await text('#official-hs-notes [data-kind=definition] .reference-targets'), /9405\.42/);
  assert.match(await text('#official-hs-notes [data-kind=exclusion] .reference-targets'), /9405\.41/);
  await backToGoods(held, heldCpc);

  const residual = bySlug.get('other-electric-lighting-residual-candidate');
  await searchGoods('9405.49', residual);
  assert.equal(await exists('#atlas-bindings [data-status=reviewed]'), false);
  const residualCpc = bindingFor(residual, id('46539'));
  assert.equal(residualCpc.source_clause_id, null);
  await click(bindingSelector('#atlas-bindings', residualCpc) + ' > a');
  await expectNode([...lighting, '46539']);
  await backToGoods(residual, residualCpc);
  await openHs('#atlas-bindings', '9405.49');
  assert.equal(await exists('#hs-official-backlinks a'), false);
  await backToGoods(residual, bindingFor(residual, hsId('9405.49')));
  assert.equal(goods.lighting_review.correction_search.status, 'no_46539_correction_in_checked_results');
  console.log('Passed: lighting scopes 9405.11/.21, 46539 conflict at .42, and the separate .49 candidate.');

  const frozen = bySlug.get('frozen-octopus-candidate');
  await searchGoods('冷冻章鱼', frozen);
  await openHs('#atlas-bindings', '0307.52');
  assert.equal(await exists('#hs-official-backlinks a'), false);
  assert.match(await text('#hs-candidate-backlinks'), /Atlas 待核候选/);
  await backToGoods(frozen, bindingFor(frozen, hsId('0307.52')));

  const bindingFailures = await evaluate(`(() => {
    const bindings = ${json(Object.values(goods.bindings))};
    const errors = [];
    const check = (selector, item, target) => {
      const row = document.querySelector(selector + ' li[data-binding-id="' + item.id + '"]');
      const hash = row?.querySelector('a')?.hash;
      return row?.dataset.status === item.status && hash && decodeURIComponent(hash.slice(1)) === target;
    };
    for (const item of bindings) {
      const source = item.source_clause_id || item.source_id;
      renderSelection(item.concept_id);
      if (!check('#atlas-bindings', item, source)) errors.push(item.id + ' forward');
      renderSelection(source);
      if (!check('#atlas-backlinks', item, item.concept_id)) errors.push(item.id + ' reverse');
    }
    return errors;
  })()`);
  assert.deepEqual(bindingFailures, []);
  console.log('Passed: Atlas hierarchy, original evidence hashes, source-clause clicks and both directions of all ' +
    Object.keys(goods.bindings).length + ' bindings.');

  const fixture = path.join(temp, 'fixture');
  const copy = file => fs.cpSync(path.join(root, file), path.join(fixture, file), { recursive: true });
  for (const file of ['data/registry', 'data/source-candidates.csv', 'data/resources.lock.json']) copy(file);
  for (const input of baseline.inputs) copy(path.dirname(input.path));
  async function registryState(state, expected) {
    buildRegistry(fixture);
    await navigate(path.join(fixture, registry), '?domain=02-products&fixture=' + state);
    assert.match(await text('#cpc-entry'), expected);
    assert.equal(await exists('#cpc-entry a'), state === 'ready');
  }
  await registryState('not-generated', /浏览页尚未生成/);
  execFileSync('python3', ['-m', 'atlas_sources', '--root', fixture, 'cpc'], { cwd: root });
  for (const file of [view, report, directory]) {
    assert.ok(fs.readFileSync(path.join(fixture, file)).equals(fs.readFileSync(path.join(root, file))), file);
  }
  await registryState('ready', /打开 CPC 3\.0 离线目录/);
  assert.equal(await exists('#atlas-goods-entry'), true);
  fs.appendFileSync(path.join(fixture, view), '<!-- stale test page -->');
  await registryState('stale', /浏览页需要更新/);
  const missing = baseline.inputs.find(input => input.resource_id === notes).path;
  fs.unlinkSync(path.join(fixture, missing));
  await registryState('missing-notes', /资料缺失或校验失败/);
  assert.match(await text('#cpc-entry'), /python3 -m atlas_sources collect/);
  console.log('Passed: 3/3 clean rebuild outputs are byte-identical and catalogue readiness states are correct.');
}

withOfflineBrowser(run).catch(error => { console.error(error); process.exitCode = 1; });
