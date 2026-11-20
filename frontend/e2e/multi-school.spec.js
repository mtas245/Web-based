import { test, expect } from '@playwright/test'

async function signIn(page, email, password) {
  await page.goto('/')
  await page.getByLabel('E-Mail-Adresse').fill(email)
  await page.getByLabel('Passwort', { exact: true }).fill(password)
  await page.getByRole('button', { name: /Anmelden/ }).click()
}

async function signOut(page) {
  await page.getByRole('button', { name: /Abmelden/ }).click()
  await expect(page.getByRole('button', { name: /Anmelden/ })).toBeVisible()
}

async function authHeaders(page) {
  const token = await page.evaluate(() => sessionStorage.getItem('edusub_token'))
  expect(token).toBeTruthy()
  return { Authorization: `Bearer ${token}` }
}

test('cross-school applications are visible to teachers but manageable only by the owning school', async ({ page }) => {
  const date = new Date()
  date.setDate(date.getDate() + 7)
  const lessonDate = date.toISOString().slice(0, 10)
  const marker = `CrossSchool-${Date.now()}`

  // Wasgenring creates and owns the vacancy. No school_id is sent by the client.
  await signIn(page, 'wasgenring@e2e.test', 'E2eWasgenring123!')
  await expect(page.getByText('ADMIN-DASHBOARD · Primarschule Wasgenring')).toBeVisible()
  await page.getByRole('button', { name: /Neue Anfrage/ }).click()
  const createForm = page.locator('section.form-card form.request-form')
  await createForm.getByLabel('Datum').fill(lessonDate)
  await createForm.getByLabel('Klassenstufe').selectOption('3a')
  await createForm.getByLabel('Fach').selectOption({ label: 'E2E Mathematik' })
  await createForm.getByLabel('Von').fill('09:00')
  await createForm.getByLabel('Bis').fill('11:00')
  await createForm.getByLabel('Bemerkung (optional)').fill(marker)
  await createForm.getByRole('button', { name: /Anfrage erstellen/ }).click()
  await expect(page.getByText('Stellvertretungsanfrage erfolgreich erstellt', { exact: false })).toBeVisible()
  const wasgenringHeaders = await authHeaders(page)
  const ownedResponse = await page.request.get('/api/v1/requests/', { headers: wasgenringHeaders })
  expect(ownedResponse.status()).toBe(200)
  const request = (await ownedResponse.json()).find((item) => item.note === marker)
  expect(request).toBeTruthy()

  // Teachers see the school identity and can filter to that school's open vacancies.
  await signOut(page)
  await signIn(page, 'teacher@e2e.test', 'E2eTeacher123!')
  await expect(page.getByRole('heading', { name: 'Offene Stellvertretungen' })).toBeVisible()
  await page.getByRole('combobox', { name: 'Nach Schule filtern' }).selectOption(String(request.school_id))
  const listing = page.locator('.teacher-request').filter({ hasText: marker })
  await expect(listing).toContainText('Primarschule Wasgenring')
  await listing.getByRole('button', { name: /Bewerben/ }).click()
  await expect(listing.getByRole('button', { name: /Beworben/ })).toBeDisabled()
  await expect(page.getByText('● Ausstehend')).toBeVisible()
  const teacherResponse = await page.request.get('/api/v1/applications/my', { headers: await authHeaders(page) })
  expect(teacherResponse.status()).toBe(200)
  const application = (await teacherResponse.json()).find((item) => item.request_id === request.id)
  expect(application?.status).toBe('pending')

  // Volta cannot list or modify a Wasgenring request, nor approve its application.
  await signOut(page)
  await signIn(page, 'admin@e2e.test', 'E2eAdmin123!')
  await expect(page.getByText('ADMIN-DASHBOARD · Primarschule Volta')).toBeVisible()
  const voltaHeaders = await authHeaders(page)
  const voltaList = await page.request.get('/api/v1/requests/', { headers: voltaHeaders })
  expect((await voltaList.json()).some((item) => item.id === request.id)).toBe(false)
  const foreignUpdate = await page.request.patch(`/api/v1/requests/${request.id}`, {
    headers: voltaHeaders,
    data: { note: 'Unauthorized update attempt' },
  })
  expect(foreignUpdate.status()).toBe(404)
  const foreignApproval = await page.request.patch(`/api/v1/applications/${application.id}/approve`, {
    headers: voltaHeaders,
  })
  expect(foreignApproval.status()).toBe(404)

  // The owning school may approve and the vacancy becomes filled.
  await signOut(page)
  await signIn(page, 'wasgenring@e2e.test', 'E2eWasgenring123!')
  const approval = await page.request.patch(`/api/v1/applications/${application.id}/approve`, {
    headers: await authHeaders(page),
  })
  expect(approval.status()).toBe(200)
  expect((await approval.json()).status).toBe('approved')
  const filled = await page.request.get(`/api/v1/requests/${request.id}`, { headers: await authHeaders(page) })
  expect(filled.status()).toBe(200)
  expect((await filled.json()).status).toBe('filled')

  await signOut(page)
  await signIn(page, 'teacher@e2e.test', 'E2eTeacher123!')
  await expect(page.getByText('● Genehmigt').first()).toBeVisible()
  await expect(page.locator('.teacher-request').filter({ hasText: marker })).toHaveCount(0)
})
