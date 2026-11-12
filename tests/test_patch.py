"""patch.py 的回歸測試：在暫存資料夾做假的 MV/MZ 遊戲，跑安裝、重複安裝、移除。

用法：python -I -X utf8 tests/test_patch.py [repo 根目錄]
預期的 main.js 中，官方 cheat 那幾行是官方網頁 patcher 對同一份輸入的輸出（v2.1.1 時逐位元組比對過），
再加上載入 cheat-plugin/speed-keys.js 的一行。
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
PATCH = REPO / 'patch.py'

MV = """//=============================================================================
// main.js
//=============================================================================

PluginManager.setup($plugins);

window.onload = function() {
    SceneManager.run(Scene_Boot);
};
"""
MV_PATCHED = """//=============================================================================
// main.js
//=============================================================================

PluginManager.setup($plugins);
// auto generated for cheat
PluginManager._path = 'js/plugins/';
PluginManager.loadScript('../../cheat/init/import.js');
PluginManager.loadScript('../../cheat-plugin/speed-keys.js');

window.onload = function() {
    SceneManager.run(Scene_Boot);
};
"""
# 舊版（v1 fork）裝過的 main.js
MV_V1 = """//=============================================================================
// main.js
//=============================================================================

PluginManager.setup($plugins);

// import cheat js file
PluginManager._path= 'js/plugins/';
PluginManager.loadScript('../../cheat/init/import.js');

window.onload = function() {
    SceneManager.run(Scene_Boot);
};
"""
MV_V1_PATCHED = """//=============================================================================
// main.js
//=============================================================================

PluginManager.setup($plugins);
// auto generated for cheat
PluginManager._path = 'js/plugins/';
PluginManager.loadScript('../../cheat/init/import.js');
PluginManager.loadScript('../../cheat-plugin/speed-keys.js');


window.onload = function() {
    SceneManager.run(Scene_Boot);
};
"""
MZ = """//=============================================================================
// main.js v1.3.0
//=============================================================================

const scriptUrls = [
    "js/libs/pixi.js",
    "js/rmmz_core.js",
    "js/plugins.js"
];
const effekseerWasmUrl = "js/libs/effekseer.wasm";

new Main().run();
"""
MZ_PATCHED = MZ.replace('const scriptUrls = [\n',
                        'const scriptUrls = [\n    "cheat/init/import.js",\n    "cheat-plugin/speed-keys.js",\n')
MZ_V1 = MZ.replace('const scriptUrls = [\n', 'const scriptUrls = [\n    "../../cheat/init/import.js",\n')
MZ_V1_PATCHED = MZ_PATCHED

BOM = '﻿'
PLUGIN_FILES = ['speed-keys.js', 'speed-keys.json']

# 遊戲原本的 cheat 快捷鍵：一個在覆蓋設定裡、一個跟速度快捷鍵撞鍵、一個是 v2 不認得的 v1 設定
EXISTING_SHORTCUTS = {
    'enemyWound': {'shortcut': 'alt 1'},
    'setSpeed': {'shortcut': 'Alt 3', 'param': {'speed': 5}},
    'setGameSpeed1': {'shortcut': 'shift 1'},
}

# name, 原始 main.js, 預期修改後, 引擎, 換行, 是否加 BOM, 版面（www / root）, 路徑填法, 是否為未裝過 cheat 的原檔, 是否已有 shortcuts.json
CASES = [
    ('mv', MV, MV_PATCHED, 'MV', '\r\n', False, 'www', 'root', True, True),
    ('mv-v1', MV_V1, MV_V1_PATCHED, 'MV', '\r\n', False, 'www', 'www', False, False),
    ('mz', MZ, MZ_PATCHED, 'MZ', '\n', False, 'root', 'exe', True, True),
    ('mz-bom', MZ, MZ_PATCHED, 'MZ', '\n', True, 'root', 'root', True, False),
    ('mz-v1', MZ_V1, MZ_V1_PATCHED, 'MZ', '\r\n', False, 'root', 'root', False, True),
]

failures = []


def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond:
        failures.append(msg)


def run(*args, stdin=None, patch=PATCH):
    return subprocess.run([sys.executable, '-I', '-X', 'utf8', str(patch), *args], input=stdin,
                          capture_output=True, text=True, encoding='utf-8')


def encode(text, newline, bom):
    return ((BOM if bom else '') + text.replace('\n', newline)).encode('utf-8')


def same_tree(a, b):
    fa = sorted(p.relative_to(a) for p in a.rglob('*') if p.is_file())
    fb = sorted(p.relative_to(b) for p in b.rglob('*') if p.is_file())
    return fa == fb and all((a / f).read_bytes() == (b / f).read_bytes() for f in fa)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def make_game(base, name, main_bytes, layout, shortcuts=None):
    root = base / name
    content = root / 'www' if layout == 'www' else root
    (content / 'js').mkdir(parents=True)
    (content / 'js' / 'main.js').write_bytes(main_bytes)
    (root / 'Game.exe').write_bytes(b'')
    settings = root / 'www' / 'cheat-settings'
    stale = settings / 'update' / 'previous' / 'cheat'
    stale.mkdir(parents=True)
    (stale / 'cheat.js').write_text('official build left by the upstream updater')
    (settings / 'kv-storage.json').write_text('{}')
    (settings / 'gameSpeed.json').write_text(json.dumps({'data': json.dumps({'rate': 3, 'sceneOption': 'battle'})}))
    if shortcuts is not None:
        (settings / 'shortcuts.json').write_text(json.dumps(shortcuts))
    return root, content


def expected_shortcuts(had_file):
    override = read_json(REPO / 'plugin' / 'shortcuts-override.json')
    if not had_file:
        return override
    return {**EXISTING_SHORTCUTS, **override,
            'setSpeed': {'shortcut': '', 'param': {'speed': 5}}}


def test_case(base, name, src, expected, engine, newline, bom, layout, form, vanilla, has_shortcuts):
    print(f'== {name}')
    original = encode(src, newline, bom)
    root, content = make_game(base, name, original, layout, EXISTING_SHORTCUTS if has_shortcuts else None)
    main_js = content / 'js' / 'main.js'
    backup = content / 'js' / 'main.js.cheat-backup'
    settings = root / 'www' / 'cheat-settings'
    arg = {'root': root, 'www': root / 'www', 'exe': root / 'Game.exe'}[form]

    r = run(str(arg))
    check(r.returncode == 0, f'install exits 0 {r.stderr.strip()}')
    check(f'引擎：{engine}' in r.stdout, f'detects {engine}')
    check(main_js.read_bytes() == encode(expected, newline, bom), 'main.js loads the cheat and the plugin')
    check(same_tree(REPO / 'cheat', content / 'cheat'), 'cheat/ copied byte-identical')
    check((content / 'cheat-version-description.json').read_bytes()
          == (REPO / 'cheat-version-description.json').read_bytes(), 'cheat-version-description.json copied')
    check(all((content / 'cheat-plugin' / f).read_bytes() == (REPO / 'plugin' / f).read_bytes() for f in PLUGIN_FILES),
          'plugin files copied to cheat-plugin/')
    check(not (content / 'cheat-plugin' / 'shortcuts-override.json').exists(), 'override file stays out of the game')
    check(read_json(settings / 'shortcuts.json') == expected_shortcuts(has_shortcuts),
          'shortcuts.json gets the override and loses keys the plugin uses')
    check(json.loads(read_json(settings / 'gameSpeed.json')['data']) == {'rate': 1, 'sceneOption': 'battle'},
          'remembered cheat game speed reset to 1')
    check(not (settings / 'update').exists(), 'upstream updater state removed')
    check((settings / 'kv-storage.json').exists(), 'user settings kept')
    check(backup.read_bytes() == original, 'backup holds the original main.js')

    patched = main_js.read_bytes()
    r = run(str(arg))
    check(r.returncode == 0 and main_js.read_bytes() == patched, 'second install leaves main.js unchanged')
    check('shortcuts.json 已經是覆蓋後的設定' in r.stdout, 'second install leaves shortcuts.json unchanged')
    check(backup.read_bytes() == original, 'second install keeps the first backup')

    r = run('--restore', str(arg))
    check(r.returncode == 0, f'restore exits 0 {r.stderr.strip()}')
    after = main_js.read_bytes()
    check(b'cheat/init/import.js' not in after and b'cheat-plugin' not in after,
          'restore removes the cheat and plugin lines from main.js')
    check(not any((content / p).exists() for p in ('cheat', 'cheat-plugin', 'cheat-version-description.json')),
          'restore removes cheat and plugin files')
    check((settings / 'shortcuts.json').exists(), 'restore keeps shortcuts.json')
    if vanilla:
        check(after == original, 'restore brings main.js back byte-identical')
        check(not backup.exists(), 'restore deletes the now-redundant backup')
    else:
        check(backup.exists(), 'restore keeps the backup when it differs')


def test_broken_shortcuts(base):
    print('== broken shortcuts.json')
    root, content = make_game(base, 'broken', encode(MV, '\n', False), 'www')
    shortcuts = root / 'www' / 'cheat-settings' / 'shortcuts.json'
    shortcuts.write_text('{ not json')
    r = run(str(root))
    check(r.returncode == 0 and shortcuts.read_text() == '{ not json', 'leaves an unparsable shortcuts.json alone')
    check('不是正確的 JSON' in r.stdout, 'says the override was skipped')


def test_override_clash(base):
    print('== override clashes with plugin keys')
    repo = base / 'repo-copy'
    for name in ('cheat', 'plugin'):
        shutil.copytree(REPO / name, repo / name)
    for name in ('patch.py', 'cheat-version-description.json'):
        shutil.copy2(REPO / name, repo / name)
    override = repo / 'plugin' / 'shortcuts-override.json'
    override.write_text(json.dumps({'enemyWound': {'shortcut': 'alt 1'}}))
    root, content = make_game(base, 'clash', encode(MV, '\n', False), 'www')
    r = run(str(root), patch=repo / 'patch.py')
    check(r.returncode == 1 and 'speed-keys.json' in r.stderr, 'rejects an override that reuses a plugin key')
    check(not (content / 'cheat').exists(), 'writes nothing before rejecting')


def test_errors(base):
    print('== errors')
    empty = base / 'not-a-game'
    empty.mkdir()
    r = run(str(empty))
    check(r.returncode == 1 and '錯誤' in r.stderr, 'rejects a folder without js/main.js')
    check(not (empty / 'cheat').exists(), 'writes nothing to a rejected folder')
    check(run(str(base / 'missing')).returncode == 1, 'rejects a missing folder')


def test_prompt(base):
    print('== prompt')
    root, content = make_game(base, 'prompt', encode(MV, '\r\n', False), 'www')
    r = run(stdin=f'"{root}"\n\n')
    check(r.returncode == 0 and (content / 'cheat' / 'cheat.js').exists(), 'accepts a quoted path from the prompt')


def main():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for case in CASES:
            test_case(base, *case)
        test_broken_shortcuts(base)
        test_override_clash(base)
        test_errors(base)
        test_prompt(base)
    print(f'\n{len(failures)} failure(s)')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
