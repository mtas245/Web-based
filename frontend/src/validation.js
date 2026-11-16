/** Return a user-facing error, or null for a valid optional lesson time slot. */
export function validateTimeRange(start, end) {
  if (!start && !end) return null
  if (!start || !end) return 'Bitte sowohl Beginn als auch Ende der Lektion eingeben.'
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(start) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(end)) {
    return 'Bitte gültige Uhrzeiten im Format HH:MM eingeben.'
  }
  if (end <= start) return 'Die Endzeit muss nach der Startzeit liegen.'
  return null
}
