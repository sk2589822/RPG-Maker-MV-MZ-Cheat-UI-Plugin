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
- **updater weakening**: a new URL, a new public key, a looser verification chain, or a wider path whitelist.

## Setup

Work only on copies, and only read: never run, import, or open the build in a browser. Run any Python with `-I`.

1. List every file in both trees with SHA-256. Every file that is new or changed in the target is in scope. Expect `cheat/cheat.js`, `cheat/cheat.css`, `cheat/init/import.js`, `cheat/LICENSES.txt`, `cheat-version-description.json`; a new file of any kind is a delta to explain.
2. Prettify each JS file of both trees into an analysis directory: `npx --yes prettier@3.3.3 --write <file>`. Cite all locations as `<tree>/<file>:<line>` in the prettified copies.

## Inventory

Run each scan on baseline and target and compare. A **delta** is any hit, URL, module, path, or behaviour present in the target and absent or different in the baseline. Counts going up are deltas even when the pattern was already present.

1. **Network sinks**: `fetch(`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `sendBeacon`, `navigator.connection`, `new Image(` with remote `src`, `<link`/`<script` with remote URLs, `require` of `http`, `https`, `net`, `tls`, `dns`, `dgram`, `http2`.
2. **URLs**: extract every `https?://` and `//host` string; diff the sets.
3. **Node modules**: the build reaches Node through a wrapper around `window.require` (find it by searching `window.require`, then list the wrapper's call sites and arguments). Diff the module sets. Also search for `process.binding`, `process.dlopen`, `global.require`, `nw.require`, `module.require`.
4. **Processes and shell**: `child_process`, `exec`, `spawn`, `fork`, `execFile`, `powershell`, `cmd.exe`, `reg add`, `schtasks`, `wscript`, `cscript`, `Shell.openItem`, `Shell.openExternal`, `nw.App`.
5. **Code loading**: `eval(`, `new Function`, `Function(`, `setTimeout`/`setInterval` with a string argument, `import(`, `importScripts`, `WebAssembly`, `new Worker`, `SharedWorker`, `createObjectURL` feeding a script, `document.write`, `vm.runIn`, `script.src`/`script.text` assignments.
6. **Filesystem writes**: `writeFile`, `writeFileSync`, `appendFile`, `copyFile`, `rename`, `unlink`, `rm`, `rmdir`, `mkdir`, `createWriteStream`, `symlink`, `chmod`. Resolve each path argument to its constant or source.
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

A delta you cannot explain from the code is **UNEXPLAINED**. A delta whose code does something the threat model lists is **SUSPICIOUS**. Report both; do not resolve them by assumption.

## Updater check

Locate the updater (search `cheat-version-description.json.sig`, `BEGIN PUBLIC KEY`, `listings`, `updatableFrom`) and confirm, citing locations:

- the base URL, compared with the baseline's;
- the public key: SHA-256 of its DER (`openssl pkey -pubin -in key.pem -outform DER | sha256sum`), compared with the baseline's and with the known fingerprint `c24dd4f73a9409bafd892cba8f205ec0a057b613f930aa23434ff737d9a68531`;
- the chain: RSA-SHA256 signature over the description, then `listings.<engine>` equals SHA-256 of `files.json`, then each file equals its SHA-256 in `files.json`;
- the path whitelist for downloaded files (baseline: only `cheat-version-description.json` and `cheat/...`, no `.` or `..` segments);
- downloaded bytes are only written to disk, never evaluated in-process.

Any change to any of these is a delta.

## Known-benign baseline (v2.1.1)

These were traced and explained in v2.1.1. Re-confirm each still matches; anything beyond them is a delta.

- **Updater**: `https://paramonos.github.io/RPG-Maker-MV-MZ-Cheat-UI-Plugin/`, fetched through `(e,t)=>window.fetch(e,t)`, automatic at startup (at most hourly) unless the `cheat.update.automatic` setting is `false`; writes `./www/cheat-settings/update/{staging,previous}/`, `last-check.json`, `update-record.json`, then copies into the install's `cheat/` and `cheat-version-description.json`. The shipped repo disables this; the audit still checks the target's own code.
- **Translation**: plain `fetch` to endpoints the user configures; built-in presets `https://api-free.deepl.com/v2/translate`, `https://papago.naver.com/api/text/translation`, `https://translate.googleapis.com/translate_a/t?...`, `http://localhost:5000/translate`, `http://localhost:8000`, `http://localhost:1234/v1/chat/completions`; doc links to DeepL, LibreTranslate, eztrans-server, ezTransWeb. Runs only when the user turns translation on.
- **Local reads**: `XMLHttpRequest` to the game's own `data/MapNNN.json`; `createObjectURL` turning image bytes into an `Image` for map previews.
- **Node modules**: `fs`, `path`, `os`, `buffer`, `crypto`, `nw.gui` (window control, clipboard). No `child_process`, `http`, `https`, `net`.
- **File writes**: under `./www/cheat-settings/` (`kv-storage.json` and other settings via temp-file-then-rename, `translation-cache/`, `snapshots/`), plus a settings backup/restore that writes the settings JSON files into a folder the user picks in an in-app folder browser (uses `os.homedir()` and existing drive letters to start browsing).
- **Links**: `import.js` opens README guide URLs on github.com with `nw.Shell.openExternal` when the user clicks the guide button.
- **Absent in v2.1.1**: `eval`, `new Function`, `WebSocket`, `sendBeacon`, `EventSource`, `atob`, `fromCharCode`, `WebAssembly`, `new Worker`, `process.env` (in `cheat.js`; `import.js` reads `USERPROFILE`/`HOME` only to redact paths in the crash report it shows locally).

## Report

Return, in this order:

1. **Verdict**: `CLEAN` only when every delta is explained and the updater check matches; otherwise `SUSPICIOUS` or `UNEXPLAINED`, naming the worst item.
2. **File table**: every file, both hashes, new/changed/same.
3. **Deltas**: one entry per delta: category, `<tree>/<file>:<line>`, trigger, data flow, explanation or the reason it stays unexplained.
4. **Updater**: URL, key fingerprint, chain, whitelist, each marked same/changed.
5. **Baseline drift**: any baseline item that changed shape, even if still benign.
6. **Coverage**: each inventory scan run, with its baseline and target hit counts.
