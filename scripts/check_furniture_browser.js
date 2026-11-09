// Acceptance test against a real Chromium browser and the generated file:// pages.
const assert = require('node:assert/strict');
const { spawn, execFileSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');
const { fileURLToPath, pathToFileURL } = require('node:url');

const root = path.resolve(__dirname, '..');
const chrome = process.env.ATLAS_CHROME ||
  (process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : 'chromium');
const registry = 'data/reports/registry.html';
const old = 'FR_NAF:Rev.2:31.01Z';
const current = 'FR_NAF:2025:31.00G';
const whole = 'urn:atlas:concept:df67a84e-39ed-547f-b0f1-8d1dfbf6233e';
const part = 'urn:atlas:concept:a62f38d1-7dd9-52ae-b515-2d39384f83ac';
const json = JSON.stringify;
const href = id => '[href="#' + encodeURIComponent(id) + '"]';

function connect(profile) {
  const browser = spawn(chrome, [
    '--headless', '--remote-debugging-pipe', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--proxy-server=http://127.0.0.1:9',
    '--window-size=1440,1000', '--user-data-dir=' + profile, 'about:blank'
  ], { stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'] });
  const requests = new Map();
  let lastId = 0;
  let buffer = '';
  let stderr = '';
  let closed = false;
  browser.stderr.on('data', chunk => { stderr = (stderr + chunk).slice(-4000); });
  const done = new Promise(resolve => {
    function stop(error) {
      if (closed) return;
      closed = true;
      for (const request of requests.values()) request.reject(error);
      resolve();
    }
    browser.on('error', stop);
    browser.on('close', (code, signal) => stop(new Error('Chrome exited (' + (signal || code) + ')\n' + stderr)));
    browser.stdio[3].on('error', stop);
  });
  browser.stdio[4].setEncoding('utf8');
  browser.stdio[4].on('data', chunk => {
    const messages = (buffer + chunk).split('\0');
    buffer = messages.pop();
    for (const message of messages) {
      const { id, result, error } = JSON.parse(message);
      const request = requests.get(id);
      if (!request) continue;
      if (error) request.reject(new Error(error.message));
      else request.resolve(result);
    }
  });

  function send(method, params = {}, sessionId) {
    if (closed) return Promise.reject(new Error('Chrome is closed'));
    const id = ++lastId;
    let timer;
    return new Promise((resolve, reject) => {
      timer = setTimeout(() => reject(new Error('Chrome timed out at ' + method + '\n' + stderr)), 10000);
      requests.set(id, { resolve, reject });
      browser.stdio[3].write(json({ id, method, params, sessionId }) + '\0');
    }).finally(() => {
      clearTimeout(timer);
      requests.delete(id);
    });
  }

  async function close() {
    if (!closed) browser.kill();
    await done;
  }
  return { send, close };
}

async function until(read, label) {
  for (let attempt = 0; attempt < 100; attempt++) {
    const value = await read();
    if (value) return value;
    await delay(50);
  }
  throw new Error('Browser did not reach ' + label);
}

function buildRegistry(fixture) {
  execFileSync('python3', ['-m', 'atlas_sources', '--root', fixture, 'report'], { cwd: root });
}

async function run(temp, browser) {
  const { send } = browser;
  const version = await send('Browser.getVersion');
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const page = (method, params) => send(method, params, sessionId);
  await page('Network.enable');
  await page('Network.emulateNetworkConditions', {
    offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0
  });
  await page('Network.setBlockedURLs', { urls: ['http://*', 'https://*'] });
  console.log(version.product + ' · headless · offline file://');

  async function evaluate(expression) {
    const { result, exceptionDetails } = await page('Runtime.evaluate', { expression, returnByValue: true });
    if (exceptionDetails) throw new Error(result.description || exceptionDetails.text);
    return result.value;
  }
  const select = selector => 'document.querySelector(' + json(selector) + ')';
  const text = selector => evaluate(select(selector) + '?.innerText');
  const linksTo = (group, id) => group + ' a' + href(id);
  const exists = selector => evaluate('Boolean(' + select(selector) + ')');
  async function click(selector) {
    const point = await evaluate(`(() => {
      const node = ${select(selector)};
      if (!node || !node.getClientRects().length) return null;
      node.scrollIntoView({ block: 'center' });
      const { x, y, width, height } = node.getClientRects()[0];
      return { x: x + width / 2, y: y + height / 2 };
    })()`);
    assert.ok(point, 'Visible click target: ' + selector);
    for (const type of ['mousePressed', 'mouseReleased']) {
      await page('Input.dispatchMouseEvent', { ...point, type, button: 'left', clickCount: 1 });
    }
  }
  async function navigate(file, query = '') {
    const url = pathToFileURL(file).href + query;
    const result = await page('Page.navigate', { url });
    assert.equal(result.errorText, undefined);
    await until(() => evaluate('location.href === ' + json(url) + ' && document.readyState === "complete"'), url);
    assert.equal(await evaluate('navigator.onLine'), false);
  }
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

  const pins = JSON.parse(fs.readFileSync(path.join(root, 'data/resources.lock.json')));
  async function original(selector, resource, fragment = '') {
    const url = new URL(await evaluate(select(selector) + '?.href'));
    assert.equal(url.protocol, 'file:');
    assert.equal(url.hash, fragment);
    const bytes = fs.readFileSync(fileURLToPath(url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), pins[resource].sha256, resource);
    return url.href;
  }
  async function openPdf(claim, resource, physicalPage, excerpt) {
    const index = await evaluate(`Array.from(document.querySelectorAll('#approved-bindings > details'))
      .findIndex(node => node.firstElementChild.innerText.startsWith(${json(claim + ' · ')}))`);
    assert.ok(index >= 0, claim);
    const details = '#approved-bindings > details:nth-of-type(' + (index + 1) + ')';
    await click(details + ' > summary');
    if (excerpt) assert.ok((await text(details + '[open] > pre')).includes(excerpt));
    const link = details + '[open] > .reference a';
    const url = await original(link, resource, '#page=' + physicalPage);
    await click(link);
    let targets;
    const target = await until(async () => {
      targets = (await send('Target.getTargets')).targetInfos;
      return targets.find(target => target.type === 'page' && target.targetId !== targetId && target.url === url);
    }, resource + ' PDF tab').catch(error => {
      throw new Error(error.message + '\nExpected ' + url + '\nOpened ' + targets.map(target => target.url).join('\n'));
    });
    const pdf = await send('Target.attachToTarget', { targetId: target.targetId, flatten: true });
    await until(async () => (await send('Runtime.evaluate', {
      expression: 'document.contentType === "application/pdf" && document.readyState === "complete"',
      returnByValue: true
    }, pdf.sessionId)).result.value, resource + ' loaded PDF');
    await send('Target.closeTarget', { targetId: target.targetId });
  }

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
  await openPdf('FN001', 'naf-rev2-cpf21-notes-2020', 422);
  await toNode('#approved-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  await toNode('#pending-backlinks', part, partTitle, 'atlas');
  assert.match(await text('#candidate-bindings'), /FR_NAF:Rev\.2:31\.01Z · 未批准关系/);
  assert.match(await text('#candidate-bindings'), /"relation": null/);
  assert.match(await text('#candidate-bindings'), /"status": "pending_specialist_scope"/);
  assert.match(await text('#approved-bindings'), /FR_NAF:2025:31\.00G · broadMatch/);
  assert.equal(await exists(linksTo('#approved-bindings', old)), false);
  await openPdf('FN003', 'naf-2025-notes-2025', 160, 'la fabrication de composants intégrés pour meubles de magasin');
  await toNode('#candidate-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  await evaluate('history.back()');
  await expectNode(part, partTitle, 'atlas');
  await toNode('#approved-bindings', current, /^31\.00G /, 'FR_NAF:2025');
  await toNode('#approved-backlinks', part, partTitle, 'atlas');
  await toNode('#approved-bindings', current, /^31\.00G /, 'FR_NAF:2025');
  await toNode('#approved-backlinks', whole, wholeTitle, 'atlas');
  await toNode('#approved-bindings', old, /^31\.01Z /, 'FR_NAF:Rev.2');
  console.log('Passed: both directions of reviewed and pending bindings, stable history, PDF pages 422 and 160.');

  const downloads = path.join(temp, 'downloads');
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads });
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
    const link = opened + ' > .reference a';
    const originalUrl = await original(link, resource);
    await click(link);
    const downloaded = path.join(downloads, path.basename(fileURLToPath(originalUrl)));
    await until(() => fs.existsSync(downloaded), resource + ' workbook download');
    assert.equal(createHash('sha256').update(fs.readFileSync(downloaded)).digest('hex'), pins[resource].sha256);
    await toNode(opened, to, title, scheme);
  }
  await click('nav[aria-label="经济活动导航"] a');
  await until(() => evaluate('document.querySelector("#domain")?.value === "01-economy"'), 'registry return');
  console.log('Passed: official rows 383 and 382, both workbook downloads match their pins, registry return.');

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

async function main() {
  const temp = fs.mkdtempSync(path.join(tmpdir(), 'atlas-furniture-browser-'));
  const browser = connect(path.join(temp, 'chrome'));
  try {
    await run(temp, browser);
  } finally {
    await browser.close();
    fs.rmSync(temp, { recursive: true, force: true });
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
