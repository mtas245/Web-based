import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { apiRequest, login } from './api'
import './style.css'

const initialForm = { date: '', grade_level: '', subject_id: '', start: '', end: '', note: '' }

function formatDate(date) {
  return new Intl.DateTimeFormat('de-CH', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(`${date}T12:00:00`))
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('edusub_token') || '')
  const [user, setUser] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [requests, setRequests] = useState([])
  const [subjects, setSubjects] = useState([])
  const [grades, setGrades] = useState([])
  const [form, setForm] = useState(initialForm)
  const [showForm, setShowForm] = useState(false)

  function signOut() {
    sessionStorage.removeItem('edusub_token')
    setToken('')
    setUser(null)
    setRequests([])
    setError('')
    setSuccess('')
  }

  useEffect(() => {
    if (!token) return
    let cancelled = false
    async function initialize() {
      setLoading(true)
      setError('')
      try {
        const current = await apiRequest('/auth/me', { token })
        if (current.role !== 'admin') throw new Error('Diese Milestone-3-Demo ist derzeit für Administratoren vorgesehen.')
        const [allRequests, availableSubjects, availableGrades] = await Promise.all([
          apiRequest('/requests/', { token }),
          apiRequest('/subjects/', { token }),
          apiRequest('/requests/grade-levels'),
        ])
        if (!cancelled) {
          setUser(current)
          setRequests(allRequests)
          setSubjects(availableSubjects)
          setGrades(availableGrades)
        }
      } catch (err) {
        if (!cancelled) {
          if (err.message.includes('Anmeldung ungültig')) signOut()
          setError(err.message)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    initialize()
    return () => { cancelled = true }
  }, [token])

  async function handleLogin(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await login(email.trim(), password)
      if (result.role !== 'admin') throw new Error('Diese Demo ist derzeit nur für Administratoren verfügbar.')
      sessionStorage.setItem('edusub_token', result.access_token)
      setToken(result.access_token)
      setPassword('')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function refreshRequests() {
    const updated = await apiRequest('/requests/', { token })
    setRequests(updated)
  }

  async function handleCreate(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const payload = {
        date: form.date,
        grade_level: form.grade_level,
        subject_id: Number(form.subject_id),
        time_slot: form.start && form.end ? `${form.start}-${form.end}` : null,
        note: form.note.trim() || null,
      }
      await apiRequest('/requests/', { token, method: 'POST', body: JSON.stringify(payload) })
      await refreshRequests()
      setSuccess('Stellvertretungsanfrage erfolgreich erstellt und aus der Datenbank neu geladen.')
      setForm(initialForm)
      setShowForm(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const subjectName = (id) => subjects.find((subject) => subject.id === id)?.name || `Fach #${id}`
  const openCount = requests.filter((request) => request.status === 'open').length
  const filledCount = requests.filter((request) => request.status === 'filled').length
  const today = new Date().toLocaleDateString('en-CA')

  if (!token || (!user && !loading)) {
    return <main className="login-layout">
      <section className="intro-panel">
        <div className="brand brand-light"><span className="brand-icon">E</span> EduSub</div>
        <div className="intro-copy"><span className="eyebrow">SCHULALLTAG. EINFACHER.</span><h1>Die passende Vertretung. Zur richtigen Zeit.</h1><p>Stellvertretungsanfragen zentral erfassen, verwalten und besetzen – übersichtlich und ohne Umwege.</p></div>
        <div className="intro-foot">FHNW · Web-based Applications · Milestone 3</div>
      </section>
      <section className="login-panel">
        <div className="login-card"><span className="pill">Administratorbereich</span><h2>Willkommen zurück</h2><p className="muted">Melde dich an, um deine Stellvertretungen zu verwalten.</p>
          <form onSubmit={handleLogin} className="stack">
            <label>E-Mail-Adresse<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="admin@schule.ch" required /></label>
            <label>Passwort<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Dein Passwort" required /></label>
            {error && <p className="alert error" role="alert">{error}</p>}
            <button className="primary full" disabled={busy || loading}>{busy || loading ? 'Bitte warten …' : 'Anmelden →'}</button>
          </form>
          <p className="login-hint">Demo: Melde dich mit deinem lokal angelegten Administrator an. Zugangsdaten werden nicht im Projekt gespeichert.</p>
        </div>
      </section>
    </main>
  }

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><span className="brand-icon">E</span> EduSub</div><span className="nav-label">ARBEITSBEREICH</span><div className="nav-active">▦ <span>Übersicht</span></div><div className="sidebar-bottom"><div className="avatar">{user.full_name?.[0]?.toUpperCase() || 'A'}</div><div><strong>{user.full_name}</strong><small>Administrator</small></div></div></aside>
    <div className="main-column"><header className="topbar"><div className="mobile-brand">EduSub</div><span className="topbar-caption">Stellvertretungsmanagement</span><button className="ghost" onClick={signOut}>Abmelden ↗</button></header>
      <main className="content"><div className="page-heading"><div><span className="eyebrow dark">ADMIN-DASHBOARD</span><h1>Guten Tag, {user.full_name?.split(' ')[0] || 'Admin'} <span className="wave">👋</span></h1><p className="muted">Hier hast du alle Stellvertretungsanfragen im Blick.</p></div><button className="primary" onClick={() => { setShowForm(true); setError(''); setSuccess('') }}>＋ Neue Anfrage</button></div>
      <section className="stats"><div className="stat"><span>Anfragen gesamt</span><strong>{requests.length}</strong><small>Alle erfassten Anfragen</small></div><div className="stat"><span>Offene Anfragen</span><strong>{openCount}</strong><small>Noch nicht besetzt</small></div><div className="stat"><span>Besetzte Anfragen</span><strong>{filledCount}</strong><small>Erfolgreich vermittelt</small></div></section>
      {error && <p className="alert error" role="alert">{error}</p>}{success && <p className="alert success" role="status">{success}</p>}
      {showForm && <section className="form-card"><div className="card-heading"><div><h2>Neue Stellvertretungsanfrage</h2><p className="muted">Die Anfrage wird direkt über die REST API gespeichert.</p></div><button className="icon-button" aria-label="Formular schliessen" onClick={() => setShowForm(false)}>✕</button></div><form onSubmit={handleCreate} className="request-form"><label>Datum<input type="date" min={today} value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} required /></label><label>Klassenstufe<select value={form.grade_level} onChange={(event) => setForm({ ...form, grade_level: event.target.value })} required><option value="">Bitte wählen</option>{grades.map((grade) => <option key={grade} value={grade}>{grade}</option>)}</select></label><label>Fach<select value={form.subject_id} onChange={(event) => setForm({ ...form, subject_id: event.target.value })} required><option value="">Bitte wählen</option>{subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></label><div className="time-row"><label>Von<input type="time" value={form.start} onChange={(event) => setForm({ ...form, start: event.target.value })} /></label><label>Bis<input type="time" value={form.end} onChange={(event) => setForm({ ...form, end: event.target.value })} /></label></div><label className="wide">Bemerkung (optional)<textarea rows="3" maxLength="1000" value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} placeholder="Wichtige Informationen zur Lektion …" /></label><div className="form-actions"><button type="button" className="secondary" onClick={() => setShowForm(false)}>Abbrechen</button><button className="primary" disabled={busy || !subjects.length}>{busy ? 'Speichert …' : 'Anfrage erstellen →'}</button></div></form>{!subjects.length && <p className="hint">Keine Fächer vorhanden. Bitte zuerst einmalig im Swagger als Admin <code>POST /api/v1/subjects/seed</code> ausführen.</p>}</section>}
      <section className="table-card"><div className="card-heading"><div><h2>Stellvertretungsanfragen</h2><p className="muted">Aktuelle Daten aus dem Backend</p></div><button className="secondary" onClick={async () => { setError(''); try { await refreshRequests() } catch (err) { setError(err.message) } }}>↻ Aktualisieren</button></div><div className="table-scroll"><table><thead><tr><th>DATUM</th><th>KLASSE</th><th>FACH</th><th>ZEIT</th><th>STATUS</th></tr></thead><tbody>{requests.map((request) => <tr key={request.id}><td>{formatDate(request.date)}</td><td><span className="grade">{request.grade_level}</span></td><td>{subjectName(request.subject_id)}</td><td>{request.time_slot || '—'}</td><td><span className={`status ${request.status}`}>{request.status === 'open' ? '● Offen' : request.status === 'filled' ? '● Besetzt' : request.status === 'closed' ? '● Geschlossen' : request.status}</span></td></tr>)}</tbody></table></div>{!requests.length && <div className="empty">Noch keine Stellvertretungsanfragen vorhanden. Erstelle deine erste Anfrage.</div>}</section>
      <footer className="footer">EduSub · Integrationsdemo · React + FastAPI + SQLite</footer>
      </main>
    </div>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
