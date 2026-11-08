// Offline DOM simulation; not a visual browser acceptance test.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[2] || 'data/local/economy/furniture/index.html','utf8');
const payload = html.match(/<script type="application\/json" id="data">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.style={};this.value='';}
  appendChild(child){this.children.push(child);return child;}
  replaceChildren(...children){this.children=[...children];}
}
const elements=new Map(['data','scheme','search','tree','detail','stats','issues'].map(k=>[k,new Element(k)]));
elements.get('data').textContent=payload;elements.get('scheme').value='atlas';
const context={document:{getElementById:id=>elements.get(id),createElement:tag=>new Element(tag)}};
vm.runInNewContext(code,context);
const text=n=>[n.textContent,...n.children.map(text)].join(' ');
const view=context.furnitureView;
assert.equal(elements.get('tree').children.length,11,'complete own branch tree');
const ceramic=view.data.directory.concepts.find(n=>n.key==='ceramic');
view.show(ceramic);
assert.match(text(elements.get('detail')),/NACE:Rev.2.1:31.00/);
assert.match(text(elements.get('detail')),/ISIC:Rev.4:2393/);
assert.match(text(elements.get('detail')),/ISIC:Rev.5:2393/);
assert.match(text(elements.get('detail')),/待审来源.*NACE:Rev.2:23.42/);
assert.match(text(elements.get('detail')),/field_sha256/);
view.show(view.data.sources.find(n=>n.id==='NACE:Rev.2.1:31.00'));
assert.match(text(elements.get('detail')),/官方行及独立审查/);
assert.match(text(elements.get('detail')),/Atlas 活动范围研究对应（非官方表）/);
assert.match(text(elements.get('detail')),/木制厨房家具制造/);
elements.get('scheme').value='NACE:Rev.2';elements.get('search').value='31.09';view.render();
assert.match(text(elements.get('tree')),/31.09/);
assert.match(text(elements.get('tree')),/31.0/);
assert.match(text(elements.get('tree')),/Manufacturing/);
assert.match(text(elements.get('issues')),/FURN-FINISHING/);
assert.match(text(elements.get('issues')),/FURN-DIRECT-CROSSWALK/);
console.log('Passed: furniture source trees, stable own IDs, directional bindings, evidence hashes, candidate separation, official/research distinction and conflicts. Visual layout not tested.');
