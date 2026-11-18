/** Date-only comparisons in local time: lesson dates do not carry a timezone. */
export function upcomingOpenRequests(requests, today = new Date()) {
  const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const lastDay = new Date(midnight)
  lastDay.setDate(lastDay.getDate() + 7)

  return requests
    .filter((request) => {
      if (request.status !== 'open') return false
      const [year, month, day] = request.date.split('-').map(Number)
      const date = new Date(year, month - 1, day)
      return date >= midnight && date <= lastDay
    })
    .sort((a, b) => a.date.localeCompare(b.date) || a.id - b.id)
}

export function filterRequests(requests, { query = '', status = 'all', grade = 'all' }, subjectName) {
  const needle = query.trim().toLocaleLowerCase('de-CH')
  return requests.filter((request) => {
    if (status !== 'all' && request.status !== status) return false
    if (grade !== 'all' && request.grade_level !== grade) return false
    const searchable = [request.date, request.grade_level, subjectName(request.subject_id), request.note || ''].join(' ').toLocaleLowerCase('de-CH')
    return searchable.includes(needle)
  })
}
