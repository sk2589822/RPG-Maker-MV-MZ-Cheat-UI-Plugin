# Malware audit: paramonos cheat release

You are auditing a closed-source, minified build of an RPG Maker MV/MZ cheat before it is shipped. You receive two extracted release trees: the **baseline** (the last release that passed this audit) and the **target** (the new one). Your output is a verdict the update depends on, so be relentless: a capability you did not trace is a capability you cannot vouch for.

## Threat model

The build is loaded into the game's NW.js window with Node integration, so it runs with the player's full user privileges: any file, any process, any network. Look for:

- **exfiltration**: sending saves, settings, env vars, browser profiles, tokens, or file listings anywhere;
- **remote code**: anything fetched and then evaluated, injected as a `<script>`, written into an executable location, or loaded as a Worker/WASM;
- **process and persistence**: spawning processes, writing `.exe`/`.bat`/`.ps1`/`.vbs`, Startup folder, registry, scheduled tasks;
- **mining and abuse**: WebAssembly, Workers, sustained hidden computation;
- **obfuscation**: payloads hidden in encoded strings, character-code arithmetic, dynamic property names hiding `require`/`eval`;
- **triggered behaviour**: code gated on dates, locale, machine name, or the presence of specific files;
- **updater weakening**: a new URL, a new public key, a looser verification chain, or a wider path whitelist;
- **writes by proxy**: files written through the game's own engine APIs instead of `fs`.

## Setup

Work only on copies, and only read: the build is never run, imported, or opened in a browser. Static parsing (prettier, an AST parser such as acorn) counts as reading. Run any Python with `-I`.

1. When you are given the release zips, confirm each tree's files equal the zip's contents byte for byte.
2. List every file in both trees with SHA-256. Every file that is new or changed in the target is in scope. Expect `cheat/cheat.js`, `cheat/cheat.css`, `cheat/init/import.js`, `cheat/LICENSES.txt`, `cheat-version-description.json`; a new file of any kind is a delta to explain.
3. Prettify each JS file of both trees into an analysis directory: `npx --yes prettier@3.3.3 --write <file>`. Cite all locations as `<tree>/<file>:<line>` in the prettified copies.

## Inventory

Run each scan on baseline and target and compare. The audit covers the **security surface**: the scan hits below, every call site of the filesystem, network, Node, process, and code-loading APIs, and the sets of URLs, Node modules, and free globals. A release can add thousands of lines of feature code; code that touches none of the surface is out of scope.

A **delta** is a surface item present in the target and absent or different in the baseline. Count call sites in the prettified files, and a rising count is a delta even when the pattern already existed. A hit that is not the sink it looks like (`RegExp.prototype.exec`, a UI string containing "rename", a minified name like `rm`) is a **false positive**: list it once with its receiver or context as the reason, not as a delta.

1. **Network sinks**: `fetch(`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `sendBeacon`, `navigator.connection`, `new Image(` with remote `src`, `<link`/`<script` with remote URLs, `require` of `http`, `https`, `net`, `tls`, `dns`, `dgram`, `http2`.
2. **URLs**: extract every `https?://` and `//host` string; diff the sets.
3. **Node modules**: the build reaches Node through a wrapper around `window.require` (find it by searching `window.require`, then list the wrapper's call sites and arguments), and may reach it by other routes. Also search every `.require` property access, the `nw` global and `window.nw`, `process.mainModule`, `process.binding`, `process.dlopen`, `global.require`, `module.require`. Diff the module sets per file.
4. **Processes and shell**: `child_process`, `exec`, `spawn`, `fork`, `execFile`, `powershell`, `cmd.exe`, `reg add`, `schtasks`, `wscript`, `cscript`, `Shell.openItem`, `Shell.openExternal`, `nw.App`.
5. **Code loading**: `eval(`, `new Function`, `Function(`, `setTimeout`/`setInterval` with a string argument, `import(`, `importScripts`, `WebAssembly`, `new Worker`, `SharedWorker`, `createObjectURL` feeding a script, `document.write`, `vm.runIn`, `script.src`/`script.text` assignments.
6. **Filesystem writes**: `writeFile`, `writeFileSync`, `appendFile`, `copyFile`, `rename`, `unlink`, `rm`, `rmdir`, `mkdir`, `createWriteStream`, `symlink`, `chmod`, and writes by proxy through the engine: `StorageManager`, `DataManager.saveGame`, `ConfigManager.save`, `localforage`. Resolve each path argument to its constant or source.
7. **Sensitive strings**: `APPDATA`, `LOCALAPPDATA`, `USERPROFILE`, `HOME`, `homedir`, `process.env`, `Local Storage`, `Cookies`, `Login Data`, `.ssh`, `wallet`, `discord`, `token`, `password`, `Startup`, `\Run`, `.exe`, `.bat`, `.ps1`, `.vbs`, `document.cookie`, `clipboard` reads.
8. **Obfuscation**: `atob`, `btoa`, `Buffer.from(` with `base64`/`hex`, `String.fromCharCode`, `charCodeAt` inside decode loops, string literals over 200 characters of base64/hex alphabet, dense `\x`/`\u` escapes, computed member access building identifiers from fragments.
9. **Triggers**: `new Date`/`Date.now` compared against fixed values, `navigator.language`/`Intl` branches that change network or file behaviour, `os.hostname`, `os.userInfo`.
10. **Stylesheet**: `url(` and `@import` in `cheat.css` pointing off-machine.
11. **`import.js`**: read the whole prettified target file. It is the loader `main.js` runs first; every line of it is in scope, not just the scan hits.

## Explaining a delta

Open each delta in the target at its cited line with at least 40 lines of context and write down:

- what triggers it: a user action (button, setting, hotkey) or automatic (startup, timer);
- what it reads and what leaves the machine, to where;
- why it is benign, tied to visible code, not to a feature name or a string label.

A delta you cannot explain from the code is **UNEXPLAINED**. A delta whose code does something the threat model lists is **SUSPICIOUS**. Report both as they stand; deciding what to do about them belongs to the user.

## Updater check

Locate the updater (search `cheat-version-description.json.sig`, `BEGIN PUBLIC KEY`, `listings`, `updatableFrom`) and confirm, citing locations:

- the base URL, compared with the baseline's;
- the public key: SHA-256 of its DER (`openssl pkey -pubin -in key.pem -outform DER | sha256sum`), compared with the baseline's and with the known fingerprint `c24dd4f73a9409bafd892cba8f205ec0a057b613f930aa23434ff737d9a68531`;
- the chain: RSA-SHA256 signature over the description, then `listings.<engine>` equals SHA-256 of `files.json`, then each file equals its SHA-256 in `files.json`;
- the path whitelist for downloaded files (baseline: only `cheat-version-description.json` and `cheat/...`, no `.` or `..` segments);
- downloaded bytes are only written to disk, never evaluated in-process.

Any change to any of these is a delta.

## Known-benign behaviour (audited through v2.1.1)

What earlier audits traced and explained, as of v2.1.1. It speeds up explaining a delta and never removes one: every delta still goes in the report. Check each item against the target and report any change under baseline drift.

- **Updater** (`cheat.js`): `https://paramonos.github.io/RPG-Maker-MV-MZ-Cheat-UI-Plugin/`, fetched through `(e,t)=>window.fetch(e,t)`, automatic at startup (at most hourly) unless the `cheat.update.automatic` setting is `false`, and skipped when the previous start never completed. Writes `./www/cheat-settings/update/{staging,previous}/`, `last-check.json`, `update-record.json`, then copies into the install's `cheat/` and `cheat-version-description.json`. The shipped repo disables this; the audit still checks the target's own code.
- **Translation** (`cheat.js`): plain `fetch` to endpoints the user configures; built-in presets `https://api-free.deepl.com/v2/translate`, `https://papago.naver.com/api/text/translation`, `https://translate.googleapis.com/translate_a/t?...`, `http://localhost:5000/translate`, `http://localhost:8000`, `http://localhost:1234/v1/chat/completions`; doc links to DeepL, LibreTranslate, eztrans-server, ezTransWeb. Every send checks that translation and its target are enabled (both off by default); the settings "test" button sends fixed sample strings.
- **Local reads** (`cheat.js`): relative `XMLHttpRequest` to the game's own `data/MapNNN.json` and `img/` files (`system`, `faces`, `characters`, `enemies`, `sv_enemies`, `tilesets`, `parallaxes`; names `encodeURIComponent`'d), decrypted with the game's key and turned into an `Image` through `createObjectURL`.
- **Node modules**: `cheat.js` through its wrapper: `fs`, `path`, `os`, `buffer`, `crypto`, `nw.gui` (devtools window only). `import.js`: `fs` and `path` through `window.require`, and `nw.gui`/`window.nw` for `Shell.openExternal` and clipboard writes. No `child_process`, `http`, `https`, `net` anywhere.
- **File writes** (`cheat.js`):
  - under `./www/cheat-settings/`: settings JSON (`kv-storage.json`, `shortcuts.json`, `valueLocks.json`, `favorites.json`, `gameOptions.json`, translation files) written as `<file>.unfinished` then renamed over, unparsable files renamed to `<file>.broken`; `translation-cache/`; `snapshots/<id>.jsonl` (id `^[A-Za-z0-9_-]+$`; game state the user chooses to snapshot);
  - by proxy: `ConfigManager.save()` when the user changes game options, temporarily wrapping `StorageManager.saveObject` only to catch its promises;
  - settings backup/restore: the settings JSON files written into a folder the user picks in an in-app folder browser (starts from `os.homedir()` and existing drive letters).
- **`import.js`**: the loader plus a startup error card. Captures `error`/`unhandledrejection` coming from cheat files so they don't crash the game, listens for one key to reopen the card, and sets a 10 s startup deadline. The report it shows locally has versions, OS, plugin names, and stacks, with `USERPROFILE`/`HOME`/cwd redacted; it reaches the clipboard only when the user clicks Copy. "See the fix" opens fixed github.com README URLs with `nw.Shell.openExternal`. Reads `cheat.language` from `./www/cheat-settings/kv-storage.json`. Rolls back a failed update from `./www/cheat-settings/update/previous`.
- **Absent**: `eval`, `new Function`, `WebSocket`, `sendBeacon`, `EventSource`, `atob`, `btoa`, `fromCharCode`, `WebAssembly`, `new Worker`, `child_process`; `process.env` only in `import.js` for the redaction above.

## Report

Return, in this order:

1. **Verdict**: `CLEAN` only when every delta is explained and the updater check matches; otherwise `SUSPICIOUS` or `UNEXPLAINED`, naming the worst item.
2. **File table**: every file, both hashes, new/changed/same.
3. **Deltas**: one entry per delta: category, `<tree>/<file>:<line>`, trigger, data flow, explanation or the reason it stays unexplained.
4. **Updater**: URL, key fingerprint, chain, whitelist, each marked same/changed.
5. **Baseline drift**: any baseline item that changed shape, even if still benign.
6. **Coverage**: each inventory scan run, with its baseline and target hit counts.
