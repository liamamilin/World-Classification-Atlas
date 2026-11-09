// ISIC acceptance cases against the generated pages in a real offline Chromium browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { root, href, until, buildRegistry, withOfflineBrowser } = require('./offline_browser');

const registry = 'data/reports/registry.html';
const notes = 'isic5-notes-20260819';
const crosswalk = 'isic4-isic5-correspondence';
const cpc = 'cpc21-notes-20250403';
const ice = 'urn:atlas:concept:a069b429-1983-589d-be3b-0607e6e841b4';
const masks = [
  ['urn:atlas:concept:63e2abf5-ffc0-50a7-b5d0-82e8a44c661f', /外科口罩/, 'B027'],
  ['urn:atlas:concept:f9c09487-c6cc-58b0-a12d-13f4c1cf55b8', /FFP2防护口罩/, 'B028'],
  ['urn:atlas:concept:88f1570f-432e-56c4-af43-6cf164312fae', /FFP3防护口罩/, 'B029']
];
const carbon = 'urn:atlas:concept:89e4f6ba-eb22-5cb4-9615-639db3d7c890';
const fibre = 'urn:atlas:concept:0beae3f5-0067-5771-89c0-f828769d0486';
const plantMilk = 'urn:atlas:concept:ab79f5d2-6f27-5e11-8538-18d9efe87fa5';
const cheese = 'urn:atlas:concept:ad59199d-85b4-55d6-91d1-cbe6b1e29246';
const coffee = 'urn:atlas:concept:88f8a64c-6e56-5ceb-9079-e900ff47b8a4';
const foodIce = 'urn:atlas:concept:4ea445f2-8b44-53e7-b979-677a4fe83f22';
const coolingIce = 'urn:atlas:concept:d65a2f04-9a43-5ffc-8771-1e13991b0340';
const enrichment = 'urn:atlas:concept:74680745-b0dc-55d2-9482-ae708be8eaf3';
const fuel = 'urn:atlas:concept:4403c5fa-343d-5807-aef2-00df829c16ca';
const uranium = 'urn:atlas:concept:7815f6bc-fc2e-5cce-8f71-f10dadf6f0e2';
const bioethanol = 'urn:atlas:concept:a4c619fd-571c-5408-b764-a2a527b29c40';
const adhesives = 'urn:atlas:concept:e066ca01-a777-5205-817b-19f215976f80';
const approved = '#approved-sources';
const reverse = '#approved-backlinks';
const pending = '#candidate-sources';
const reversePending = '#candidate-backlinks';
const json = JSON.stringify;
const rowTo = (group, id) => group + ' > article:has(> a' + href(id) + ')';
const officialTo = id => rowTo('#official-rows', id);
const supplementTo = id => rowTo('#supplemental-rows', id);
const rev4 = code => 'ISIC:Rev.4:' + code;
const rev5 = code => 'ISIC:Rev.5:' + code;

async function run(temp, { evaluate, text, exists, linksTo, click, navigate, expand, openOriginal, openClaim }) {
  async function expectNode(id, title) {
    await until(() => evaluate('document.querySelector("#detail > small")?.innerText === ' + json(id)), id);
    const edition = id.startsWith('ISIC:') ? id.split(':')[1] : 'Atlas';
    assert.equal(await evaluate('document.querySelector("#edition").value'), edition);
    assert.equal(await evaluate('decodeURIComponent(location.hash.slice(1))'), id);
    if (title) assert.match(await text('#detail > h2'), title);
  }
  async function toNode(group, id, title) {
    await click(linksTo(group, id));
    await expectNode(id, title);
  }
  async function treeNode(edition, code) {
    await evaluate(`(() => {
      const edition = document.querySelector('#edition');
      edition.value = ${json(edition)};
      edition.dispatchEvent(new Event('change', { bubbles: true }));
      const search = document.querySelector('#q');
      search.value = ${json(code)};
      search.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    await toNode('#results', 'ISIC:' + edition + ':' + code);
  }
  async function erratum(row, expected) {
    await click('#errata > summary');
    assert.match(await text('#errata > h4:first-of-type'), /2024 原说明/);
    assert.match(await text('#errata > h4:last-of-type'), /2026 更新说明/);
    assert.match(await text('#errata'), expected);
    assert.ok((await text('#errata > .reference')).includes('Notes · 第 ' + row + ' 行'));
    await openOriginal('#errata > .reference .source-file', notes);
  }
  async function roundTrip(id, source, group = approved, back = reverse) {
    await toNode(group, source);
    await toNode(back, id);
  }
  async function heldPair(old, current) {
    const older = supplementTo(old);
    assert.equal(await exists(officialTo(old)), false);
    assert.match(await text(older), /atlas_research_supplement · held_after_research · 未批准关系/);
    await toNode(older, old);
    const newer = supplementTo(current);
    assert.equal(await exists(officialTo(current)), false);
    assert.match(await text(newer), /held_after_research · 未批准关系/);
    await toNode(newer, current);
  }
  async function approvedSupplement(old, current, activity, issue) {
    for (const peer of [current, old]) {
      const row = supplementTo(peer);
      assert.equal(await exists(officialTo(peer)), false);
      assert.match(await text(row), /atlas_research_supplement · accepted_scoped_overlap · relatedMatch/);
      assert.ok(await exists(linksTo(row, activity)), activity);
      assert.ok((await text('#detail')).includes(issue + ' · addressed_in_research'));
      await toNode(row, peer);
    }
  }
  async function officialPair(old, current, { number, topology, scope, gsim, activity, excluded, download }) {
    for (const peer of [current, old]) {
      const row = officialTo(peer);
      const content = await text(row);
      assert.ok(content.includes(gsim + ' · ' + topology), row);
      assert.ok(content.includes(scope), row);
      assert.match(content, /审查 · reviewed_current_relation · Rev\.4 → Rev\.5 relatedMatch/);
      assert.ok((await text(row + ' > .reference')).includes('第 ' + number + ' 行'), row);
      assert.ok(await exists(linksTo(row, activity)), activity);
      if (excluded) assert.equal(await exists(linksTo(row, excluded)), false);
      if (download && peer === current) await openOriginal(row + ' > .reference .source-file', crosswalk);
      await toNode(row, peer);
    }
  }
  async function errataPdf(claim, resource, pdfPage, excerpt) {
    const pdfs = await expand('#detail > #errata', '手册与勘误 PDF 旁证');
    await openClaim(pdfs, claim, resource, { mode: 'pdf', pdfPage, excerpt });
  }

  await navigate(path.join(root, registry));
  await evaluate(`(() => {
    const domain = document.querySelector('#domain');
    domain.value = '01-economy';
    domain.dispatchEvent(new Event('input', { bubbles: true }));
  })()`);
  await click('#isic-entry a');
  await until(() => exists('#results details'), 'ISIC catalogue from registry');
  assert.equal(await evaluate('navigator.onLine'), false);

  await click('aside > details > summary');
  await toNode('#proposals', ice, /无调味直接食用水冰制造/);
  assert.match(await text('#detail'), /held_after_research/);
  assert.match(await text('#detail'), /没有已批准的来源绑定/);
  assert.equal(await exists(linksTo('#results', ice)), false);
  await openClaim('#detail', 'B001', cpc, { locator: 'CPC2.1 · 第 512 行' });
  await openClaim('#detail', 'B003', cpc, { locator: 'CPC2.1 · 第 765 行' });
  await openClaim('#detail', 'B008', 'cpc21-manual-2015', { mode: 'pdf', pdfPage: 56 });
  await toNode('#proposal-parents', 'ISIC:Rev.5:3530');
  await erratum(35, /partially_reviewed_water_ice_pending/);
  assert.equal(await exists(linksTo(reverse, ice)), false);
  await toNode('#proposal-backlinks', ice);
  await toNode('#proposal-parents', 'ISIC:Rev.5:1050');
  await erratum(14, /sorbet/i);
  await toNode('#proposal-backlinks', ice);
  await toNode('#proposal-parents', 'ISIC:Rev.5:1050');
  await heldPair('ISIC:Rev.4:3530', 'ISIC:Rev.5:1050');
  await toNode(supplementTo('ISIC:Rev.4:3530'), 'ISIC:Rev.4:3530');
  assert.match(await text('#detail > pre'), /ice for food and non-food/i);
  const sameIce = officialTo('ISIC:Rev.5:3530');
  assert.match(await text(sameIce), /原范围 whole \/ 新范围 whole/);
  assert.match(await text(sameIce), /relatedMatch/);
  await toNode(sameIce, 'ISIC:Rev.5:3530');
  const iceOfficial = officialTo('ISIC:Rev.4:3530');
  assert.match(await text(iceOfficial + ' > .reference'), /第 209 行/);
  await openOriginal(iceOfficial + ' > .reference .source-file', crosswalk);
  await toNode(iceOfficial, 'ISIC:Rev.4:3530');
  console.log('Passed: water-ice proposal and both candidate parents, 1050/3530 errata, separate held supplement and official row 209.');

  await treeNode('Rev.5', '3250');
  const currentMasks = 'ISIC:Rev.5:3250';
  for (const [id, title, claim] of masks) {
    await toNode(reverse, id, title);
    assert.match(await text('#detail'), /仅Rev.5当前范围已审/);
    assert.match(await text(approved), /ISIC:Rev\.5:3250 · broadMatch/);
    await openClaim(approved, claim, notes, { locator: 'ISIC5 · 第 313 行' });
    for (const older of ['ISIC:Rev.4:1392', 'ISIC:Rev.4:3250']) {
      assert.equal(await exists(linksTo(approved, older)), false);
      await toNode(pending, older);
      assert.equal(await exists(linksTo(reverse, id)), false);
      assert.match(await text(reversePending), /unresolved_scope_hypothesis · 未批准关系/);
      await toNode(reversePending, id, title);
    }
    await toNode(approved, currentMasks);
  }
  await heldPair('ISIC:Rev.4:1399', currentMasks);
  await toNode(supplementTo('ISIC:Rev.4:1399'), 'ISIC:Rev.4:1399');
  await openClaim(supplementTo(currentMasks), 'B006', cpc, {
    locator: 'CPC2.1 · 第 2529 行', excerpt: 'neither mechanical parts nor replaceable filters'
  });
  await toNode(officialTo('ISIC:Rev.5:1399'), 'ISIC:Rev.5:1399');
  await erratum(20, /partially_reviewed_masks_pending/);
  assert.match(await text('#errata'), /protective masks/i);
  console.log('Passed: three current-only masks, six two-way pending legacy bindings, 1399 erratum and held 1399→3250 supplement.');

  await treeNode('Rev.4', '1312');
  await toNode(reverse, carbon, /非电气用途碳纤维织物织造/);
  await openClaim(approved, 'C024', 'isic4-database', { locator: '代码 1312', excerpt: 'carbon and aramid threads' });
  await openClaim(approved, 'C023', notes, { locator: 'ISIC5 · 第 127 行', excerpt: 'see 2399' });
  await roundTrip(carbon, 'ISIC:Rev.4:1312');
  await roundTrip(carbon, 'ISIC:Rev.5:2399');
  await toNode(pending, 'ISIC:Rev.4:2399');
  assert.equal(await exists(linksTo(reverse, carbon)), false);
  assert.ok(await exists(linksTo(reverse, fibre)));
  assert.match(await text(reversePending), /unresolved_competing_source · 未批准关系/);
  await toNode(reversePending, carbon);
  const competing = rowTo(pending, 'ISIC:Rev.4:2399');
  await openClaim(competing, 'B012', 'cpc21-manual-2015', { mode: 'pdf', pdfPage: 87 });
  await toNode(approved, 'ISIC:Rev.4:1312');
  const newerCarbon = 'ISIC:Rev.5:2399';
  assert.equal(await exists(officialTo(newerCarbon)), false);
  assert.match(await text(supplementTo(newerCarbon)), /accepted_scoped_overlap · relatedMatch/);
  await toNode(supplementTo(newerCarbon), newerCarbon);
  await toNode(supplementTo('ISIC:Rev.4:1312'), 'ISIC:Rev.4:1312');
  await toNode(officialTo('ISIC:Rev.5:1312'), 'ISIC:Rev.5:1312');
  await erratum(17, /Removed "or glass"/i);
  await evaluate('history.back()');
  await expectNode('ISIC:Rev.4:1312');
  console.log('Passed: bounded carbon-weaving overlap, separate competing old 2399, 1312 erratum and browser history.');

  await treeNode('Rev.4', '1079');
  await toNode(reverse, plantMilk, /植物奶饮料制造/);
  await openClaim(approved, 'C001', 'isic4-database', { locator: '代码 1079', excerpt: 'non-dairy milk' });
  await openClaim(approved, 'C002', notes, { locator: 'ISIC5 · 第 120 行', excerpt: 'oat milk' });
  await openClaim(approved, 'C048', notes, { locator: 'ISIC5 · 第 100 行', excerpt: 'see 1105' });
  await roundTrip(plantMilk, rev4('1079'));
  await roundTrip(plantMilk, rev5('1105'));
  await toNode(approved, rev4('1079'));
  await approvedSupplement(rev4('1079'), rev5('1105'), plantMilk, 'ALLOCATION-PLANT-MILK');
  await toNode(supplementTo(rev5('1105')), rev5('1105'));
  assert.match(await text('#detail'), /TEXT-2026-1105 · resolved_for_research/);
  assert.match(await text('#detail'), /发布者解决状态 · not_obtained/);
  await erratum(16, /different_word_sequence/);
  await errataPdf('C087', 'isic5-white-cover-2026', 109, 'soya-based beverages');
  await toNode(supplementTo(rev4('1079')), rev4('1079'));
  await officialPair(rev4('1079'), rev5('1076'), {
    number: 72, topology: 'one_to_many', scope: '原范围 partial / 新范围 whole',
    gsim: 'RC4.2 - Split off', activity: coffee, excluded: plantMilk, download: true
  });
  await officialPair(rev4('1079'), rev5('1079'), {
    number: 73, topology: 'one_to_many', scope: '原范围 partial / 新范围 whole',
    gsim: 'RC4.2 - Split off', activity: cheese, excluded: plantMilk
  });
  await toNode(officialTo(rev5('1079')), rev5('1079'));
  await erratum(15, /bounded_allocations_reviewed_official_gap_open/);
  await openClaim('#errata', 'C056', notes, { excerpt: 'non-dairy milk and cheese substitutes' });
  await openClaim('#errata', 'C057', notes, { excerpt: 'manufacture of cheese substitutes' });
  console.log('Passed: plant-milk evidence and text difference, separate supplement, both official 1079 split rows.');

  await treeNode('Rev.4', '1050');
  await toNode(reverse, foodIce, /冰淇淋及雪葩制造/);
  await openClaim(approved, 'C009', 'isic4-database', { locator: '代码 1050', excerpt: 'ice cream' });
  await openClaim(approved, 'C010', notes, { locator: 'ISIC5 · 第 100 行', excerpt: 'sorbet' });
  await roundTrip(foodIce, rev4('1050'));
  await roundTrip(foodIce, rev5('1050'));
  await toNode(approved, rev4('1050'));
  await officialPair(rev4('1050'), rev5('1050'), {
    number: 64, topology: 'one_to_one', scope: '原范围 whole / 新范围 whole',
    gsim: 'GSIM 空白', activity: foodIce, excluded: ice, download: true
  });
  await toNode(officialTo(rev5('1050')), rev5('1050'));
  assert.equal(await exists(linksTo(reverse, ice)), false);
  assert.ok(await exists(linksTo('#proposal-backlinks', ice)));
  await erratum(14, /consolidate ice cream and related edible ices/i);
  await openClaim('#errata', 'C054', notes, { excerpt: 'see 1105' });
  await errataPdf('C086', 'isic5-white-cover-2026', 103, 'see 1105');
  await treeNode('Rev.4', '3530');
  await toNode(reverse, coolingIce, /冷却用途水冰生产/);
  await roundTrip(coolingIce, rev4('3530'));
  await roundTrip(coolingIce, rev5('3530'));
  await toNode(approved, rev5('3530'));
  assert.equal(await exists(linksTo(reverse, foodIce)), false);
  await erratum(35, /partially_reviewed_water_ice_pending/);
  for (const version of ['first', 'last']) {
    assert.match(await text('#errata > pre:' + version + '-of-type'), /manufacturing of edible ice, see 1050/);
  }
  await openClaim('#errata', 'C063', notes, { excerpt: 'for cooling purposes' });
  await errataPdf('C090', 'isic5-white-cover-2026', 178, 'see 1050');
  console.log('Passed: food ice and cooling ice in separate reviewed activities, Notes 14/35 and held water-ice proposal.');

  for (const [id, title, old, current, oldClaim, currentClaim, row] of [
    [enrichment, /铀钍矿富集/, '2011', '2011', 'C031', 'C032', 174],
    [fuel, /核反应堆燃料元件制造/, '2011', '2420', 'C033', 'C034', 208],
    [uranium, /天然铀金属冶炼精炼/, '2420', '2420', 'C035', 'C036', 208]
  ]) {
    await treeNode('Rev.4', old);
    await toNode(reverse, id, title);
    await openClaim(approved, oldClaim, 'isic4-database', { locator: '代码 ' + old });
    await openClaim(approved, currentClaim, notes, { locator: 'ISIC5 · 第 ' + row + ' 行' });
    await roundTrip(id, rev4(old));
    await roundTrip(id, rev5(current));
  }
  await treeNode('Rev.4', '2011');
  await approvedSupplement(rev4('2011'), rev5('2420'), fuel, 'ALLOCATION-NUCLEAR');
  await officialPair(rev4('2011'), rev5('2011'), {
    number: 108, topology: 'one_to_many', scope: '原范围 partial / 新范围 whole',
    gsim: 'RC5 - Transfer', activity: enrichment, excluded: fuel, download: true
  });
  await officialPair(rev4('2011'), rev5('2029'), {
    number: 109, topology: 'many_to_many', scope: '原范围 partial / 新范围 partial',
    gsim: 'RC5 - Transfer', activity: bioethanol, excluded: fuel, download: true
  });
  await toNode(officialTo(rev5('2011')), rev5('2011'));
  await erratum(22, /bounded_allocations_reviewed_official_gap_open/);
  assert.doesNotMatch(await text('#errata > pre:last-of-type'), /production of fuel elements/);
  await openClaim('#errata', 'C080', notes, { excerpt: 'production of fuel elements' });
  await openClaim('#errata', 'C081', notes, { excerpt: 'enrichment of uranium and thorium ores' });
  await errataPdf('C091', 'isic5-errata-2026', 16, 'production of fuel elements');
  await treeNode('Rev.4', '2029');
  await officialPair(rev4('2029'), rev5('2029'), {
    number: 115, topology: 'many_to_one', scope: '原范围 whole / 新范围 partial',
    gsim: 'GSIM 空白', activity: adhesives, excluded: fuel
  });
  await treeNode('Rev.4', '2420');
  await officialPair(rev4('2420'), rev5('2420'), {
    number: 130, topology: 'one_to_one', scope: '原范围 whole / 新范围 whole',
    gsim: 'GSIM 空白', activity: uranium, excluded: fuel
  });
  await toNode(officialTo(rev5('2420')), rev5('2420'));
  await erratum(27, /bounded_allocations_reviewed_official_gap_open/);
  assert.match(await text('#errata > pre:first-of-type'), /processing of nuclear fuel/);
  await openClaim('#errata', 'C084', notes, { excerpt: 'production of fuel elements for nuclear reactors' });
  await errataPdf('C092', 'isic5-errata-2026', 24, 'production of fuel elements');
  await errataPdf('C089', 'isic5-white-cover-2026', 135, 'production of fuel elements');
  console.log('Passed: separate nuclear activities, Notes 22/27 and PDF corroboration, official transfer and partial scopes.');

  await click('nav[aria-label="经济活动导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "01-economy"'), 'registry return');
  console.log('Passed: registry return.');

  const fixture = path.join(temp, 'fixture');
  for (const file of ['data/registry', 'data/source-candidates.csv', 'data/resources.lock.json',
    'data/reports/isic-economy.json']) {
    fs.cpSync(path.join(root, file), path.join(fixture, file), { recursive: true });
  }
  fs.mkdirSync(path.join(fixture, 'data/local'), { recursive: true });
  for (const raw of ['data/raw', 'data/local/raw']) fs.symlinkSync(path.join(root, raw), path.join(fixture, raw), 'dir');
  async function unavailable(state, message) {
    buildRegistry(fixture);
    await navigate(path.join(fixture, registry), '?domain=01-economy&fixture=' + state);
    assert.match(await text('#isic-entry'), message);
    assert.match(await text('#isic-entry'), /python3 -m atlas_sources economy\s+python3 -m atlas_sources report/);
    assert.equal(await exists('#isic-entry a'), false);
  }
  await unavailable('missing-view', /ISIC 浏览页尚未生成/);
  const stale = path.join(fixture, 'data/local/economy/isic/index.html');
  fs.mkdirSync(path.dirname(stale), { recursive: true });
  fs.writeFileSync(stale, 'stale test page');
  await unavailable('stale-view', /ISIC 浏览页需要更新/);
  fs.unlinkSync(path.join(fixture, 'data/local/raw'));
  await unavailable('missing-inputs', /ISIC 资料缺失或校验失败/);
  assert.match(await text('#isic-entry'), /python3 -m atlas_sources collect/);
  console.log('Passed: ISIC recovery hints for missing page, stale page and missing snapshots.');
}

withOfflineBrowser(run).catch(error => { console.error(error); process.exitCode = 1; });
