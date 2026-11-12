// plugin/speed-keys.js 的測試：用假的遊戲環境載入外掛，模擬按鍵。
// 用法：在 repo 根目錄執行 node --test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const PLUGIN = readFileSync(fileURLToPath(new URL('../plugin/speed-keys.js', import.meta.url)), 'utf8');
const CONFIG = readFileSync(fileURLToPath(new URL('../plugin/speed-keys.json', import.meta.url)), 'utf8');

function loadPlugin({ config = CONFIG, hasPlayer = true } = {}) {
  const listeners = [];
  const intervals = new Map();
  let nextTimer = 1;
  const game = {
    sceneUpdates: 0,
    moveSpeeds: [],
    toasts: [],
    listeners,
    intervals,
  };
  const toastElement = { style: {}, set textContent(text) { game.toasts.push(text); } };
  const sandbox = {
    console: { warn() {}, error() {} },
    window: { addEventListener: (type, fn, capture) => listeners.push({ type, fn, capture }) },
    document: { body: { appendChild() {} }, createElement: () => toastElement },
    XMLHttpRequest: class {
      open(method, url) { this.url = url; }
      overrideMimeType() {}
      send() {
        if (config === null) return this.onerror();
        this.status = 0;
        this.responseText = config;
        this.onload();
      }
    },
    SceneManager: {
      updateScene() { game.sceneUpdates += 1; },
      updateInputData() {},
      changeScene() {},
    },
    $gamePlayer: hasPlayer ? { setMoveSpeed: (speed) => game.moveSpeeds.push(speed) } : null,
    setTimeout: () => 0,
    clearTimeout() {},
    setInterval: (fn) => { const id = nextTimer++; intervals.set(id, fn); return id; },
    clearInterval: (id) => intervals.delete(id),
  };
  vm.runInNewContext(PLUGIN, sandbox);
  game.press = (code, modifiers = {}, extra = {}) => {
    const event = {
      code,
      ctrlKey: false, altKey: false, shiftKey: false, metaKey: false,
      repeat: false,
      target: { tagName: 'CANVAS' },
      defaultPrevented: false,
      preventDefault() { this.defaultPrevented = true; },
      ...modifiers,
      ...extra,
    };
    listeners.filter((l) => l.type === 'keydown').forEach((l) => l.fn(event));
    return event;
  };
  game.frame = () => {
    const before = game.sceneUpdates;
    sandbox.SceneManager.updateScene();
    return game.sceneUpdates - before;
  };
  game.tickLock = () => intervals.forEach((fn) => fn());
  return game;
}

test('number keys set the game speed', () => {
  const game = loadPlugin();
  assert.equal(game.frame(), 1);
  assert.ok(game.press('Digit2').defaultPrevented);
  assert.equal(game.frame(), 2);
  game.press('Digit3');
  assert.equal(game.frame(), 3);
  game.press('Digit1');
  assert.equal(game.frame(), 1);
  assert.deepEqual(game.toasts, ['遊戲速度 ×2', '遊戲速度 ×3', '遊戲速度 ×1']);
});

test('alt + number keys set and lock the move speed', () => {
  const game = loadPlugin();
  game.press('Digit1', { altKey: true });
  game.press('Digit3', { altKey: true });
  assert.deepEqual(game.moveSpeeds, [4, 6]);
  assert.equal(game.intervals.size, 1, 'the previous lock is replaced');
  game.tickLock();
  assert.deepEqual(game.moveSpeeds, [4, 6, 6]);
  assert.equal(game.frame(), 1, 'move speed keys leave the game speed alone');
});

test('other modifier combinations, repeats and typing are ignored', () => {
  const game = loadPlugin();
  assert.equal(game.press('Digit2', { shiftKey: true }).defaultPrevented, false);
  game.press('Digit2', { ctrlKey: true, altKey: true });
  game.press('Numpad2');
  game.press('Digit2', {}, { repeat: true });
  game.press('Digit2', {}, { target: { tagName: 'input' } });
  game.press('Digit2', {}, { target: { tagName: 'DIV', isContentEditable: true } });
  assert.equal(game.frame(), 1);
  assert.deepEqual(game.moveSpeeds, []);
});

test('move speed waits for the map', () => {
  const game = loadPlugin({ hasPlayer: false });
  game.press('Digit1', { altKey: true });
  assert.equal(game.intervals.size, 0);
  assert.deepEqual(game.toasts, ['進入地圖後才能改移動速度']);
});

test('invalid config entries are skipped and the rest still work', () => {
  const game = loadPlugin({
    config: JSON.stringify({
      gameSpeed: { 'alt 1 2': 2, '4': 99, 'numpad5': 0.5 },
      moveSpeed: { 'ctrl f2': 3, 'hyper 1': 4 },
    }),
  });
  game.press('Digit4');
  assert.equal(game.frame(), 1);
  game.press('Numpad5');
  assert.equal(game.frame() + game.frame(), 1, 'half speed runs one update every two frames');
  game.press('F2', { ctrlKey: true });
  assert.deepEqual(game.moveSpeeds, [3]);
});

test('a missing config leaves the keys unbound', () => {
  const game = loadPlugin({ config: null });
  assert.equal(game.listeners.length, 0);
});
