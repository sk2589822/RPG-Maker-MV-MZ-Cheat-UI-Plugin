import {MAX_KEY_CODE, UNASSIGNED_KEY_CODE} from './KeyCodes.js'

export class ShortcutMap {
    constructor () {
        this.actionTable = new Array(2 * 2 * 2 * 2 * (MAX_KEY_CODE + 1))
    }

    static toInt (booleanVar) {
        // Number(booleanVar) / booleanVar|0 ... can be slot
        return booleanVar === true ? 1 : 0
    }

    /**
     * get flatten index of key
     *
     * @param key
     * @returns {number}
     */
    static tableIndex (key) {
        return this.toInt(key.ctrl) + 2 * this.toInt(key.alt) + 4 * this.toInt(key.shift) + 8 * this.toInt(key.meta) + 16 * key.code
    }

    /**
     * register key-action
     *
     * @param key
     * @param action
     */
    register (key, value, enterAction, repeatAction, leaveAction) {
        if (!key || key.isEmpty()) {
            return
        }

        this.actionTable[ShortcutMap.tableIndex(key)] = {
            value: value,
            enterAction: enterAction,
            repeatAction: repeatAction,
            leaveAction: leaveAction
        }
    }

    /**
     * remove key-action
     *
     * @param key
     * @return: previous value of removed key
     */
    remove (key) {
        if (!key|| key.isEmpty()) {
            return null
        }

        const idx = ShortcutMap.tableIndex(key)
        const removed = this.actionTable[idx]

        this.actionTable[idx] = null

        if (removed) {
            return removed.value
        }

        return null
    }

    getValue (key) {
        const item = this.getItem(key)

        if (item) {
            return item.value
        }

        return null
    }

    /**
     * run action on key
     *
     * @param key
     * @type Key
     */
    runEnterAction (key) {
        const item = this.getItem(key)

        if (item) {
            item.enterAction()
            return true
        }

        return false
    }

    runRepeatAction (key) {
        const item = this.getItem(key)

        if (item) {
            item.repeatAction()
            return true
        }

        return false
    }

    runLeaveAction (key) {
        const item = this.getItem(key)

        if (item) {
            item.leaveAction()
            return true
        }

        return false
    }

    getItem (key) {
        const index = ShortcutMap.tableIndex(key)

        if (index < this.actionTable.length && this.actionTable[index]) {
            return this.actionTable[index]
        }

        // Subset matching: a shortcut triggers if its required modifiers are all
        // present in the pressed key. Pick the most specific (most modifiers) match.
        const pressedMods = ShortcutMap.toInt(key.ctrl)
            | (ShortcutMap.toInt(key.alt) << 1)
            | (ShortcutMap.toInt(key.shift) << 2)
            | (ShortcutMap.toInt(key.meta) << 3)
        const baseIndex = 16 * key.code

        let bestMatch = null
        let bestBits = -1

        let sub = pressedMods
        do {
            sub = (sub - 1) & pressedMods
            const item = this.actionTable[sub + baseIndex]
            if (item) {
                const bits = sub.toString(2).replace(/0/g, '').length
                if (bits > bestBits) {
                    bestBits = bits
                    bestMatch = item
                }
            }
        } while (sub > 0)

        return bestMatch
    }
}
