# paramonos cheat v2.1.1（已停用自動更新）

RPG Maker MV/MZ 的作弊 UI。這個分支收錄官方 v2.1.1 的發布檔，拿掉了遊戲啟動時自動從網路下載、安裝新版的功能，並附一個本機安裝腳本，不需要透過官方網頁 patch。舊的 v1 在 `main` 分支。

來源：https://github.com/paramonos/RPG-Maker-MV-MZ-Cheat-UI-Plugin/releases/tag/v2.1.1
（MV 與 MZ 的 zip 內容完全相同，由程式在執行時判斷引擎）

## 相對於官方 release 的改動

只改了 `cheat/cheat.js` 兩處，其他檔案與官方 zip 位元組相同：

| 原始 | 改成 | 效果 |
| --- | --- | --- |
| `function o5(){return Wc().getItem(e5)!==\`false\`}` | `function o5(){return!1}` | 自動更新開關永遠視為關閉，啟動時不檢查、不安裝 |
| `i5=(e,t)=>window.fetch(e,t)` | `i5=(e,t)=>Promise.reject(Error(\`update disabled\`))` | 更新器專用的 fetch 一律失敗；在設定裡手動按「檢查更新」也不會連網，只會顯示下載失敗 |

SHA-256：

```
70dd15b92fab1c74eb0fb07ef6dde51848cb29a6aaf4016a467bff27ea47aab2  cheat-version-description.json   (官方原檔)
0ad9b7d7818b3e0242ff3093df29449345f4c8698e8c56aabc15e184019d5bb4  cheat/cheat.css                  (官方原檔)
d85ddbe1871c110cfcc5b076fde9965f9641eb06a1a08ee9dd07bca5e0ae5172  cheat/cheat.js                   (已修改)
afb45b22f73bbe3c4c3519bb467f121bda76349966c0158ad54c0082cc288761  cheat/cheat.js                   (官方原檔，修改前)
0c3741fa94fb2984d18b175dadfbadc00b9ab0137df42e8be2d1a6a0aa92707e  cheat/init/import.js             (官方原檔)
6d7e6d13766b9bc7cf4ff189184f8b04e14cb52ed674e1108ae11591c6664c66  cheat/LICENSES.txt               (官方原檔)
```

## 用 patch.py 安裝（Python 3.8+）

```
python patch.py <遊戲資料夾>            安裝或更新
python patch.py --restore <遊戲資料夾>  移除
```

不帶路徑執行（或直接雙擊）會詢問路徑，可以把資料夾拖進視窗。路徑填 `Game.exe` 所在的資料夾或裡面的 `www` 都可以。

安裝時會：

1. 複製 `cheat/` 和 `cheat-version-description.json` 到內容資料夾。
2. 刪掉官方更新器留下的 `www/cheat-settings/update/`（原因見下方「遊戲以前用官方網頁裝過 v2 的話」）。
3. 安裝[速度快捷鍵外掛](#速度快捷鍵外掛)：複製到內容資料夾的 `cheat-plugin/`，把快捷鍵覆蓋設定合併進 `www/cheat-settings/shortcuts.json`，並把 cheat 視窗記住的遊戲速度重設為 1 倍。
4. 第一次修改前，把原本的 `js/main.js` 備份成 `js/main.js.cheat-backup`，再照官方網頁 patcher 的方式修改 `js/main.js`，並多加一行載入外掛。重複執行不會重複插入。

移除時會從 `main.js` 拿掉 cheat 和外掛那幾行，刪掉 `cheat/`、`cheat-plugin/` 和 `cheat-version-description.json`；`main.js` 和備份一致時順便刪掉備份。設定檔 `www/cheat-settings/` 會保留。

不想用腳本的話，照下面手動做也一樣（手動步驟只裝官方 cheat，不含外掛）。

## 速度快捷鍵外掛

官方 v2 每個動作只能綁一個鍵，也沒有「把遊戲速度設成 N」，所以另外寫了 `plugin/`。它跟官方 `cheat/` 分開，官方更新時不受影響。

| 檔案 | 用途 |
| --- | --- |
| `plugin/speed-keys.js` | 外掛本體：按鍵直接設定遊戲速度或移動速度，畫面上方會短暫顯示目前的值 |
| `plugin/speed-keys.json` | 按鍵設定，寫法和 cheat 的 `shortcuts.json` 相同 |
| `plugin/shortcuts-override.json` | 每次安裝時合併進遊戲 `shortcuts.json` 的 cheat 快捷鍵，讓每個遊戲都用同一套鍵 |

預設按鍵：

| 按鍵 | 效果 |
| --- | --- |
| `1` / `2` / `3`（`~` 右邊那排，不是數字鍵盤） | 遊戲速度 ×1 / ×2 / ×3 |
| `Alt+1` / `Alt+2` / `Alt+3` | 移動速度 4 / 5 / 6，每秒重新套用一次，蓋過遊戲事件的改動 |

- 改按鍵或速度：改 `plugin/speed-keys.json`。遊戲速度 0.1~10，移動速度 1~10；按鍵支援 `ctrl`、`alt`、`shift`、`meta` 加上數字、英文字母、`f1`~`f12`、`numpad0`~`numpad9`。
- 改共用的 cheat 快捷鍵：改 `plugin/shortcuts-override.json`。只寫要覆蓋的動作，其他動作保留各遊戲自己的設定。
- 衝突處理：安裝時會清掉遊戲 `shortcuts.json` 裡跟速度快捷鍵用同一個鍵的 cheat 快捷鍵（例如官方預設的 `Alt+1` 敵人重傷），並列出清掉了哪些；`shortcuts-override.json` 本身如果用到速度快捷鍵的鍵，安裝會直接中止。
- 輸入框裡打字、按住不放的連發都不會觸發。
- cheat 視窗裡的遊戲速度和外掛會相乘，請讓 cheat 視窗保持 1 倍；cheat 的「固定移動速度」也會跟外掛互相蓋掉，二選一使用。
- 改完設定後重新執行 `patch.py` 套用到遊戲。

測試：`python -I -X utf8 tests/test_patch.py` 和 `node --test`。

## 手動 patch 步驟

先找到遊戲的「內容資料夾」：同時有 `index.html` 和 `js/` 的那一層。

- MV：通常是 `<遊戲>/www/`
- MZ：通常是 `<遊戲>/`（`Game.exe` 旁邊）

1. 備份內容資料夾裡的 `js/main.js`。
2. 把這裡的 `cheat/` 資料夾和 `cheat-version-description.json` 複製到內容資料夾。
3. 編輯 `js/main.js`：

   **MV**：在 `PluginManager.setup($plugins);` 這行下面加：

   ```js
   // auto generated for cheat
   PluginManager._path = 'js/plugins/';
   PluginManager.loadScript('../../cheat/init/import.js');
   ```

   **MZ**：在 `const scriptUrls = [` 這行下面，加成陣列第一項：

   ```js
       "cheat/init/import.js",
   ```

4. 啟動遊戲。

還原：把備份的 `js/main.js` 放回去，刪掉 `cheat/` 與 `cheat-version-description.json`。
（設定存在 `<遊戲>/www/cheat-settings/`，要不要刪隨你。）

## 遊戲以前用官方網頁裝過 v2 的話

除了覆蓋 `cheat/` 之外，**一定要刪掉 `<遊戲>/www/cheat-settings/update/`**。

那裡面是官方更新器留下的 `previous/`、`staging/` 和 `update-record.json`。`import.js` 啟動時若看到更新紀錄停在 `swapping` 或 `starting`，會把 `previous/` 裡的舊檔複製回 `cheat/`，蓋掉這份停用更新的版本。

如果 `js/main.js` 已經被官方網頁改過（裡面已有 `cheat/init/import.js`），就不用再改 main.js。官方網頁的備份在遊戲根目錄（`Game.exe` 那層）的 `[_cheat-patch-backup-Qx7v_]/`，裡面有原始的 `main.js`。

## 授權

`cheat/` 內的程式是 paramonos 以 MIT License 發布的 v2.1.1（Copyright (c) 2022 paramonos），本分支為修改後的再散布，非官方版本。依 MIT 條款，`cheat/LICENSES.txt`（含 paramonos 本身與 Vue、Lucide 的授權聲明）必須隨檔案一起保留。
