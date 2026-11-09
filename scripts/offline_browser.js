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

async function offlineSession(temp, browser) {
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
  const pins = JSON.parse(fs.readFileSync(path.join(root, 'data/resources.lock.json')));
  async function original(selector, resource, fragment = '') {
    const url = new URL(await evaluate(select(selector) + '?.href'));
    assert.equal(url.protocol, 'file:');
    assert.equal(url.hash, fragment);
    const bytes = fs.readFileSync(fileURLToPath(url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), pins[resource].sha256, resource);
    return url.href;
  }
  async function expand(group, summary) {
    const index = await evaluate(`Array.from(document.querySelectorAll(${json(group + ' > details')}))
      .findIndex(node => node.firstElementChild.innerText.startsWith(${json(summary)}))`);
    assert.ok(index >= 0, summary);
    const details = group + ' > details:nth-of-type(' + (index + 1) + ')';
    if (!(await exists(details + '[open]'))) await click(details + ' > summary');
    return details + '[open]';
  }
  async function openOriginal(selector, resource, { pdfPage, mode = 'download' } = {}) {
    const url = await original(selector, resource, pdfPage ? '#page=' + pdfPage : '');
    let download;
    if (mode !== 'pdf') {
      const folder = fs.mkdtempSync(path.join(temp, 'download-'));
      await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: folder });
      download = path.join(folder, path.basename(fileURLToPath(url)));
    }
    await click(selector);
    const opened = await until(async () => {
      if (download && fs.existsSync(download)) return { download };
      if (mode === 'download') return undefined;
      const { targetInfos } = await send('Target.getTargets');
      return targetInfos.find(tab => tab.type === 'page' && tab.targetId !== targetId && tab.url === url);
    }, resource + ' original');
    if (opened.download) {
      assert.equal(createHash('sha256').update(fs.readFileSync(download)).digest('hex'), pins[resource].sha256);
      return;
    }
    const originalTab = await send('Target.attachToTarget', { targetId: opened.targetId, flatten: true });
    const expected = mode === 'text' ? '/^(text\\/plain|application\\/json|text\\/csv)$/.test(document.contentType)' :
      'document.contentType === "application/pdf"';
    await until(async () => (await send('Runtime.evaluate', {
      expression: 'document.readyState === "complete" && ' + expected,
      returnByValue: true
    }, originalTab.sessionId)).result.value, resource + ' loaded original');
    await send('Target.closeTarget', { targetId: opened.targetId });
  }
  async function openClaim(group, claim, resource, { excerpt, locator, ...options } = {}) {
    const details = await expand(group, claim + ' · ');
    if (excerpt) assert.ok((await text(details + ' > pre')).includes(excerpt), claim + ' excerpt');
    if (locator) assert.ok((await text(details + ' > .reference')).includes(locator), claim + ' locator');
    await openOriginal(details + ' > .reference a', resource, options);
  }


  return { page, evaluate, text, exists, linksTo, click, navigate, expand, openOriginal, openClaim };
}

async function withOfflineBrowser(check) {
  const temp = fs.mkdtempSync(path.join(tmpdir(), 'atlas-offline-browser-'));
  const browser = connect(path.join(temp, 'chrome'));
  try {
    await check(temp, await offlineSession(temp, browser));
  } finally {
    await browser.close();
    fs.rmSync(temp, { recursive: true, force: true });
  }
}

module.exports = { root, href, until, buildRegistry, withOfflineBrowser };
