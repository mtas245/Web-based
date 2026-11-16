const BASE = '/api/v1'

export async function apiRequest(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
  }

  let response
  try {
    response = await fetch(`${BASE}${path}`, { ...options, headers })
  } catch {
    throw new Error('Backend nicht erreichbar. Läuft FastAPI auf Port 8000?')
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    let detail = body.detail
    if (Array.isArray(detail)) detail = detail.map((item) => item.msg).join('; ')
    if (typeof detail !== 'string') detail = `HTTP ${response.status}`
    if (response.status === 401) detail = 'Anmeldung ungültig oder abgelaufen. Bitte erneut anmelden.'
    if (response.status === 403) detail = 'Keine Berechtigung für diese Aktion.'
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response.json()
}

export function login(email, password) {
  const body = new URLSearchParams({ username: email, password })
  return apiRequest('/auth/login', { method: 'POST', body })
}
