import React, { useEffect, useState } from 'react'
import { apiRequest } from './api'

/** Admin decisions are made by the API. This component only presents the workflow. */
export default function AdminApplications({ token, requests, onRequestsChanged }) {
  const [applications, setApplications] = useState([])
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function reload() {
    const [pending, teacherList] = await Promise.all([
      apiRequest('/applications/pending', { token }),
      apiRequest('/teachers/', { token }),
    ])
    setApplications(pending)
    setTeachers(teacherList)
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([
      apiRequest('/applications/pending', { token }),
      apiRequest('/teachers/', { token }),
    ]).then(([pending, teacherList]) => {
      if (!cancelled) {
        setApplications(pending)
        setTeachers(teacherList)
      }
    }).catch((err) => {
      if (!cancelled) setError(err.message)
    }).finally(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [token])

  const teacherName = (id) => teachers.find((teacher) => teacher.id === id)?.full_name ?? `Lehrperson #${id}`
  const requestLabel = (id) => {
    const request = requests.find((item) => item.id === id)
    return request ? `${request.grade_level} · ${request.date}` : `Anfrage #${id}`
  }

  async function decide(application, action) {
    const verb = action === 'approve' ? 'genehmigen' : 'ablehnen'
    if (!window.confirm(`Bewerbung von ${teacherName(application.teacher_id)} wirklich ${verb}?`)) return
    setBusyId(application.id)
    setError('')
    setNotice('')
    try {
      await apiRequest(`/applications/${application.id}/${action}`, { token, method: 'PATCH' })
      // Refresh both lists: approval also changes the request status to filled.
      await Promise.all([reload(), onRequestsChanged()])
      setNotice(action === 'approve'
        ? 'Bewerbung genehmigt. Die Anfrage wurde erneut geladen und sollte jetzt als besetzt angezeigt werden.'
        : 'Bewerbung abgelehnt. Die ausstehenden Bewerbungen wurden aktualisiert.')
    } catch (err) {
      setError(err.message)
      // The backend may have changed even if refreshing failed; offer another reload.
    } finally {
      setBusyId(null)
    }
  }

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      await Promise.all([reload(), onRequestsChanged()])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return <section className="table-card" aria-label="Bewerbungsverwaltung">
    <div className="card-heading"><div><h2>Offene Bewerbungen <span className="teacher-count">{applications.length}</span></h2><p className="muted">Lehrpersonen auswählen, genehmigen oder ablehnen.</p></div><button className="secondary" disabled={loading || busyId !== null} onClick={refresh}>↻ Aktualisieren</button></div>
    {error && <p className="alert error" role="alert">{error}</p>}
    {notice && <p className="alert success" role="status">{notice}</p>}
    {loading ? <p className="muted">Bewerbungen werden geladen …</p> : <>
      <div className="table-scroll"><table><thead><tr><th>LEHRPERSON</th><th>ANFRAGE</th><th>BEWORBEN AM</th><th>AKTIONEN</th></tr></thead><tbody>{applications.map((application) => <tr key={application.id}><td>{teacherName(application.teacher_id)}</td><td>{requestLabel(application.request_id)}</td><td>{new Date(application.applied_at).toLocaleDateString('de-CH')}</td><td><div className="decision-actions"><button className="primary" disabled={busyId !== null} onClick={() => decide(application, 'approve')}>{busyId === application.id ? 'Bitte warten …' : 'Genehmigen'}</button><button className="secondary" disabled={busyId !== null} onClick={() => decide(application, 'reject')}>Ablehnen</button></div></td></tr>)}</tbody></table></div>
      {!applications.length && <div className="empty">Aktuell liegen keine offenen Bewerbungen vor.</div>}
    </>}
  </section>
}
