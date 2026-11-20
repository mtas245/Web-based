import React, { useState } from 'react'
import { apiRequest } from './api'

function formatDate(value) {
  return new Intl.DateTimeFormat('de-CH', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(`${value}T12:00:00`))
}

/** Teacher-facing view. The API, not this component, decides whether applying is allowed. */
export default function TeacherDashboard({ token, user, subjects, initialRequests, initialApplications, onLogout }) {
  const [requests, setRequests] = useState(initialRequests)
  const [applications, setApplications] = useState(initialApplications)
  const [grade, setGrade] = useState('all')
  const [school, setSchool] = useState('all')
  const [page, setPage] = useState(1)
  const [busyId, setBusyId] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const appliedIds = new Set(applications.map((application) => application.request_id))
  const visibleRequests = requests.filter((request) =>
    (grade === 'all' || request.grade_level === grade) &&
    (school === 'all' || String(request.school_id) === school))
  const pageSize = 5
  const totalPages = Math.max(1, Math.ceil(visibleRequests.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const pagedRequests = visibleRequests.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  const gradeOptions = [...new Set(requests.map((request) => request.grade_level))].sort()
  const schoolOptions = [...new Map(requests.map((request) => [request.school_id, request.school_name || `Schule #${request.school_id}`])).entries()].sort((a, b) => a[1].localeCompare(b[1]))
  const subjectName = (subjectId) => subjects.find((subject) => subject.id === subjectId)?.name ?? `Fach #${subjectId}`

  async function reload() {
    const [available, mine] = await Promise.all([
      apiRequest('/requests/open', { token }),
      apiRequest('/applications/my', { token }),
    ])
    setRequests(available)
    setApplications(mine)
  }

  async function refresh() {
    setRefreshing(true)
    setError('')
    try {
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  async function apply(requestId) {
    setBusyId(requestId)
    setError('')
    setNotice('')
    try {
      await apiRequest(`/requests/${requestId}/apply`, { token, method: 'POST' })
      // Re-read from the server; an optimistic badge is not proof of persistence.
      await reload()
      setNotice('Deine Bewerbung wurde gespeichert und ist jetzt unter „Meine Bewerbungen“ sichtbar.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  return <div className="teacher-layout">
    <header className="teacher-topbar"><div className="brand"><span className="brand-icon">E</span> EduSub</div><div className="teacher-actions"><span>{user.full_name}</span><button className="ghost" onClick={onLogout}>Abmelden ↗</button></div></header>
    <main className="teacher-content">
      <div className="page-heading"><div><span className="eyebrow dark">LEHRPERSONENBEREICH</span><h1>Offene Stellvertretungen</h1><p className="muted">Finde passende Einsätze und bewirb dich direkt über EduSub.</p></div><button className="secondary" disabled={refreshing || busyId !== null} onClick={refresh}>↻ {refreshing ? 'Lädt …' : 'Aktualisieren'}</button></div>
      {error && <p className="alert error" role="alert">{error}</p>}
      {notice && <p className="alert success" role="status">{notice}</p>}
      <section className="table-card"><div className="card-heading"><div><h2>Verfügbare Anfragen <span className="teacher-count">{visibleRequests.length}</span></h2><p className="muted">Offene Anfragen aller teilnehmenden Schulen – direkt aus der API.</p></div><div className="teacher-filter-controls"><label className="teacher-filter">Schule<select aria-label="Nach Schule filtern" value={school} onChange={(event) => { setSchool(event.target.value); setPage(1) }}><option value="all">Alle Schulen</option>{schoolOptions.map(([id, name]) => <option key={id} value={String(id)}>{name}</option>)}</select></label><label className="teacher-filter">Klasse<select aria-label="Nach Klasse filtern" value={grade} onChange={(event) => { setGrade(event.target.value); setPage(1) }}><option value="all">Alle Klassen</option>{gradeOptions.map((level) => <option key={level} value={level}>{level}</option>)}</select></label></div></div>
      <div className="teacher-list">{pagedRequests.map((request) => <article className="teacher-request" key={request.id}><div className="teacher-request-info"><div className="teacher-school-name">{request.school_name || `Schule #${request.school_id}`}</div><div className="teacher-request-date">{formatDate(request.date)} <span className="grade">{request.grade_level}</span></div><h3>{subjectName(request.subject_id)}</h3><p className="muted">{request.time_slot || 'Zeit nach Vereinbarung'}{request.note ? ` · ${request.note}` : ''}</p></div><button className={appliedIds.has(request.id) ? 'secondary' : 'primary'} disabled={appliedIds.has(request.id) || busyId !== null} onClick={() => apply(request.id)}>{appliedIds.has(request.id) ? '✓ Beworben' : busyId === request.id ? 'Wird gesendet …' : 'Bewerben →'}</button></article>)}</div>
      {visibleRequests.length > pageSize && <nav className="teacher-pagination" aria-label="Seitennavigation Stellvertretungen"><button className="secondary" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>← Zurück</button><span>Seite {currentPage} von {totalPages}</span><button className="secondary" disabled={currentPage === totalPages} onClick={() => setPage(currentPage + 1)}>Weiter →</button></nav>}
      {!visibleRequests.length && <div className="empty">Für diesen Filter sind aktuell keine offenen Stellvertretungen vorhanden.</div>}</section>
      <section className="table-card"><div className="card-heading"><div><h2>Meine Bewerbungen</h2><p className="muted">Status direkt vom Backend</p></div></div><div className="table-scroll"><table><thead><tr><th>ANFRAGE</th><th>BEWORBEN AM</th><th>STATUS</th></tr></thead><tbody>{applications.map((application) => <tr key={application.id}><td>#{application.request_id}</td><td>{new Date(application.applied_at).toLocaleDateString('de-CH')}</td><td><span className={`status ${application.status}`}>{application.status === 'pending' ? '● Ausstehend' : application.status === 'approved' ? '● Genehmigt' : application.status === 'rejected' ? '● Abgelehnt' : application.status}</span></td></tr>)}</tbody></table></div>{!applications.length && <div className="empty">Du hast dich noch auf keine Stellvertretungsanfrage beworben.</div>}</section>
      <footer className="footer">EduSub · React-Komponente · REST API · gespeicherte Bewerbungen</footer>
    </main>
  </div>
}
