// NACE and ISIC cases in the shared offline Chrome session.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const approved = '#approved-bindings';
const pending = '#candidate-bindings';
const reverse = '#approved-backlinks';
const reversePending = '#pending-backlinks';
const finishing = ['urn:atlas:concept:fb06e8aa-e396-55df-9f4e-c91b6562ec73', /新制非矿物家具喷涂、涂漆与抛光/, 'atlas'];
const wood = ['urn:atlas:concept:c6d8be01-7532-53c8-bb0f-05eee3179ce9', /木质新制家用活动家具的表面处理/, 'atlas'];
const metal = ['urn:atlas:concept:3bc38e79-01eb-5935-8ea2-37f56c7f2716', /全金属新制家用活动家具的表面处理/, 'atlas'];
const contractor = ['urn:atlas:concept:2fccaadf-2a4d-5207-ba75-0d70cf4784f4', /新制家用活动家具独立承包涂装/, 'atlas'];
const ceramic = ['urn:atlas:concept:953444c4-dddf-55cc-be13-9ab1fb231965', /^陶瓷家具制造$/, 'atlas'];
const sanitary = ['urn:atlas:concept:03f6de96-1dd0-5f3d-8210-e87fd4eb8ba5', /^陶瓷卫生洁具制造$/, 'atlas'];

async function checkLayout(page, evaluate, width, height, selector, screenshot) {
  const mobile = width <= 800;
  await page('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile });
  const geometry = await evaluate(`(() => {
    const target = document.querySelector(${JSON.stringify(selector)});
    target.scrollIntoView({block:'start'});
    const bounds = node => node.getBoundingClientRect();
    const tree = bounds(document.querySelector('.grid > section'));
    const detail = bounds(document.querySelector('#detail'));
    const region = bounds(target);
    return {
      viewport: innerWidth,
      pageWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      columnLayout: Math.abs(tree.top - detail.top) < 1 && detail.left > tree.right,
      stackLayout: detail.top >= tree.bottom && Math.abs(tree.left - detail.left) < 1,
      regionVisible: region.left >= 0 && region.right <= document.documentElement.clientWidth &&
        region.top < innerHeight && region.bottom > 0
    };
  })()`);
  assert.equal(geometry.viewport, width, 'The browser viewport must not expand to fit the page');
  assert.ok(geometry.pageWidth <= geometry.clientWidth, JSON.stringify(geometry));
  assert.ok(geometry[mobile ? 'stackLayout' : 'columnLayout'], JSON.stringify(geometry));
  assert.ok(geometry.regionVisible, JSON.stringify(geometry));
  const folder = process.env.ATLAS_BROWSER_SCREENSHOTS;
  if (folder) {
    fs.mkdirSync(folder, { recursive: true });
    const { data } = await page('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(folder, screenshot + '-' + width + '.png'), Buffer.from(data, 'base64'));
  }
  console.log(`Passed: ${width}×${height} ${mobile ? 'stacked' : 'two-column'} layout, no horizontal overflow.`);
}

module.exports = async function checkNaceIsic({ page, evaluate, text, exists, click, toNode, expand, openClaim, openOriginal }) {
  function source(group, id) {
    const colon = id.lastIndexOf(':');
    const code = id.slice(colon + 1).replace('.', '\\.');
    return toNode(group, id, new RegExp('^' + code + ' '), id.slice(0, colon));
  }

  async function treeNode(scheme, code) {
    await evaluate(`(() => {
      const scheme = document.querySelector('#scheme');
      scheme.value = ${JSON.stringify(scheme)};
      scheme.dispatchEvent(new Event('change', { bubbles: true }));
      const search = document.querySelector('#search');
      search.value = ${JSON.stringify(code)};
      search.dispatchEvent(new Event('input', { bubbles: true }));
    })()`);
    await source('#tree', scheme + ':' + code);
  }

  const hasLink = (group, id) => exists(group + ' a[href="#' + encodeURIComponent(id) + '"]');
  async function roundTrip(atlasNode, sourceId, isPending = false) {
    await source(isPending ? pending : approved, sourceId);
    await toNode(isPending ? reversePending : reverse, ...atlasNode);
  }

  await treeNode('NACE:Rev.2', '31.09');
  await toNode(reverse, ...finishing);
  assert.match(await text(approved), /ISIC:Rev\.5:310 · broadMatch\s+组级证据/);
  assert.match(await text(pending), /"status": "pending_material_scope_split"/);
  assert.equal(await hasLink(approved, 'ISIC:Rev.5:3101'), false);
  assert.equal(await hasLink(approved, 'ISIC:Rev.5:3102'), false);
  await openClaim(approved, 'FF003', 'nace2-cellar-selected-notes-20261109', {
    mode: 'text', locator: '结果行 76', excerpt: 'finishing of furniture'
  });
  await openClaim(pending, 'F029', 'nace21-nace2-correspondence', {
    locator: 'Sheet0 · 第 555 行', excerpt: 'finishing of furniture'
  });
  await roundTrip(finishing, 'NACE:Rev.2:31.09');
  await source(pending, 'NACE:Rev.2:31.01');
  assert.equal(await hasLink(reverse, finishing[0]), false);
  await toNode(reversePending, ...contractor);
  assert.match(await text(pending), /"status": "publisher_statement_conflicts_with_legacy_definition"/);
  assert.match(await text(pending), /"relation": null/);
  await roundTrip(contractor, 'NACE:Rev.2:31.01', true);
  await roundTrip(contractor, 'NACE:Rev.2:31.09');
  await source(pending, 'NACE:Rev.2:31.01');
  await toNode(reversePending, ...finishing);
  await roundTrip(finishing, 'ISIC:Rev.5:310');
  await roundTrip(finishing, 'NACE:Rev.2.1:31.00');
  await roundTrip(finishing, 'ISIC:Rev.4:3100');
  await checkLayout(page, evaluate, 1440, 1000, '#detail', 'finishing');

  for (const [code, activity, row, materialClaim, materialRow, officialRow] of [
    ['3101', wood, '187', 'FM001', '300', 'FM010'],
    ['3102', metal, '188', 'FM002', '301', 'FM011']
  ]) {
    const sourceId = 'ISIC:Rev.5:' + code;
    await source(approved, 'ISIC:Rev.4:3100');
    const official = await expand('#official-rows', 'ISIC:Rev.4:3100 → ' + sourceId);
    assert.match(await text(official + ' > pre'), /"RC4\.1"/);
    assert.ok((await text(official + ' > .reference')).includes('第 ' + row + ' 行'));
    assert.ok((await text(official)).includes(officialRow));
    await source(official, sourceId);
    assert.equal(await hasLink(reverse, finishing[0]), false);
    await toNode(reverse, ...activity);
    assert.match(await text(approved), /组级工序与材料细类的交集/);
    await openClaim(approved, materialClaim, 'isic5-notes-20260819', { locator: 'ISIC5 · 第 ' + materialRow + ' 行' });
    if (code === '3101') {
      await openClaim(approved, 'FF002', 'isic5-notes-20260819', { locator: 'ISIC5 · 第 299 行' });
      await openClaim(approved, 'FM003', 'nace2-manual-2008', { mode: 'pdf', pdfPage: 194 });
    }
    await source(approved, sourceId);
    await toNode(reversePending, ...finishing);
    await roundTrip(finishing, sourceId, true);
  }
  console.log('Passed: NACE 31.01/31.09 conflict, ISIC group and material scopes, official split rows 187/188.');

  await treeNode('NACE:Rev.2', '23.42');
  assert.ok(await hasLink(reverse, sanitary[0]));
  await toNode(reverse, ...ceramic);
  assert.equal(await exists('#official-gaps'), false);
  assert.match(await text(approved), /依据官方对应表的具体活动分配/);
  const history = await expand('#detail', '历史绑定 · NACE:Rev.2:23.42');
  assert.match(await text(history + ' > pre'), /"status": "approved_bounded_allocation"/);
  await openClaim(approved, 'FF019', 'nace2-nace21-correspondence-20260831', {
    locator: 'Sheet0 · 第 333 行', excerpt: 'manufacture of ceramic furniture'
  });
  await roundTrip(ceramic, 'NACE:Rev.2.1:31.00');
  await openClaim(approved, 'F005', 'nace21-notes-20260930', { locator: 'Sheet0 · 第 409 行' });
  await roundTrip(ceramic, 'ISIC:Rev.4:2393');
  await roundTrip(ceramic, 'ISIC:Rev.5:2393');
  await source(approved, 'NACE:Rev.2:23.42');
  const allocation = await expand('#official-rows', 'NACE:Rev.2:23.42 → NACE:Rev.2.1:31.00');
  await source(allocation, 'NACE:Rev.2.1:31.00');
  const reverseAllocation = await expand('#official-rows', 'NACE:Rev.2:23.42 → NACE:Rev.2.1:31.00');
  await source(reverseAllocation, 'NACE:Rev.2:23.42');
  await toNode(reverse, ...sanitary);
  await roundTrip(sanitary, 'NACE:Rev.2:23.42');
  await roundTrip(sanitary, 'NACE:Rev.2.1:23.42');
  await roundTrip(sanitary, 'ISIC:Rev.4:2392');
  await roundTrip(sanitary, 'ISIC:Rev.5:2393');
  await openClaim(approved, 'FM020', 'isic4-database', { locator: 'tblTitles_English_ISICRev4 · 代码 2392' });
  await openClaim(approved, 'FM021', 'isic5-notes-20260819', { locator: 'ISIC5 · 第 199 行' });
  await openClaim(approved, 'FM022', 'nace2-manual-2008', { mode: 'pdf', pdfPage: 153 });
  await openClaim(approved, 'FM023', 'nace21-notes-20260930', { locator: 'Sheet0 · 第 255 行' });
  console.log('Passed: separate ceramic furniture and sanitary fixtures, four-edition reverse lookup and allocation history.');

  const gaps = [
    ['sanitary-isic-revision', 'ISIC:Rev.4:2392', 'ISIC:Rev.5:2393', 605, 'isic4-isic5-correspondence', 'download', ['第 123 行', '第 124 行']],
    ['sanitary-unsd-legacy', 'ISIC:Rev.4:2392', 'NACE:Rev.2:23.42', 996, 'isic4-nace2-correspondence', 'text', ['第 249 行', '第 250 行', '第 253 行']],
    ['sanitary-eurostat-legacy', 'NACE:Rev.2:23.42', 'ISIC:Rev.4:2392', 996, 'nace-cellar-nace2-isic4-xkos-20261109', 'text', ['结果行 498、499、500', '结果行 501、502、503', '结果行 513、514、515']]
  ];
  assert.equal(await evaluate('document.querySelectorAll("#official-gaps > details").length'), gaps.length);
  for (const [id, from, to, count, resource, mode, locators] of gaps) {
    const card = '#official-gaps > [data-gap="' + id + '"]';
    await click(card + ' > summary');
    assert.ok((await text(card + ' > summary')).includes(from + ' → ' + to));
    assert.match(await text(card), new RegExp('核查 ' + count + ' 条发布记录'));
    assert.match(await text(card), /Atlas 研究关系 · relatedMatch/);
    const adjacent = await expand(card, '相邻官方记录与定位');
    const adjacentText = await text(adjacent);
    for (const locator of locators) assert.ok(adjacentText.includes(locator), locator);
    const record = await expand(card, '完整核查记录');
    assert.match(await text(record + ' > pre'), /"official_mapping_id": null/);
    await openOriginal(card + ' > .reference a', resource, { mode });
    if (id === 'sanitary-isic-revision') {
      await openClaim(card, 'FM024', 'isic5-notes-20240311', { mode: 'pdf', pdfPage: 71 });
      await openClaim(card, 'FM025', 'isic5-notes-20240311', { mode: 'pdf', pdfPage: 72, excerpt: 'see 2392' });
      await openClaim(card, 'FM028', 'isic5-notes-20260819', { locator: 'Notes · 第 26 行', excerpt: 'Deletion' });
    } else {
      assert.match(await text(record + ' > pre'), id === 'sanitary-unsd-legacy' ? /"ISIC4part": "1"/ : /"relation": "closeMatch"/);
    }
    await source(card, from);
    const endpointCard = '#official-gaps > [data-gap="' + id + '"]';
    await click(endpointCard + ' > summary');
    await source(endpointCard, to);
    await toNode(reverse, ...sanitary);
  }
  console.log('Passed: three bounded official gaps, adjacent rows, original tables, 2024 notes and 2026 correction evidence.');

  const card = '#official-gaps > [data-gap="sanitary-isic-revision"]';
  await click(card + ' > summary');
  await checkLayout(page, evaluate, 390, 844, '#official-gaps', 'sanitary');
  await expand(card, '完整核查记录');
  await checkLayout(page, evaluate, 320, 760, card, 'sanitary');
  await source(card, 'ISIC:Rev.4:2392');
  assert.equal(await evaluate('document.activeElement.id'), 'detail');
  assert.ok(await evaluate(`(() => {
    const title = document.querySelector('#detail > h2').getBoundingClientRect();
    return title.top >= 0 && title.bottom <= innerHeight;
  })()`), 'Narrow layout shows the newly selected node title');
  await page('Emulation.clearDeviceMetricsOverride');
};
