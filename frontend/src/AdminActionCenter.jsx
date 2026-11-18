import React from 'react'
import { upcomingOpenRequests } from './dashboard-utils'

export default function AdminActionCenter({ requests, pendingApplications, pendingTeachers, subjectName }) {
  const upcoming = upcomingOpenRequests(requests)
  const next = upcoming[0]
  const pendingTotal = (pendingApplications ?? 0) + (pendingTeachers ?? 0) + upcoming.length

  return <section className="action-center" aria-labelledby="action-center-title">
    <div className="action-center-heading">
      <div><span className="eyebrow dark">DEIN ÜBERBLICK</span><h2 id="action-center-title">Das steht als Nächstes an</h2><p className="muted">Offene Einsätze innerhalb von sieben Tagen und ausstehende Entscheidungen.</p></div>
      <span className="action-counter">{pendingTotal} {pendingTotal === 1 ? 'Hinweis' : 'Hinweise'}</span>
    </div>
    <div className="action-grid">
      <a className="action-item" href="#requests-list">
        <span className="action-icon" aria-hidden="true">◷</span>
        <div><strong>{upcoming.length} {upcoming.length === 1 ? 'offener Einsatz' : 'offene Einsätze'} in den nächsten 7 Tagen</strong>
          <p>{next ? `${next.grade_level} · ${subjectName(next.subject_id)} · ${new Date(`${next.date}T12:00:00`).toLocaleDateString('de-CH')}` : 'Aktuell sind keine zeitnahen Einsätze offen.'}</p></div>
        <span className="action-arrow" aria-hidden="true">→</span>
      </a>
      <a className="action-item" href="#pending-applications">
        <span className="action-icon" aria-hidden="true">✉</span>
        <div><strong>{pendingApplications === null ? 'Bewerbungen werden geladen' : `${pendingApplications} ${pendingApplications === 1 ? 'Bewerbung wartet' : 'Bewerbungen warten'} auf Entscheidung`}</strong><p>Bewerbungen prüfen und passende Lehrpersonen auswählen.</p></div>
        <span className="action-arrow" aria-hidden="true">→</span>
      </a>
      <a className="action-item" href="#pending-teachers">
        <span className="action-icon" aria-hidden="true">✓</span>
        <div><strong>{pendingTeachers === null ? 'Lehrpersonen werden geladen' : `${pendingTeachers} ${pendingTeachers === 1 ? 'Lehrperson wartet' : 'Lehrpersonen warten'} auf Freigabe`}</strong><p>Neue Accounts prüfen und bei Bedarf freischalten.</p></div>
        <span className="action-arrow" aria-hidden="true">→</span>
      </a>
    </div>
  </section>
}
