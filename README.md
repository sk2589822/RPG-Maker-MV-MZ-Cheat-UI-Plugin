# paramonos cheat v2.1.1

RPG Maker MV/MZ 的作弊 UI。這個分支收錄官方 v2.1.1 的發布檔，並附一個本機安裝腳本，不需要透過官方網頁 patch。舊的 v1 在 `main` 分支。

來源：https://github.com/paramonos/RPG-Maker-MV-MZ-Cheat-UI-Plugin/releases/tag/v2.1.1
（MV 與 MZ 的 zip 內容完全相同，由程式在執行時判斷引擎）

SHA-256（與官方 zip 相同）：

```
70dd15b92fab1c74eb0fb07ef6dde51848cb29a6aaf4016a467bff27ea47aab2  cheat-version-description.json   (官方原檔)
0ad9b7d7818b3e0242ff3093df29449345f4c8698e8c56aabc15e184019d5bb4  cheat/cheat.css                  (官方原檔)
afb45b22f73bbe3c4c3519bb467f121bda76349966c0158ad54c0082cc288761  cheat/cheat.js                   (官方原檔)
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
2. 第一次修改前，把原本的 `js/main.js` 備份成 `js/main.js.cheat-backup`，再照官方網頁 patcher 的方式修改 `js/main.js`。重複執行不會重複插入。

移除時會從 `main.js` 拿掉 cheat 那幾行，刪掉 `cheat/` 和 `cheat-version-description.json`；`main.js` 和備份一致時順便刪掉備份。設定檔 `www/cheat-settings/` 會保留。

不想用腳本的話，照下面手動做也一樣。

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

如果 `js/main.js` 已經被官方網頁改過（裡面已有 `cheat/init/import.js`），就不用再改 main.js。官方網頁的備份在遊戲根目錄（`Game.exe` 那層）的 `[_cheat-patch-backup-Qx7v_]/`，裡面有原始的 `main.js`。

## 授權

`cheat/` 內的程式是 paramonos 以 MIT License 發布的 v2.1.1（Copyright (c) 2022 paramonos），本分支為再散布，非官方版本。依 MIT 條款，`cheat/LICENSES.txt`（含 paramonos 本身與 Vue、Lucide 的授權聲明）必須隨檔案一起保留。
