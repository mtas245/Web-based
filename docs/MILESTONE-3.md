# Milestone 3 — Frontend/API integration (HS26)

## Aktuelle Erweiterung: Admin-CRUD über die Weboberfläche

Die Admin-Tabelle erhält Aktionen zum **Bearbeiten** (`PATCH /api/v1/requests/{id}`) und **Löschen** (`DELETE /api/v1/requests/{id}`). Ein Bearbeitungsformular übernimmt vorhandene Felder, prüft den Zeitraum und zeigt API-Fehler an. Nach beiden Operationen werden die Daten erneut über die API gelesen. Nicht offene Anfragen zeigen keine Bearbeiten-/Löschen-Buttons; das Backend erzwingt die Regeln unabhängig davon. Löschen wird mit einem Bestätigungsdialog abgesichert; bei vorhandenen Bewerbungen ist ein HTTP-409-Konflikt zu erwarten.

**Manuelle Bestätigung durch das Team (16. November 2026):** Alle vier im gemeinsamen UI-Testplan ausgeführten CRUD-Prüfungen wurden vom Team als erfolgreich gemeldet. Diese Ergebnisse stammen aus einem lokalen Browserdurchlauf; Screenshots und genaue HTTP-Statuscodes wurden nicht mitgeliefert.

- [x] Offene Anfrage bearbeiten, speichern und anschliessend geänderte Werte in der Liste sehen (Teamangabe: bestanden).
- [x] Mit `12:00–08:00` im Bearbeitungsformular eine sichtbare Fehlermeldung erhalten; keine Änderung speichern (Teamangabe: bestanden).
- [x] Eine offene Anfrage **ohne Bewerbungen** löschen und ihr Verschwinden aus der Liste beobachten (Teamangabe: bestanden).
- [ ] Eine offene Anfrage **mit Bewerbungen** zu löschen versuchen: sichtbare Backend-Fehlermeldung, Anfrage bleibt bestehen.
- [x] Eine besetzte Anfrage betrachten: keine Bearbeiten-/Löschen-Aktion sichtbar (Teamangabe: bestanden).

**Ergebnis: 4/4 ausgeführte manuelle CRUD-Tests bestanden.** Der zusätzliche Konflikttest für das Löschen einer Anfrage mit bestehenden Bewerbungen ist weiterhin offen und darf nicht als bestanden ausgegeben werden. Für die Abgabe sollten passende, anonymisierte Screenshots und gegebenenfalls die tatsächlichen HTTP-Statuscodes aus dem Netzwerk-Tab ergänzt werden.

**Nächste Prioritäten:** (1) Konflikttest für `DELETE` bei vorhandenen Bewerbungen, (2) automatisierter Ende-zu-Ende-Test des gesamten Admin-/Lehrpersonenprozesses, (3) Responsive- und Accessibility-Prüfung, (4) Dokumentation von Teambeiträgen und tatsächlicher Unterrichtsdemonstration. Die fachliche Erweiterung bleibt bewusst nach der technischen Integration priorisiert.

### Automatisierte Integrations- und Browser-Tests (neue Iteration)

- **Backend-Regressionsnachweis:** `backend/tests/test_request_workflow.py::test_request_with_pending_application_cannot_be_deleted` erstellt eine Anfrage und eine Bewerbung, versucht die Anfrage zu löschen und prüft HTTP **409** sowie das Fortbestehen beider Datensätze. Mit diesem Test: **14 Backend-Tests bestanden** (lokal, 31 Deprecation-Warnungen).
- **Browser-Test eingerichtet:** `frontend/e2e/workflow.spec.js` beschreibt den Ablauf Admin-Login → Anfrage erstellen → Lehrer-Login → bewerben → unzulässigen Löschversuch prüfen → Bewerbung genehmigen → Status `filled` und `approved` kontrollieren. Playwright startet Backend und Vite automatisch. Der Backend-Testserver (`backend/tests/e2e_server.py`) verwendet eine eigene temporäre SQLite-Datenbank mit ausschliesslich fiktiven Konten; die produktive/lokale EduSub-Datenbank wird nicht verändert.
- **Ausführungsstatus:** Die 7 Frontend-Unit-Tests sind bestanden; der Vite-Build wurde geprüft. Ein vollständiger Playwright-Durchlauf war in der Entwicklungs-Sandbox **nicht möglich**, weil der dortige Chromium-Prozess mit `socket() failed: Operation not permitted` beendet wurde. Deshalb ist der neue Browser-E2E-Test **noch nicht als bestanden** dokumentiert. Er muss unter Windows ausgeführt und bei Bedarf angepasst werden.

**Lokaler Browser-Test (Windows / PowerShell):** Python 3.12 und die Backend-Abhängigkeiten müssen in der aktiven Umgebung verfügbar sein. In `backend` die virtuelle Umgebung aktivieren und `python -m pip install -r requirements.txt` ausführen; danach im Verzeichnis `frontend`:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

Falls der Frontend-Terminal eine eigene neue PowerShell-Session ist, dort zuerst `..\backend\.venv\Scripts\Activate.ps1` aufrufen. Der Test startet seine Server selbst auf **127.0.0.1:18000** (Backend) und **127.0.0.1:15173** (Vite); diese Ports müssen frei sein. Testpasswörter gehören ausschliesslich zu wegwerfbaren lokalen Accounts. Ein erfolgreicher Browserlauf ist mit dem tatsächlich angezeigten Testresultat nachzutragen.

## Scope

First integrated **administrator** journey for the EduSub coaching session:

1. Admin signs in on the React web UI (`POST /api/v1/auth/login` with form-encoded credentials).
2. UI checks the session and admin role (`GET /api/v1/auth/me`).
3. UI retrieves subjects and grade levels (`GET /api/v1/subjects/`, `GET /api/v1/requests/grade-levels`).
4. Admin creates a substitute request (`POST /api/v1/requests/` with JSON).
5. UI retrieves saved requests again (`GET /api/v1/requests/`) and displays the persisted record.

The browser requests `/api/v1/...`; Vite proxies these paths to FastAPI on `127.0.0.1:8000` in development. FastAPI validates incoming data in Pydantic schemas, uses service logic for business rules and persists changes in the SQLModel/SQLite database.

The original Milestone 3 administrator slice was manually verified. A subsequent frontend iteration adds an initial teacher view for browsing open requests and applying; the teacher view has since been manually verified as described below. Administrator approval of teacher applications is also available through Swagger. See [frontend design decisions](FRONTEND-DECISIONS.md).

**Subsequent manual confirmation (16 November 2026):** A team member successfully logged in as an approved teacher, viewed open requests, used the class filter, applied for a request and saw the resulting `pending` application. The class filter intentionally offers only classes currently present among open requests. Filled/non-open requests are absent from the teacher list, so there is no application button for them; this is expected.

**New frontend iteration (awaiting manual verification):** `frontend/src/AdminApplications.jsx` shows pending applications, teacher names and their target request. Administrators can approve/reject after a confirmation prompt. The component calls `PATCH /api/v1/applications/{id}/approve` or `/reject`, then re-reads pending applications and requests from the API. On approval the backend sets the request to `filled` and rejects competing pending applications. The React build succeeds; the new administrative UI actions are **not yet manually verified**.

**Additional implementation (subsequently browser-tested):** A public registration screen now submits `FormData` to `POST /api/v1/auth/register`. New teacher accounts remain pending until the administrator approves them through `GET /api/v1/teachers/pending` and `PATCH /api/v1/teachers/{id}/approve` from a new admin section. A new backend test verifies registration (201), denied login before approval (403), approval (200) and login after approval (200). The test suite reports **13 passed** locally; the frontend build and existing 7 validation tests also pass. Document upload is deliberately excluded from this first UI because the backend's handling of personal documents needs a security review.

### Registration and approval browser test – confirmed by team

1. On the login screen select **Als Lehrperson registrieren**, use a fresh fake email and a test password, then submit.
2. Confirm the message that approval is required. Logging in before approval should show an error.
3. Sign in as administrator, find the account under **Lehrpersonen freigeben**, and approve it.
4. Sign out, then sign in as the new teacher. The teacher dashboard should open.
5. Optional error test: register the same email twice; the second attempt must display a backend error without creating another account.

**Team confirmation (16 November 2026):** The user reports that the complete registration → administrator approval → login as newly approved teacher workflow works as expected in the local browser. Exact HTTP response codes and redacted screenshots were not supplied for this manual run; the automated backend test independently verifies expected 201, 403, 200 and 200 statuses. The optional duplicate-email negative case has not been separately confirmed.

### End-to-end browser verification — next exercise

1. Admin creates a fresh open request.
2. Approved teacher logs in, applies and sees `pending` under "Meine Bewerbungen".
3. Admin signs in and sees the application under "Offene Bewerbungen".
4. Admin chooses **Genehmigen**, confirms and sees the request status change to `filled`.
5. Teacher signs in again and sees the application status `approved`.
6. Confirm the filled request is no longer available for new applications.
7. Negative check: an already decided application must not be approved a second time (backend should reject with 409); do not falsify results before execution.

Capture redacted HTTP status/response evidence from browser DevTools → Network and document the actual observed results.

## Local run (two terminals)

Prerequisites: Python 3.12, Node.js 20.19+ or 22.12+ (Node 24 also works), npm.

Terminal A — from `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

If `.venv` does not yet exist: `py -3.12 -m venv .venv`. Create an admin using the documented local admin script if needed. The database must contain subjects: in Swagger (`http://127.0.0.1:8000/docs`), authorize as an admin and run `POST /api/v1/subjects/seed` once.

Terminal B — from `frontend/`:

```powershell
npm install
npm run dev
```

Open **http://127.0.0.1:5173** and sign in with the local admin account. The backend is on `http://127.0.0.1:8000`.

## Confirmed manual frontend integration tests — 16 November 2026

The following results were **reported and confirmed by a team member** after running EduSub locally. They are manual browser observations, not automated end-to-end test results. The assistant did not independently inspect browser network traces or the SQLite database.

| Test | Reported result | Conclusion |
| --- | --- | --- |
| EduSub login page loads | Successful | React/Vite frontend is accessible |
| Administrator signs in with valid credentials | Successful | Login and authenticated UI transition work |
| Dashboard displays existing requests | Successful | Frontend retrieves request data from the API |
| Administrator creates a new substitute request | Successful | Browser submission through the API works |
| Newly created request appears in the overview | Successful | The UI re-reads the created request from the backend |

**Overall: 5/5 reported manual tests successful.** This supports the central Milestone 3 integrated administrator journey. The final database persistence is supported by the application architecture and re-read behaviour, but has not been separately verified by directly inspecting SQLite during this test.

### Negative frontend tests — team report, 16 November 2026

| Test | Team-reported result | Interpretation / next action |
| --- | --- | --- |
| Login with correct email and wrong password | **Passed** | Error handling and denied access behaved as expected according to the team member. |
| Create request with invalid time range (12:00–08:00) | **Failed** | Expected visible validation error and no creation were **not confirmed**. Exact observed UI behaviour and HTTP response have not been supplied; investigate before claiming a fix. |

**Further investigation / pending correction (16 November 2026):** The team clarified that the invalid request was actually created. Code inspection shows that the frontend currently sends `time_slot: null` if either time input is blank, which the API intentionally permits because time slots are optional. This is a possible explanation but the exact browser request was not captured, so the root cause is not conclusively confirmed. The frontend fix is now **published on `feature/milestone1-2`**: it checks both time inputs together, rejects inverted/equal intervals before POST and displays an inline error. Seven frontend unit tests pass. A published backend regression test verifies that `12:00-08:00` returns HTTP 422 with no database insertion (12 Python tests passing locally). **Manual confirmation received:** After pulling the updated frontend, a team member confirmed that the invalid time-range test now behaves as expected: the frontend displays the validation error and does not create the request. This is user-reported manual evidence, not independently captured browser network evidence.

**Initial investigation:** The current backend `schemas/request.py` rejects time ranges with end <= start via `validate_time_slot`, which should yield HTTP 422. The frontend sends the `HH:MM-HH:MM` string to the API when both times are filled in and renders any API error in an alert above the request form. This code-level inspection does not explain the reported failure conclusively. Inspect browser Network → POST `/api/v1/requests/` status and request body, whether a record was created, and whether the error appears out of view. Do not classify this test as passed until repeated successfully.

### Retest result — team-confirmed

After the corrected frontend was published, the same invalid-time scenario (`12:00–08:00`) was tested again. The team member reported that the validation message appeared and the request was not created. **Retest passed.** The original failing run remains recorded above as an identified-and-corrected defect. Seven frontend validation tests and 12 backend tests passed in the assistant's development environment; the live browser confirmation is reported by the team member.

## Coaching demo / verification checklist

- [ ] Start the backend and verify `GET /` displays `EduSub API is running`.
- [x] Start the frontend and load the login page (team-confirmed).
- [x] Show incorrect password → visible authentication error; correct admin login → dashboard (team-confirmed).
- [x] Show existing requests in the dashboard (team-confirmed; statistics calculation not separately checked).
- [x] Create a valid request from the frontend (team-confirmed; exact field values not recorded).
- [x] Confirm a newly created request appears in the dashboard (team-confirmed).
- [ ] Confirm the same request appears through Swagger `GET /api/v1/requests/` and, if helpful, inspect the SQLite persistence.
- [x] Retest invalid time range: corrected UI shows a validation error and does not submit/create the request (team-confirmed). This is **client-side** rejection; HTTP 422 is independently covered by the automated backend regression test, not by this browser attempt.
- [ ] Explain browser → Vite proxy → FastAPI router → service → SQLModel → SQLite → JSON response.
- [ ] Run `python -m pytest -q` from the updated backend and capture results (local unpublished test run: 12 passed, 20 warnings).
- [ ] Record actual team contributors, coaching feedback, and outstanding integration tasks.

Checked items reflect team-confirmed manual browser results; unchecked items remain pending and must not be reported as verified. The successful admin login is confirmed, but the incorrect-password case in the combined login checklist is still pending.

## Known limitations / next iteration

- Teacher-facing screens for browsing and applying, as well as administrator approval in the UI, are pending.
- Only the admin login/create/list journey is included here; edit/delete remain available through the API but are not yet available in this UI.
- Authentication token is stored in browser `sessionStorage` for this local demo. Review storage strategy and additional security requirements before final submission.
- Additional automated frontend/API integration tests, mobile browser checks, and error-state review should follow.
- Backend security issues noted in `MILESTONE-1-2.md` remain open. Do not use real credentials or confidential teacher documents in screenshots or demo recordings.
- The project is currently on a fork branch. Coordinate merging into the group repository and make sure the lecturer has access to the committed Milestone 3 snapshot before coaching.
