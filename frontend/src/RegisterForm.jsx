import React, { useState } from 'react'
import { apiRequest } from './api'

/** Public registration; new teachers must be approved before signing in. */
export default function RegisterForm({ onBack }) {
  const [data, setData] = useState({ full_name: '', email: '', phone: '', password: '', confirm: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [registered, setRegistered] = useState(false)

  function update(field, value) {
    setData((current) => ({ ...current, [field]: value }))
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    if (data.password !== data.confirm) {
      setError('Die Passwörter stimmen nicht überein.')
      return
    }
    const bytes = new TextEncoder().encode(data.password).length
    if (bytes > 72) {
      setError('Bitte ein kürzeres Passwort verwenden (maximal 72 UTF-8-Bytes).')
      return
    }
    setBusy(true)
    setError('')
    try {
      const form = new FormData()
      for (const field of ['full_name', 'email', 'phone', 'password']) {
        form.set(field, field === 'password' ? data[field] : data[field].trim())
      }
      // Optional teacher subjects/documents are a later, separate workflow.
      const result = await apiRequest('/auth/register', { method: 'POST', body: form })
      if (result.is_approved !== false) throw new Error('Unerwarteter Freigabestatus. Bitte den Administrator kontaktieren.')
      setRegistered(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (registered) return <div className="registration-result" role="status"><div className="pill">Registrierung eingereicht</div><h2>Vielen Dank!</h2><p className="muted">Dein Konto wurde erstellt und wartet auf die Freigabe durch einen Administrator. Erst danach kannst du dich anmelden.</p><button className="primary full" onClick={onBack}>Zur Anmeldung</button></div>

  return <div className="registration-form"><span className="pill">Lehrperson registrieren</span><h2>Neues Konto erstellen</h2><p className="muted">Bitte verwende für unsere lokale Demo nur Testdaten.</p><form className="stack" onSubmit={submit}>
    <label>Vollständiger Name<input autoComplete="name" value={data.full_name} onChange={(event) => update('full_name', event.target.value)} required /></label>
    <label>E-Mail-Adresse<input type="email" autoComplete="email" value={data.email} onChange={(event) => update('email', event.target.value)} required /></label>
    <label>Telefonnummer<input type="tel" autoComplete="tel" value={data.phone} onChange={(event) => update('phone', event.target.value)} required /></label>
    <label>Passwort (mindestens 8 Zeichen)<input type="password" autoComplete="new-password" minLength={8} value={data.password} onChange={(event) => update('password', event.target.value)} required /></label>
    <label>Passwort bestätigen<input type="password" autoComplete="new-password" minLength={8} value={data.confirm} onChange={(event) => update('confirm', event.target.value)} required /></label>
    {error && <p className="alert error" role="alert">{error}</p>}
    <button className="primary full" disabled={busy}>{busy ? 'Wird registriert …' : 'Registrierung absenden →'}</button>
  </form><button className="ghost back-login" onClick={onBack}>← Zur Anmeldung</button></div>
}
