const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'static', 'index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      value: '', style: {}, classList: { add() {}, remove() {} },
      addEventListener(type, callback) { this[type] = callback; },
      focus() {}, remove() {},
    });
  }
  return elements.get(id);
}
const context = vm.createContext({
  document: {
    getElementById: element, querySelector: element, addEventListener() {},
    documentElement: {},
  },
  navigator: { platform: 'MacIntel', language: 'en' },
  window: {},
  localStorage: { getItem() { return null; }, setItem() {} },
  setInterval, clearInterval,
});
vm.runInContext(script, context);

const oldURL = 'https://www.youtube.com/watch?v=sRPDkY3O6_0';
function setAnalyzedState() {
  element('url').value = oldURL;
  element('cookieBrowser').value = '';
  vm.runInContext(`state.url = ${JSON.stringify(oldURL)}; state.cookie = null; state.selected = {spec: '270+140'}; state.lastData = {title: 'Sample'};`, context);
  element('dlBtn').disabled = false;
}

setAnalyzedState();
element('url').value = 'https://www.youtube.com/watch?v=jNQXAC9IVRw';
element('url').input();
assert.equal(vm.runInContext('state.url', context), null);
assert.equal(vm.runInContext('state.selected', context), null);
assert.equal(element('dlBtn').disabled, true);

setAnalyzedState();
element('cookieBrowser').value = 'chrome';
vm.runInContext('saveCookieChoice()', context);
assert.equal(vm.runInContext('state.url', context), null);
assert.equal(vm.runInContext('state.selected', context), null);
assert.equal(element('dlBtn').disabled, true);

async function testChangedURLWhileAnalyzing() {
  setAnalyzedState();
  let completeFetch;
  context.fetch = () => new Promise(resolve => { completeFetch = resolve; });
  const pending = vm.runInContext('analyze()', context);
  element('url').value = 'https://www.youtube.com/watch?v=jNQXAC9IVRw';
  completeFetch({ ok: true, json: async () => ({ title: 'Old video' }) });
  await pending;
  assert.equal(vm.runInContext('state.url', context), null);
  assert.equal(vm.runInContext('state.selected', context), null);
  assert.equal(element('result').style.display, 'none');
}

testChangedURLWhileAnalyzing().then(() => {
  console.log('UI stale format checks passed');
}).catch(error => {
  console.error(error);
  process.exitCode = 1;
});
