---
name: update-upstream
description: Upgrade the v2 branch to a newer paramonos upstream release — download the minified build, malware-audit it, disable its auto-updater, refresh hashes. Use when updating the cheat to a new upstream version or checking upstream for one.
---

# Update upstream

The `v2` branch ships paramonos's official v2 release files (closed source, minified) with the network auto-updater disabled, installed into games by `patch.py`. An update swaps in a newer release. That code runs inside the game's NW.js with the player's full privileges, so every release passes the malware **audit** gate before any of it reaches the repo.

Downloads are untrusted data: give each one its own empty scratch directory, keep your scripts elsewhere, read them with Python `-I`, and execute none of them.

## 1. Fetch

- List releases via `https://api.github.com/repos/paramonos/RPG-Maker-MV-MZ-Cheat-UI-Plugin/releases`. The **target** is the tag the user named, else the latest. The **baseline** is the version in the repo's `cheat-version-description.json`: the last audited release. Target equal to baseline means there is nothing to update; tell the user and stop.
- Download the target's `rpg-mv-cheat-<tag>.zip` and `rpg-mz-cheat-<tag>.zip` and the baseline's mv zip; extract each into its own directory.
- Confirm the baseline is the build that was audited: its `cheat/cheat.js` SHA-256 equals README's `(官方原檔，修改前)` hash.
- Compare the target's mv and mz trees. Up to v2.2.0 they were identical (one build, engine detected at runtime); if they differ, both go through the audit.
- When the target is the latest release, check it against the signed site manifest. Verify with the public key copied from the **baseline** `cheat.js` (the `-----BEGIN PUBLIC KEY-----` block); a key inside the new build cannot vouch for itself:
  ```
  base=https://paramonos.github.io/RPG-Maker-MV-MZ-Cheat-UI-Plugin
  curl -s -o desc.json $base/cheat-version-description.json
  curl -s -o desc.json.sig $base/cheat-version-description.json.sig
  openssl base64 -d -A -in desc.json.sig -out desc.sig.bin
  openssl dgst -sha256 -verify baseline-pub.pem -signature desc.sig.bin desc.json
  ```
  Then the SHA-256 of `$base/payload/<tag>/mv/files.json` equals `listings.mv` in `desc.json`, and every file hash it lists equals the zip's file (same for `mz`).

**Done when** the target and baseline trees are extracted, the baseline hash matches README, and the target either matches the signed manifest or you have recorded why it could not be checked (not the latest release). A failed signature or a hash mismatch ends the update: report it to the user.

## 2. Audit (gate)

Dispatch a general-purpose subagent whose prompt is: read `.claude/skills/update-upstream/AUDIT.md` and follow it, with the absolute paths of the baseline and target trees, their release zips, and a scratch directory for its analysis. The separate context keeps the later steps from pulling on the audit.

When the report returns, open every delta it cites in the network, process, code-loading, filesystem, and updater categories yourself and check that the code says what the report says.

**Done when** the verdict is `CLEAN`, every delta carries an explanation you confirmed at its cited line, and the coverage table lists all eleven scans. A `SUSPICIOUS` or `UNEXPLAINED` item, or a report you could not confirm, ends the update: show the user the item, its code, and your reading of it, and wait for their decision.

## 3. Disable the auto-updater

Locate the updater fresh in a prettified copy of the target `cheat/cheat.js`, around `paramonos.github.io`, `cheat.update.automatic`, `BEGIN PUBLIC KEY`, and `cheat-version-description.json.sig`; minified names change with every release. In v2.1.1 it took two edits, recorded in README's modification table:

- the function reading `cheat.update.automatic` returns `!1` (automatic update always off);
- the updater's fetch wrapper `(e,t)=>window.fetch(e,t)` becomes `(e,t)=>Promise.reject(Error(\`update disabled\`))`, so the manual "check for updates" button fails offline too.

Edit the raw minified file with a script that asserts each original string occurs exactly once. Then trace every call from the update code to the network; each one has to land in the neutered wrapper. A new path (a second wrapper, a direct `window.fetch`, an XHR) gets neutered the same way.

**Done when** `node --check` passes on the edited file, every network call reachable from the updater is traced to a neutered function, and a diff of original against edited (split on `;,{}`) shows only your edits.

## 4. Check the install contract

`patch.py` mirrors the official web patcher. Re-confirm its assumptions against the target:

- payload layout `cheat/` plus `cheat-version-description.json`, loader at `cheat/init/import.js`;
- the `main.js` edits: fetch the site's `index.html`, then its `assets/index-*.js`, and find the strings `auto generated for cheat` and `scriptUrls`. The MV anchor and three inserted lines, the MZ anchor and array line, and the lines it strips must match `MV_ANCHOR`, `MV_LINES`, `MV_CHEAT_LINE`, `MZ_ANCHOR`, and `MZ_LINE` in `patch.py`;
- settings under `./www/cheat-settings`, with the updater's rollback state in `update/` (the target `import.js` restores from `update/previous` when `update-record.json` is mid-update; `patch.py` deletes `update/` so that cannot bring the official files back).

The speed-keys plugin (`plugin/`, see README) sits beside the cheat and leans on these cheat behaviours, so confirm them too:

- `shortcuts.json` keeps its shape (`{ <actionId>: { shortcut, param? } }`, key names like `alt 1`), the cheat ignores action ids it does not know, and it stops a key event only when the key is bound to one of its actions;
- the cheat's default shortcut table (the object holding `toggleCheatModal: { shortcut: ... }`) binds none of the keys in `plugin/speed-keys.json`, unless `plugin/shortcuts-override.json` reassigns that action. The cheat fills missing defaults at first launch, after `patch.py`'s conflict clearing has run, so a new default on a plugin key would collide unnoticed;
- `gameSpeed.json` still stores `{"data": "{\"rate\":…,\"sceneOption\":…}"}`, which `reset_cheat_game_speed` in `patch.py` reads.

**Done when** each assumption is confirmed in the target's code, or `patch.py`, the plugin files, and the expectations in `tests/` are updated to match it.

## 5. Update the repo

Two commits, following the branch's convention, so the official-vs-ours diff stays reviewable:

1. `chore: update upstream to <tag>`: replace `cheat/` and `cheat-version-description.json` with the target's official files; in README set the version (title, source link) and list every official SHA-256; in `AUDIT.md`, fold the deltas the audit explained into the known-benign list and bump its heading's version, so the next audit starts from this build.
2. `fix: disable network auto-updater in <tag>`: apply step 3's edits; in README update the modification table with the new minified strings and list the edited `cheat.js` hash next to the official one, marked `(官方原檔，修改前)`.

Run `python -I -X utf8 tests/test_patch.py` and `node --test` on the second commit.

**Done when** the first prints `0 failure(s)`, the second reports no failures, and both commits exist. Push both together, so the remote never has a tip with the updater live, once the user confirms.

## 6. Report

Tell the user: target tag, manifest verification result, audit verdict with the deltas worth knowing (new features that touch the network or files), the updater edits, test result, and the commits.
