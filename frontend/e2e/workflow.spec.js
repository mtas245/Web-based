import { test, expect } from '@playwright/test'

async function signIn(page, email, password) {
  await page.goto('/')
  await page.getByLabel('E-Mail-Adresse').fill(email)
  await page.getByLabel('Passwort', { exact: true }).fill(password)
  await page.getByRole('button', { name: /Anmelden/ }).click()
}

test('Admin → Lehrperson → Bewerbung → Löschkonflikt → Genehmigung', async ({ page }) => {
  const date = new Date()
  date.setDate(date.getDate() + 7)
  const lessonDate = date.toISOString().slice(0, 10)
  const marker = `E2E-${Date.now()}`

  await signIn(page, 'admin@e2e.test', 'E2eAdmin123!')
  await expect(page.getByRole('heading', { name: /Guten Tag/ })).toBeVisible()
  await page.getByRole('button', { name: /Neue Anfrage/ }).click()
  const createForm = page.getByRole('heading', { name: 'Neue Stellvertretungsanfrage' }).locator('..').locator('..').locator('form')
  await createForm.getByLabel('Datum').fill(lessonDate)
  await createForm.getByLabel('Klassenstufe').selectOption('3a')
  await createForm.getByLabel('Fach').selectOption({ label: 'E2E Mathematik' })
  await createForm.getByLabel('Von').fill('09:00')
  await createForm.getByLabel('Bis').fill('11:00')
  await createForm.getByLabel('Bemerkung (optional)').fill(marker)
  await createForm.getByRole('button', { name: /Anfrage erstellen/ }).click()
  await expect(page.getByText('Stellvertretungsanfrage erfolgreich erstellt', { exact: false })).toBeVisible()

  // Use the API to identify this test's request without guessing database IDs.
  const token = await page.evaluate(() => sessionStorage.getItem('edusub_token'))
  const response = await page.request.get('/api/v1/requests/', { headers: { Authorization: `Bearer ${token}` } })
  expect(response.ok()).toBeTruthy()
  const request = (await response.json()).find((item) => item.note === marker)
  expect(request).toBeTruthy()

  await page.getByRole('button', { name: /Abmelden/ }).click()
  await signIn(page, 'teacher@e2e.test', 'E2eTeacher123!')
  await expect(page.getByRole('heading', { name: 'Offene Stellvertretungen' })).toBeVisible()
  const listing = page.locator('.teacher-request').filter({ hasText: marker })
  await expect(listing).toBeVisible()
  await listing.getByRole('button', { name: /Bewerben/ }).click()
  await expect(listing.getByRole('button', { name: /Beworben/ })).toBeDisabled()
  await expect(page.getByText('● Ausstehend')).toBeVisible()

  await page.getByRole('button', { name: /Abmelden/ }).click()
  await signIn(page, 'admin@e2e.test', 'E2eAdmin123!')
  await expect(page.getByRole('heading', { name: /Guten Tag/ })).toBeVisible()

  // The application exists; even an admin may not delete the open request.
  page.once('dialog', (dialog) => dialog.accept())
  const adminRequests = page.getByRole('heading', { name: 'Stellvertretungsanfragen' }).locator('..').locator('..')
  // Only one request exists in this isolated test database.
  const matchingRow = adminRequests.locator('tbody tr').filter({ has: page.getByRole('button', { name: 'Löschen' }) }).first()
  await matchingRow.getByRole('button', { name: 'Löschen' }).click()
  await expect(matchingRow.getByRole('alert')).toBeVisible()
  const stillThere = await page.request.get(`/api/v1/requests/${request.id}`, {
    headers: { Authorization: `Bearer ${await page.evaluate(() => sessionStorage.getItem('edusub_token'))}` },
  })
  expect(stillThere.status()).toBe(200)

  const applications = page.getByRole('region', { name: 'Bewerbungsverwaltung' })
  await expect(applications.getByRole('button', { name: 'Genehmigen' })).toBeVisible()
  page.once('dialog', (dialog) => dialog.accept())
  await applications.getByRole('button', { name: 'Genehmigen' }).click()
  await expect(page.getByText('Bewerbung genehmigt', { exact: false })).toBeVisible()
  await expect(page.getByText('● Besetzt')).toBeVisible()
  await expect(applications.getByRole('button', { name: 'Genehmigen' })).toHaveCount(0)

  await page.getByRole('button', { name: /Abmelden/ }).click()
  await signIn(page, 'teacher@e2e.test', 'E2eTeacher123!')
  await expect(page.getByText('● Genehmigt')).toBeVisible()
  await expect(page.locator('.teacher-request').filter({ hasText: marker })).toHaveCount(0)
})
