"""把這個資料夾裡的 cheat（已停用自動更新）裝進 RPG Maker MV/MZ 遊戲，或從遊戲移除。

用法：
    python patch.py <遊戲資料夾>            安裝或更新
    python patch.py --restore <遊戲資料夾>  移除
不給路徑時會詢問，可以直接把資料夾拖進視窗。

<遊戲資料夾> 可以是 Game.exe 所在的資料夾，也可以是裡面的 www 資料夾。
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parent
PAYLOAD_ITEMS = ['cheat', 'cheat-version-description.json']

LOADER = 'cheat/init/import.js'
MAIN_BACKUP_SUFFIX = '.cheat-backup'

# main.js 的改法跟官方網頁 patcher 一致
MV_ANCHOR = re.compile(r'^\s*PluginManager\s*\.\s*setup\s*\(\s*\$plugins\s*\)\s*;')
MZ_ANCHOR = re.compile(r'^\s*(?:const|let|var)\s+scriptUrls\s*=\s*\[')
MV_CHEAT_LINE = re.compile(
    r'^\s*(?:PluginManager\s*\.\s*_path\s*=|//\s*(?:auto generated for cheat|import cheat js file))')
MV_LINES = [
    '// auto generated for cheat',
    "PluginManager._path = 'js/plugins/';",
    f"PluginManager.loadScript('../../{LOADER}');",
]
MZ_LINE = f'    "{LOADER}",'


class PatchError(Exception):
    pass


def find_index(lines, pattern):
    return next((i for i, line in enumerate(lines) if pattern.search(line)), -1)


def mz_array_end(lines, start):
    if ']' in lines[start]:
        raise PatchError('scriptUrls 寫在同一行，無法自動修改 main.js')
    end = next((i for i in range(start + 1, len(lines)) if ']' in lines[i]), -1)
    if end < 0:
        raise PatchError('找不到 scriptUrls 陣列的結尾')
    return end


def strip_mv(lines):
    if not any(LOADER in line for line in lines):
        return lines
    return [line for line in lines if LOADER not in line and not MV_CHEAT_LINE.search(line)]


def strip_mz(lines):
    start = find_index(lines, MZ_ANCHOR)
    end = mz_array_end(lines, start)
    body = [line for line in lines[start + 1:end] if LOADER not in line]
    return lines[:start + 1] + body + lines[end:]


def detect_engine(lines):
    if find_index(lines, MZ_ANCHOR) >= 0:
        return 'MZ'
    if find_index(lines, MV_ANCHOR) >= 0:
        return 'MV'
    raise PatchError('main.js 裡找不到 MV 的 PluginManager.setup($plugins); 或 MZ 的 scriptUrls，不認得這個 main.js')


def patch_lines(lines, engine):
    if engine == 'MV':
        lines = strip_mv(lines)
        anchor = find_index(lines, MV_ANCHOR)
        return lines[:anchor + 1] + MV_LINES + lines[anchor + 1:]
    lines = strip_mz(lines)
    anchor = find_index(lines, MZ_ANCHOR)
    return lines[:anchor + 1] + [MZ_LINE] + lines[anchor + 1:]


def unpatch_lines(lines, engine):
    return strip_mv(lines) if engine == 'MV' else strip_mz(lines)


class MainScript:
    def __init__(self, path):
        self.path = path
        try:
            self.text = path.read_bytes().decode('utf-8')
        except UnicodeDecodeError:
            raise PatchError(f'{path} 不是 UTF-8，無法自動修改')
        self.newline = '\r\n' if self.text.count('\r\n') * 2 > self.text.count('\n') else '\n'
        self.lines = re.split(r'\r\n|\r|\n', self.text)
        self.engine = detect_engine(self.lines)

    def render(self, lines):
        return self.newline.join(lines)

    def write(self, text):
        self.path.write_bytes(text.encode('utf-8'))


def resolve_game(raw):
    path = Path(raw.strip().strip('"').strip("'")).expanduser()
    if path.is_file():
        path = path.parent
    if not path.is_dir():
        raise PatchError(f'找不到資料夾：{path}')
    content = next((c for c in (path / 'www', path) if (c / 'js' / 'main.js').is_file()), None)
    if content is None:
        raise PatchError(f'{path} 裡找不到 js/main.js 或 www/js/main.js，這看起來不是 RPG Maker MV/MZ 遊戲')
    # 遊戲執行時的工作目錄（Game.exe 那層），cheat 的設定存在它底下的 www/cheat-settings
    root = content.parent if content.name.lower() == 'www' else content
    return content, root


def check_payload():
    missing = [name for name in PAYLOAD_ITEMS if not (PAYLOAD_DIR / name).exists()]
    if missing:
        raise PatchError(f'{PAYLOAD_DIR} 少了：{", ".join(missing)}')


def install(raw):
    check_payload()
    content, root = resolve_game(raw)
    main = MainScript(content / 'js' / 'main.js')
    patched = main.render(patch_lines(main.lines, main.engine))
    print(f'引擎：{main.engine}')
    print(f'安裝到：{content}')

    shutil.copytree(PAYLOAD_DIR / 'cheat', content / 'cheat', dirs_exist_ok=True)
    shutil.copy2(PAYLOAD_DIR / 'cheat-version-description.json', content)
    print('已複製 cheat/ 與 cheat-version-description.json')

    # 官方更新器留下的備份與紀錄：不清掉的話 import.js 可能把官方版回滾蓋回來
    update_dir = root / 'www' / 'cheat-settings' / 'update'
    if update_dir.is_dir():
        shutil.rmtree(update_dir)
        print(f'已刪除官方更新器資料：{update_dir}')

    if patched == main.text:
        print('main.js 已經載入 cheat，不用修改')
    else:
        backup = main.path.with_name(main.path.name + MAIN_BACKUP_SUFFIX)
        if not backup.exists():
            shutil.copy2(main.path, backup)
            print(f'已備份 main.js：{backup}')
        main.write(patched)
        print('已修改 main.js')

    web_backup = root / '[_cheat-patch-backup-Qx7v_]'
    if web_backup.is_dir():
        print(f'註：{web_backup} 是官方網頁 patcher 的備份，裡面有原始 main.js，沒有動它')
    print('完成，可以啟動遊戲了')


def restore(raw):
    content, root = resolve_game(raw)
    main = MainScript(content / 'js' / 'main.js')
    print(f'引擎：{main.engine}')
    print(f'從這裡移除：{content}')

    restored = main.render(unpatch_lines(main.lines, main.engine))
    if restored == main.text:
        print('main.js 沒有載入 cheat，不用修改')
    else:
        main.write(restored)
        print('已從 main.js 移除 cheat')

    backup = main.path.with_name(main.path.name + MAIN_BACKUP_SUFFIX)
    if backup.is_file():
        if backup.read_bytes() == main.path.read_bytes():
            backup.unlink()
            print('main.js 已和安裝前的備份相同，刪除備份')
        else:
            print(f'註：main.js 和安裝前的備份不同，保留備份：{backup}')

    cheat_dir = content / 'cheat'
    if cheat_dir.is_dir():
        shutil.rmtree(cheat_dir)
        print(f'已刪除 {cheat_dir}')
    description = content / 'cheat-version-description.json'
    if description.is_file():
        description.unlink()
        print(f'已刪除 {description}')

    print(f'設定檔保留在 {root / "www" / "cheat-settings"}，不需要可以自己刪')
    print('完成')


def main():
    # 輸出被導向檔案時 Windows 會用系統編碼，遇到印不出的字（例如日文遊戲路徑）不要讓整個安裝中斷
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors='backslashreplace')

    parser = argparse.ArgumentParser(description='安裝或移除 RPG Maker MV/MZ cheat（已停用自動更新）')
    parser.add_argument('game', nargs='?', help='遊戲資料夾（Game.exe 所在或 www）')
    parser.add_argument('--restore', action='store_true', help='從遊戲移除 cheat')
    args = parser.parse_args()

    interactive = args.game is None
    raw = args.game if not interactive else input('遊戲資料夾路徑：')
    try:
        (restore if args.restore else install)(raw)
        code = 0
    except PatchError as e:
        print(f'錯誤：{e}', file=sys.stderr)
        code = 1
    if interactive:
        input('按 Enter 結束')
    sys.exit(code)


if __name__ == '__main__':
    main()
