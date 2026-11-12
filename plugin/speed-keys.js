// 速度快捷鍵：一個鍵直接把遊戲速度或移動速度設成指定值。
// 按鍵寫在同資料夾的 speed-keys.json，格式和 cheat 的 shortcuts.json 一樣（例如 "alt 1"）。
// 獨立於 cheat 本體，cheat 更新時不受影響；由 patch.py 裝進遊戲的 cheat-plugin/。
(function () {
  'use strict';

  var CONFIG_URL = 'cheat-plugin/speed-keys.json'; // 相對於遊戲的 index.html
  var MOVE_SPEED_LOCK_MS = 1000; // 移動速度每隔多久重新套用一次，蓋過遊戲事件的改動
  var GAME_SPEED_RANGE = [0.1, 10];
  var MOVE_SPEED_RANGE = [1, 10];
  var MODIFIERS = ['ctrl', 'alt', 'shift', 'meta'];

  var bindings = [];
  var gameRate = 1;
  var frameCarry = 0;
  var isSceneHooked = false;
  var moveSpeedTimer = null;
  var toastElement = null;
  var toastTimer = null;

  // "alt 1" → { code: 'Digit1', alt: true, ... }；無法辨識時回傳 null
  function parseKey(text) {
    var key = { code: null, ctrl: false, alt: false, shift: false, meta: false };
    var tokens = String(text).toLowerCase().split(/\s+/).filter(Boolean);
    for (var i = 0; i < tokens.length; i += 1) {
      var token = tokens[i];
      if (MODIFIERS.indexOf(token) >= 0) {
        key[token] = true;
      } else if (key.code !== null) {
        return null;
      } else if (/^[0-9]$/.test(token)) {
        key.code = 'Digit' + token;
      } else if (/^[a-z]$/.test(token)) {
        key.code = 'Key' + token.toUpperCase();
      } else if (/^numpad[0-9]$/.test(token)) {
        key.code = 'Numpad' + token.slice(6);
      } else if (/^f([1-9]|1[0-2])$/.test(token)) {
        key.code = token.toUpperCase();
      } else {
        return null;
      }
    }
    return key.code === null ? null : key;
  }

  function matches(key, event) {
    return event.code === key.code &&
      event.ctrlKey === key.ctrl &&
      event.altKey === key.alt &&
      event.shiftKey === key.shift &&
      event.metaKey === key.meta;
  }

  function isTyping(target) {
    if (!target || !target.tagName) return false;
    var tag = target.tagName.toUpperCase();
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable === true;
  }

  function inRange(value, range) {
    return typeof value === 'number' && value >= range[0] && value <= range[1];
  }

  function toast(text) {
    if (!document.body) return;
    if (!toastElement) {
      toastElement = document.createElement('div');
      toastElement.style.cssText = 'position: fixed; top: 16px; left: 50%; transform: translateX(-50%);' +
        ' z-index: 2147483001; padding: 6px 16px; border-radius: 6px; background: rgba(20, 20, 24, 0.85);' +
        ' color: #fff; font: 600 15px sans-serif; pointer-events: none; transition: opacity 0.3s;';
      document.body.appendChild(toastElement);
    }
    toastElement.textContent = text;
    toastElement.style.opacity = '1';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastElement.style.opacity = '0';
    }, 1500);
  }

  // 和 cheat 本體相同的作法：一個畫面更新多跑幾次場景更新
  function hookSceneUpdate() {
    var original = SceneManager.updateScene;
    SceneManager.updateScene = function () {
      if (gameRate === 1) return original.apply(this, arguments);
      frameCarry += gameRate;
      var steps = Math.floor(frameCarry);
      frameCarry -= steps;
      if (steps <= 0) return undefined;
      var result = original.apply(this, arguments);
      for (var i = 1; i < steps; i += 1) {
        SceneManager.updateInputData();
        SceneManager.changeScene();
        original.apply(this, arguments);
      }
      return result;
    };
    isSceneHooked = true;
  }

  function setGameSpeed(rate) {
    if (typeof SceneManager === 'undefined') return;
    if (!isSceneHooked && rate !== 1) hookSceneUpdate();
    gameRate = rate;
    frameCarry = 0;
    toast('遊戲速度 ×' + rate);
  }

  function setMoveSpeed(speed) {
    if (typeof $gamePlayer === 'undefined' || !$gamePlayer) {
      toast('進入地圖後才能改移動速度');
      return;
    }
    $gamePlayer.setMoveSpeed(speed);
    clearInterval(moveSpeedTimer);
    moveSpeedTimer = setInterval(function () {
      if (typeof $gamePlayer !== 'undefined' && $gamePlayer) $gamePlayer.setMoveSpeed(speed);
    }, MOVE_SPEED_LOCK_MS);
    toast('移動速度 ' + speed);
  }

  function addBindings(table, range, action, label) {
    Object.keys(table || {}).forEach(function (text) {
      var key = parseKey(text);
      var value = table[text];
      if (!key || !inRange(value, range)) {
        console.warn('[cheat-plugin] 略過無效的' + label + '設定：' + text + ' → ' + value);
        return;
      }
      bindings.push({ key: key, run: function () { action(value); } });
    });
  }

  function onKeyDown(event) {
    if (event.repeat || isTyping(event.target)) return;
    for (var i = 0; i < bindings.length; i += 1) {
      if (matches(bindings[i].key, event)) {
        event.preventDefault();
        bindings[i].run();
        return;
      }
    }
  }

  function loadConfig(done) {
    var request = new XMLHttpRequest();
    request.open('GET', CONFIG_URL);
    request.overrideMimeType('application/json');
    request.onload = function () {
      // 本機檔案成功時 status 是 0
      if (request.status >= 400) return done(null);
      try {
        done(JSON.parse(request.responseText));
      } catch (e) {
        done(null);
      }
    };
    request.onerror = function () { done(null); };
    request.send();
  }

  loadConfig(function (config) {
    if (!config) {
      console.error('[cheat-plugin] 讀不到 ' + CONFIG_URL + '，速度快捷鍵沒有啟用');
      return;
    }
    addBindings(config.gameSpeed, GAME_SPEED_RANGE, setGameSpeed, '遊戲速度');
    addBindings(config.moveSpeed, MOVE_SPEED_RANGE, setMoveSpeed, '移動速度');
    window.addEventListener('keydown', onKeyDown, true);
  });
})();
