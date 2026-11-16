import test from 'node:test'
import assert from 'node:assert/strict'
import { validateTimeRange } from './validation.js'

test('allows both times omitted', () => assert.equal(validateTimeRange('', ''), null))
test('allows a valid lesson', () => assert.equal(validateTimeRange('08:00', '12:00'), null))
test('rejects inverted range', () => assert.match(validateTimeRange('12:00', '08:00'), /Endzeit/))
test('rejects equal times', () => assert.match(validateTimeRange('08:00', '08:00'), /Endzeit/))
test('rejects a missing end time', () => assert.match(validateTimeRange('08:00', ''), /sowohl/))
test('rejects a missing start time', () => assert.match(validateTimeRange('', '08:00'), /sowohl/))
test('rejects malformed time', () => assert.match(validateTimeRange('25:00', '08:00'), /gültige/))
