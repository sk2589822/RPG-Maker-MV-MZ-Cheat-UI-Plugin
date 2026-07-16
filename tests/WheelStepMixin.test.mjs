import { test } from 'node:test'
import assert from 'node:assert/strict'
import { computeWheelStepValue } from '../cheat-engine/www/cheat/mixins/WheelStepMixin.js'

test('wheel up (negative deltaY) increases by 1', () => {
    assert.equal(computeWheelStepValue(5, -100, false), 6)
})

test('wheel down (positive deltaY) decreases by 1', () => {
    assert.equal(computeWheelStepValue(5, 100, false), 4)
})

test('Shift increases the step to 10', () => {
    assert.equal(computeWheelStepValue(5, -100, true), 15)
    assert.equal(computeWheelStepValue(5, 100, true), -5)
})

test('numeric strings are parsed', () => {
    assert.equal(computeWheelStepValue('7', -100, false), 8)
})

test('non-numeric value returns null (no-op)', () => {
    assert.equal(computeWheelStepValue('abc', -100, false), null)
})

test('empty or whitespace-only value returns null (no-op)', () => {
    assert.equal(computeWheelStepValue('', -100, false), null)
    assert.equal(computeWheelStepValue('   ', -100, false), null)
})

test('zero deltaY is a no-op', () => {
    assert.equal(computeWheelStepValue(5, 0, false), null)
})

test('negative results are allowed (game handlers clamp)', () => {
    assert.equal(computeWheelStepValue(0, 100, false), -1)
})
