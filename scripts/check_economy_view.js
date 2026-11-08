// Offline DOM simulation of generated HTML. This is not browser visual verification.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || 'data/local/economy/isic/index.html', 'utf8');
const payload = html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
class Element {
  constructor(tag) { this.tag = tag; this.textContent = ''; this.children = []; this.value = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
}
const elements = new Map(['data', 'edition', 'q', 'stats', 'detail', 'results', 'count'].map(id => [id, new Element(id)]));
elements.get('data').textContent = payload;
elements.get('edition').value = 'Atlas';
const context = { document: { getElementById: id => elements.get(id), createElement: tag => new Element(tag) } };
vm.runInNewContext(code, context);
const text = node => [node.textContent, ...node.children.map(text)].join(' ');
const data = JSON.parse(payload);
assert.ok(elements.get('results').children.length > 0, 'Atlas tree renders');
const activity = data.review.directory.find(n => n.kind === 'reviewed_activity' && n.anchor_source_id.endsWith(':2619'));
context.select(activity.id);
assert.match(text(elements.get('detail')), /Atlas → 来源/);
assert.match(text(elements.get('detail')), /broadMatch/);
elements.get('q').value = '2619'; context.browse();
assert.ok(text(elements.get('results')).includes('2619'), 'directory scope search');
elements.get('edition').value = 'Rev.4'; elements.get('q').value = ''; context.browse();
assert.ok(text(elements.get('count')).includes('766'), 'original Rev.4 tree retained');
context.select('ISIC:Rev.4:8522');
assert.match(text(elements.get('detail')), /CROSSWALK-QUESTION/);
assert.match(text(elements.get('detail')), /held_after_review/);
context.select('ISIC:Rev.5:5221');
assert.match(text(elements.get('detail')), /TEXT-2026-5221/);
assert.match(text(elements.get('detail')), /different_word_sequence/);
const buttons = node => (node.tag === 'button' ? [node] : []).concat(...node.children.map(buttons));
const parent = buttons(elements.get('detail')).find(b => b.textContent.startsWith('522 '));
assert.ok(parent, 'original parent link'); parent.onclick();
assert.match(text(elements.get('detail')), /Rev.5 · 522 /);
console.log('Passed: offline DOM smoke (Atlas tree, partial direction, search, original tree, holds, errata conflict, parent navigation). Visual layout not tested.');
