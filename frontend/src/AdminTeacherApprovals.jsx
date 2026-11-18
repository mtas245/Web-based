import React, { useEffect, useState } from 'react'
import { apiRequest } from './api'

/** Approval is protected by the backend's administrator-only role dependency. */
export default function AdminTeacherApprovals({ token, onPendingCountChange }) {
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    apiRequest('/teachers/pending', { token })
      .then((data) => { if (active) { setPending(data); onPendingCountChange(data.length) } })
      .catch((err) => { if (active) setError(err.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [token, onPendingCountChange])

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const data = await apiRequest('/teachers/pending', { token })
      setPending(data)
      onPendingCountChange(data.length)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function approve(teacher) {
    if (!window.confirm(`${teacher.full_name} als Lehrperson freigeben?`)) return
    setBusyId(teacher.id)
    setError('')
    setNotice('')
    try {
      await apiRequest(`/teachers/${teacher.id}/approve`, { method: 'PATCH', token })
      const remaining = await apiRequest('/teachers/pending', { token })
      setPending(remaining)
      onPendingCountChange(remaining.length)
      setNotice(`${teacher.full_name} wurde freigegeben und kann sich jetzt anmelden.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  return <section className="table-card" aria-label="Lehrpersonen-Freigabe"><div className="card-heading"><div><h2>Lehrpersonen freigeben <span className="teacher-count">{pending.length}</span></h2><p className="muted">Neue Konten benötigen eine Freigabe vor der ersten Anmeldung.</p></div><button className="secondary" disabled={loading || busyId !== null} onClick={refresh}>↻ Aktualisieren</button></div>
    {error && <p className="alert error" role="alert">{error}</p>}
    {notice && <p className="alert success" role="status">{notice}</p>}
    {loading ? <p className="muted">Lehrpersonen werden geladen …</p> : <><div className="table-scroll"><table><thead><tr><th>NAME</th><th>E-MAIL</th><th>REGISTRIERT AM</th><th>AKTION</th></tr></thead><tbody>{pending.map((teacher) => <tr key={teacher.id}><td>{teacher.full_name}</td><td>{teacher.email}</td><td>{new Date(teacher.created_at).toLocaleDateString('de-CH')}</td><td><button className="primary" disabled={busyId !== null} onClick={() => approve(teacher)}>{busyId === teacher.id ? 'Bitte warten …' : 'Freigeben'}</button></td></tr>)}</tbody></table></div>{!pending.length && <div className="empty">Aktuell warten keine neuen Lehrpersonen auf die Freigabe.</div>}</>}
  </section>
}
