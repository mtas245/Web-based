import React from 'react'

export default function RequestFilters({ value, onChange, grades, count, total }) {
  const update = (key, next) => onChange({ ...value, [key]: next })
  return <div className="request-filters" aria-label="Anfragen filtern">
    <label>Suche<input type="search" value={value.query} onChange={(event) => update('query', event.target.value)} placeholder="Fach, Klasse, Datum, Bemerkung …" /></label>
    <label>Status<select value={value.status} onChange={(event) => update('status', event.target.value)}><option value="all">Alle Status</option><option value="open">Offen</option><option value="filled">Besetzt</option><option value="closed">Geschlossen</option></select></label>
    <label>Klasse<select value={value.grade} onChange={(event) => update('grade', event.target.value)}><option value="all">Alle Klassen</option>{grades.map((grade) => <option key={grade} value={grade}>{grade}</option>)}</select></label>
    <div className="filter-summary" role="status">{count} von {total} Anfragen</div>
    <button type="button" className="secondary" onClick={() => onChange({ query: '', status: 'all', grade: 'all' })}>Zurücksetzen</button>
  </div>
}
