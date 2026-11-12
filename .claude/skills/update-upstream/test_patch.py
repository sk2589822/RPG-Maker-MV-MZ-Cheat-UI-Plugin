"""patch.py 的回歸測試：在暫存資料夾做假的 MV/MZ 遊戲，跑安裝、重複安裝、移除。

用法：python -I -X utf8 test_patch.py [repo 根目錄]
預期的 main.js 是官方網頁 patcher 對同一份輸入的輸出（v2.1.1 時逐位元組比對過）。
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
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
MZ_PATCHED = MZ.replace('const scriptUrls = [\n', 'const scriptUrls = [\n    "cheat/init/import.js",\n')
MZ_V1 = MZ.replace('const scriptUrls = [\n', 'const scriptUrls = [\n    "../../cheat/init/import.js",\n')
MZ_V1_PATCHED = MZ_PATCHED

BOM = '﻿'

# name, 原始 main.js, 預期修改後, 引擎, 換行, 是否加 BOM, 版面（www / root）, 路徑填法, 是否為未裝過 cheat 的原檔
CASES = [
    ('mv', MV, MV_PATCHED, 'MV', '\r\n', False, 'www', 'root', True),
    ('mv-v1', MV_V1, MV_V1_PATCHED, 'MV', '\r\n', False, 'www', 'www', False),
    ('mz', MZ, MZ_PATCHED, 'MZ', '\n', False, 'root', 'exe', True),
    ('mz-bom', MZ, MZ_PATCHED, 'MZ', '\n', True, 'root', 'root', True),
    ('mz-v1', MZ_V1, MZ_V1_PATCHED, 'MZ', '\r\n', False, 'root', 'root', False),
]

failures = []


def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond:
        failures.append(msg)


def run(*args, stdin=None):
    return subprocess.run([sys.executable, '-I', '-X', 'utf8', str(PATCH), *args], input=stdin,
                          capture_output=True, text=True, encoding='utf-8')


def encode(text, newline, bom):
    return ((BOM if bom else '') + text.replace('\n', newline)).encode('utf-8')


def same_tree(a, b):
    fa = sorted(p.relative_to(a) for p in a.rglob('*') if p.is_file())
    fb = sorted(p.relative_to(b) for p in b.rglob('*') if p.is_file())
    return fa == fb and all((a / f).read_bytes() == (b / f).read_bytes() for f in fa)


def make_game(base, name, main_bytes, layout):
    root = base / name
    content = root / 'www' if layout == 'www' else root
    (content / 'js').mkdir(parents=True)
    (content / 'js' / 'main.js').write_bytes(main_bytes)
    (root / 'Game.exe').write_bytes(b'')
    stale = root / 'www' / 'cheat-settings' / 'update' / 'previous' / 'cheat'
    stale.mkdir(parents=True)
    (stale / 'cheat.js').write_text('official build left by the upstream updater')
    (root / 'www' / 'cheat-settings' / 'kv-storage.json').write_text('{}')
    return root, content


def test_case(base, name, src, expected, engine, newline, bom, layout, form, vanilla):
    print(f'== {name}')
    original = encode(src, newline, bom)
    root, content = make_game(base, name, original, layout)
    main_js = content / 'js' / 'main.js'
    backup = content / 'js' / 'main.js.cheat-backup'
    arg = {'root': root, 'www': root / 'www', 'exe': root / 'Game.exe'}[form]

    r = run(str(arg))
    check(r.returncode == 0, f'install exits 0 {r.stderr.strip()}')
    check(f'引擎：{engine}' in r.stdout, f'detects {engine}')
    check(main_js.read_bytes() == encode(expected, newline, bom), 'main.js matches the official web patcher output')
    check(same_tree(REPO / 'cheat', content / 'cheat'), 'cheat/ copied byte-identical')
    check((content / 'cheat-version-description.json').read_bytes()
          == (REPO / 'cheat-version-description.json').read_bytes(), 'cheat-version-description.json copied')
    check(not (root / 'www' / 'cheat-settings' / 'update').exists(), 'upstream updater state removed')
    check((root / 'www' / 'cheat-settings' / 'kv-storage.json').exists(), 'user settings kept')
    check(backup.read_bytes() == original, 'backup holds the original main.js')

    patched = main_js.read_bytes()
    r = run(str(arg))
    check(r.returncode == 0 and main_js.read_bytes() == patched, 'second install leaves main.js unchanged')
    check(backup.read_bytes() == original, 'second install keeps the first backup')

    r = run('--restore', str(arg))
    check(r.returncode == 0, f'restore exits 0 {r.stderr.strip()}')
    check(b'cheat/init/import.js' not in main_js.read_bytes(), 'restore removes the loader from main.js')
    check(not (content / 'cheat').exists() and not (content / 'cheat-version-description.json').exists(),
          'restore removes cheat files')
    if vanilla:
        check(main_js.read_bytes() == original, 'restore brings main.js back byte-identical')
        check(not backup.exists(), 'restore deletes the now-redundant backup')
    else:
        check(backup.exists(), 'restore keeps the backup when it differs')


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
        test_errors(base)
        test_prompt(base)
    print(f'\n{len(failures)} failure(s)')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
