import test from 'node:test'
import assert from 'node:assert/strict'
import { upcomingOpenRequests, filterRequests } from './dashboard-utils.js'

const requests = [
  { id: 1, date: '2026-11-19', status: 'open', grade_level: '3a', subject_id: 1, note: 'Morning lesson' },
  { id: 2, date: '2026-11-20', status: 'filled', grade_level: '3a', subject_id: 2, note: null },
  { id: 3, date: '2026-12-02', status: 'open', grade_level: '6a', subject_id: 2, note: 'Afternoon' },
  { id: 4, date: '2026-11-18', status: 'open', grade_level: '6a', subject_id: 2, note: null },
]

test('upcoming requests include today and seven days but exclude filled and later dates', () => {
  const selected = upcomingOpenRequests(requests, new Date(2026, 10, 18))
  assert.deepEqual(selected.map((request) => request.id), [4, 1])
})

test('request filters combine status, grade and searchable subject or note', () => {
  const subjectName = (id) => id === 1 ? 'Mathematik' : 'Deutsch'
  assert.deepEqual(filterRequests(requests, { query: 'Mathe', status: 'open' }, subjectName).map((item) => item.id), [1])
  assert.deepEqual(filterRequests(requests, { query: 'Afternoon', grade: '6a' }, subjectName).map((item) => item.id), [3])
  assert.deepEqual(filterRequests(requests, { status: 'filled' }, subjectName).map((item) => item.id), [2])
})
