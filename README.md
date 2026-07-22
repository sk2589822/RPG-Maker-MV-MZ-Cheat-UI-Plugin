# RPG-Maker-MV-MZ-Cheat-UI-Plugin

- Forked from [paramonos/RPG-Maker-MV-MZ-Cheat-UI-Plugin](https://github.com/paramonos/RPG-Maker-MV-MZ-Cheat-UI-Plugin) v1.0.3

## ChangeLog

v1.4.2

- Give the value/amount inputs a fixed width and right-align their digits so they no longer vary in size row to row in the item and variable panels

v1.4.1

- The cheat UI now stays fully opaque at all times (removed the fade that made it transparent until hovered)
- Value inputs and switch toggles are right-aligned in the item, switch and variable panels

v1.4.0

- Scroll the mouse wheel over a numeric input to change its value (scroll up to increase, down to decrease); hold Shift to step by 10. Applies to item/weapon/armor amounts, variable values, HP/MP, actor level/EXP/stats, gold, teleport X/Y and the map read-interval

v1.3.0

- Scroll the mouse wheel over a table to flip pages (scroll down for the next page, up for the previous). Applies to the item, save/recall, shortcut, switch, teleport and variable panels

v1.2.0

- Shortcuts now trigger even when extra modifier keys are held (e.g. pressing shift+m also fires a shortcut mapped to m)

v1.1.3

- Keep only 3 move speed shortcuts

v1.1.2

- Properly remove translation feature

v1.1.1

- Set fixed move speed when using shortcut

v1.1.0
- Remove translation feature
- Update default shortcuts
- Add shorts for setting move speed to 1-9
- Add shorts for setting game speed to 1-9
- Change cheat modal size to 95% of window
- Show 15 items per page
- Do not focus on filter input when SaveRecallPanel opened
- Properly set variable when input is number
- Add map events panel (Forked from https://github.com/Justype/RPG-Maker-MV-MZ-Cheat-UI-Plugin)