import React, { useState } from 'react'
import { apiRequest } from './api'
import { validateTimeRange } from './validation'
import './request-row.css'

function initialValues(request) {
  const [start = '', end = ''] = request.time_slot?.split('-') || []
  return {
    date: request.date,
    grade_level: request.grade_level,
    subject_id: String(request.subject_id),
    start,
    end,
    note: request.note || '',
  }
}

export default function RequestRow({ request, token, grades, subjects, subjectName, onChanged }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(() => initialValues(request))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const change = (field, value) => {
    setForm((previous) => ({ ...previous, [field]: value }))
    setError('')
  }

  async function save(event) {
    event.preventDefault()
    const timeError = validateTimeRange(form.start, form.end)
    if (timeError) { setError(timeError); return }

    setBusy(true)
    setError('')
    try {
      await apiRequest(`/requests/${request.id}`, {
        token,
        method: 'PATCH',
        body: JSON.stringify({
          date: form.date,
          grade_level: form.grade_level,
          subject_id: Number(form.subject_id),
          time_slot: form.start ? `${form.start}-${form.end}` : null,
          note: form.note.trim() || null,
        }),
      })
      await onChanged()
      setEditing(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (!window.confirm(`Anfrage #${request.id} wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.`)) return
    setBusy(true)
    setError('')
    try {
      await apiRequest(`/requests/${request.id}`, { token, method: 'DELETE' })
      await onChanged()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const statusLabel = { open: '● Offen', filled: '● Besetzt', closed: '● Geschlossen' }
  return <>
    <tr>
      <td data-label="Datum">{new Intl.DateTimeFormat('de-CH', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(`${request.date}T12:00:00`))}</td>
      <td data-label="Klasse"><span className="grade">{request.grade_level}</span></td>
      <td data-label="Fach">{subjectName(request.subject_id)}</td>
      <td data-label="Zeit">{request.time_slot || '—'}</td>
      <td data-label="Status"><span className={`status ${request.status}`}>{statusLabel[request.status] || request.status}</span></td>
      <td data-label="Aktionen">
        {request.status === 'open' ? <div className="row-actions">
          <button type="button" className="secondary small" disabled={busy} onClick={() => { setForm(initialValues(request)); setError(''); setEditing(!editing) }}>{editing ? 'Schliessen' : 'Bearbeiten'}</button>
          <button type="button" className="danger small" disabled={busy} onClick={remove}>Löschen</button>
        </div> : <span className="muted">Nicht bearbeitbar</span>}
        {!editing && error && <p className="row-error" role="alert">{error}</p>}
      </td>
    </tr>
    {editing && <tr className="edit-row"><td colSpan={6}>
      <form onSubmit={save} className="request-form edit-form">
        <label>Datum<input type="date" min={new Date().toLocaleDateString('en-CA')} value={form.date} onChange={(event) => change('date', event.target.value)} required /></label>
        <label>Klassenstufe<select value={form.grade_level} onChange={(event) => change('grade_level', event.target.value)} required>{grades.map((grade) => <option key={grade} value={grade}>{grade}</option>)}</select></label>
        <label>Fach<select value={form.subject_id} onChange={(event) => change('subject_id', event.target.value)} required>{subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></label>
        <div className="time-row"><label>Von<input type="time" value={form.start} onChange={(event) => change('start', event.target.value)} /></label><label>Bis<input type="time" value={form.end} onChange={(event) => change('end', event.target.value)} /></label></div>
        <label className="wide">Bemerkung (optional)<textarea rows="2" maxLength="1000" value={form.note} onChange={(event) => change('note', event.target.value)} /></label>
        {error && <p className="alert error form-error" role="alert">{error}</p>}
        <div className="form-actions"><button type="button" className="secondary" disabled={busy} onClick={() => { setEditing(false); setError('') }}>Abbrechen</button><button className="primary" disabled={busy}>{busy ? 'Speichert …' : 'Änderungen speichern'}</button></div>
      </form>
    </td></tr>}
  </>
}
