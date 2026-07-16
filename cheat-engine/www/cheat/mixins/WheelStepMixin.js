// Adds mouse-wheel increment/decrement to a numeric input.
//
// Usage in a component:
//   import WheelStepMixin from '../mixins/WheelStepMixin.js'
//   mixins: [WheelStepMixin]
//
// and on the numeric <v-text-field>:
//   @wheel.native.stop.prevent="onWheelStep($event, item, 'amount', () => onItemChange(item))"
//
// Scrolling up increases the value, down decreases it. Holding Shift
// changes the step from 1 to 10. Non-numeric (or empty) values are left
// untouched. The .stop modifier keeps the surrounding data table from
// paging while the wheel is used on an input.

// Pure value math, exported for unit testing.
// Returns the new numeric value, or null when the current value is not a
// usable number (so the caller does nothing).
export function computeWheelStepValue (current, deltaY, shiftKey) {
    if (!deltaY) {
        return null
    }

    if (typeof current === 'string' && current.trim() === '') {
        return null
    }

    const num = Number(current)
    if (Number.isNaN(num)) {
        return null
    }

    const step = shiftKey ? 10 : 1
    const delta = deltaY < 0 ? step : -step

    return num + delta
}

export default {
    methods: {
        onWheelStep (event, obj, key, onChange) {
            if (!event || !event.deltaY) {
                return
            }

            const next = computeWheelStepValue(obj[key], event.deltaY, event.shiftKey)
            if (next === null) {
                return
            }

            // $set keeps array-index writes (e.g. actor.param[idx]) reactive
            this.$set(obj, key, next)

            if (typeof onChange === 'function') {
                onChange()
            }
        }
    }
}
