# Milestone 3 — Frontend/API integration (HS26)

## Administrator action center and request filters

The administrator dashboard now includes a task-oriented overview showing open lessons scheduled within seven days, pending teacher applications and pending teacher-account approvals. These values come from existing API-backed lists; the overview links to the corresponding management sections. The request table also supports client-side searching and filtering by status and grade without introducing another endpoint.

This is a deliberately small extension of the integrated workflow, not a complete calendar or notification system. The design alternatives, user-centred rationale and API trade-offs are recorded in [Frontend Decisions](FRONTEND-DECISIONS.md). Two new unit tests cover date selection and combined filters; the frontend suite now reports **9 passed** and its production build succeeds. **Team-confirmed local Playwright run, 18 November 2026: all 3 tests passed in 11.2 seconds**, including the new action-center and request-filter scenario. This is a team-reported terminal result, not a CI run. A separate manual usability review of the new feature is still outstanding.

Suggested manual checks (not yet individually reported as completed):

- [ ] Create an open request within the next seven days; see its grade, subject and date in the action center.
- [ ] Apply as a teacher; after returning as administrator, check that the pending-application count reflects the saved application.
- [ ] Use the three links to jump to the appropriate admin sections.
- [ ] Search by subject or note, apply status/grade filters and reset them.
- [ ] Confirm that filtering does not change the global dashboard statistics.

## Responsive admin UI: implementation and outstanding verification

The initial responsive refinement uses CSS Grid/Flexbox and media queries without introducing Bootstrap or Tailwind. Statistics, forms and action controls adapt to smaller screens; on narrow phones the main request table is presented as labelled cards. Other admin tables remain horizontally scrollable. The table's column headers are retained for assistive technology and focus indicators remain visible. See [frontend decisions](FRONTEND-DECISIONS.md) for the alternatives and trade-offs.

An additional Playwright viewport scenario covers 1440 px, 768 px and 375 px widths, including a populated request list. **Team-confirmed local Windows run, 18 November 2026: `2 passed`** (the application-workflow E2E test and the new responsive-layout test). The team supplied the passing summary, without a full transcript, screenshots or individual test timings. A manual visual, keyboard and touch review on mobile remains outstanding; automated viewport checks do not establish complete usability or accessibility.

**Documentation language:** Interface action names in this document are given in English; the currently implemented UI still displays German labels. The documented API endpoints, status codes, and test results are unchanged.

## Latest extension: Admin CRUD through the web interface

The admin request table offers **Edit** (`PATCH /api/v1/requests/{id}`) and **Delete** (`DELETE /api/v1/requests/{id}`) actions. The edit form is pre-filled with saved values, validates the time range and displays API errors. Both operations are followed by a fresh API read. Requests that are no longer open have no edit/delete buttons; the backend independently enforces these restrictions. Deletion requires confirmation, and attempts to delete a request with applications should return HTTP 409.

**Manual team confirmation (16 November 2026):** The team reported that all four CRUD checks in the agreed UI test plan passed. These are local browser observations; screenshots and exact HTTP status codes were not supplied.

- [x] Edit an open request, save it and see the updated values in the list (team-reported pass).
- [x] Enter `12:00–08:00` in the edit form and see a validation error without saving (team-reported pass).
- [x] Delete an open request **without applications** and confirm that it disappears from the list (team-reported pass).
- [ ] Attempt to delete an open request **with applications**: the backend should display an error and preserve the request (manual check still outstanding).
- [x] Open a filled request and confirm that no Edit/Delete actions are available (team-reported pass).

**Result: 4/4 executed manual CRUD checks passed.** The additional *manual* deletion-conflict check with existing applications is still outstanding and must not be marked as manually passed; automated tests now cover it. For submission, the team should add redacted screenshots and, where useful, the actual HTTP statuses from the browser's Network tab.

**Next priorities after the successful E2E test:** (1) responsive-layout and accessibility reviews, (2) further negative browser scenarios and focused automated-test coverage, (3) recording actual team contributions and classroom demonstrations. Broader product features remain lower priority than reliable technical integration.

### Automated integration and browser tests (new iteration)

- **Backend regression evidence:** `backend/tests/test_request_workflow.py::test_request_with_pending_application_cannot_be_deleted` creates a request and application, attempts deletion, checks HTTP **409**, and verifies that both records remain. Including this test, **14 backend tests passed** locally (31 deprecation warnings).
- **Browser scenario:** `frontend/e2e/workflow.spec.js` covers admin login → request creation → teacher login → application → forbidden deletion attempt → application approval → `filled` and `approved` status checks. Playwright starts FastAPI and Vite automatically. The dedicated test server (`backend/tests/e2e_server.py`) uses a temporary SQLite database with fictional accounts; it does not modify the team's regular EduSub database.
- **Execution evidence:** Seven frontend unit tests passed, and the Vite production build was successful. Chromium could not launch in the assistant's sandbox because of `socket() failed: Operation not permitted`. The first Windows run timed out after 45 seconds due to an incorrect form selector; this was fixed in the test script. **The team member confirmed a successful repeat run on 16 November 2026: `1 passed (11.1s)`, including 4.4 seconds for the scenario.** This is team-supplied terminal evidence, not a CI run or screenshot archive.

**Local browser test (Windows / PowerShell):** Python 3.12 and the backend dependencies must be available in the active environment. Activate the virtual environment in `backend`, run `python -m pip install -r requirements.txt`, and then run these commands from `frontend`:

```powershell
npm install
npx playwright install chromium
npm run test:e2e
```

If the frontend terminal is a new PowerShell session, first run `..\backend\.venv\Scripts\Activate.ps1`. The test starts its own servers at **127.0.0.1:18000** (backend) and **127.0.0.1:15173** (Vite); both ports must be free. Test passwords belong only to disposable local accounts. The successful Windows repeat run is recorded above.

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

1. On the login screen select **Register as a teacher**, use a fresh fake email and a test password, then submit.
2. Confirm the message that approval is required. Logging in before approval should show an error.
3. Sign in as administrator, find the account under **Approve teachers**, and approve it.
4. Sign out, then sign in as the new teacher. The teacher dashboard should open.
5. Optional error test: register the same email twice; the second attempt must display a backend error without creating another account.

**Team confirmation (16 November 2026):** The user reports that the complete registration → administrator approval → login as newly approved teacher workflow works as expected in the local browser. Exact HTTP response codes and redacted screenshots were not supplied for this manual run; the automated backend test independently verifies expected 201, 403, 200 and 200 statuses. The optional duplicate-email negative case has not been separately confirmed.

### End-to-end browser verification — next exercise

1. Admin creates a fresh open request.
2. Approved teacher logs in, applies and sees `pending` under "My applications".
3. Admin signs in and sees the application under "Pending applications".
4. Admin chooses **Approve**, confirms and sees the request status change to `filled`.
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

### Cross-school extension (20 November 2026; code-level verification)

EduSub now explicitly targets multiple primary schools rather than a single site. Five Basel school names are included in an idempotent demonstration seed script; **no real school is affiliated with this prototype**. A `School` entity, request ownership, legacy SQLite compatibility migration, school-admin request/application isolation, public teacher discovery across schools, a teacher school filter with five-item pagination, and a dedicated platform-admin teacher-approval view have been implemented. The architectural rationale and alternative options are recorded in [`MULTI-SCHOOL-ARCHITECTURE.md`](MULTI-SCHOOL-ARCHITECTURE.md).

**Automated verification:** 17 backend Python tests passed, including cross-school access denial and legacy migration tests. Nine frontend Node tests passed; the frontend production build succeeded. These are development-environment results, not team-confirmed multi-account browser tests. **Pending:** manually demonstrate two separate school-admin accounts, cross-school teacher search/application, platform-wide teacher approval, and a fresh Playwright run. Existing database files should be backed up before starting the updated backend.

- Teacher-facing screens for browsing and applying, as well as administrator approval in the UI, are pending.
- Only the admin login/create/list journey is included here; edit/delete remain available through the API but are not yet available in this UI.
- Authentication token is stored in browser `sessionStorage` for this local demo. Review storage strategy and additional security requirements before final submission.
- Additional automated frontend/API integration tests, mobile browser checks, and error-state review should follow.
- Backend security issues noted in `MILESTONE-1-2.md` remain open. Do not use real credentials or confidential teacher documents in screenshots or demo recordings.
- The project is currently on a fork branch. Coordinate merging into the group repository and make sure the lecturer has access to the committed Milestone 3 snapshot before coaching.


### Multi-school manual integration and authorization tests — team report, 20 November 2026

| Test | Expected | Team-reported result | Evidence |
| --- | --- | --- | --- |
| Wasgenring admin creates a substitute request | Request is saved under Wasgenring | **Passed** | Created in React and displayed in that school's overview. |
| Volta admin opens their dashboard | Wasgenring request is absent | **Passed** | School-specific listing verified in the UI. |
| Approved teacher browses available requests | Cross-school list and school filter work | **Passed** | Teacher verified the Wasgenring vacancy and the school selector in React. |
| Volta admin PATCHes a Wasgenring request ID | HTTP 404; no cross-school update | **Passed** | Swagger returned **404 Request not found** for a valid partial update body. |

**Additional API-validation observation (not an authorization result):** An initial Swagger PATCH attempt produced HTTP **422**, because the auto-generated body contained `"grade_level": "string"` and `"time_slot": "string"`. Those values violate the Pydantic grade-level and `HH:MM-HH:MM` validators. After sending only `{"note": "Unauthorized cross-school modification test"}`, the actual cross-school authorization check returned HTTP 404.

**Evidence limits:** These are team-reported manual checks, not independently recorded browser traces. The 404 response is consistent with the backend authorization policy. The next manual test should verify that a Volta admin cannot approve a pending application for a Wasgenring vacancy, while the Wasgenring admin can approve it and the request transitions to `filled`. Do not enter real teacher details or passwords in evidence screenshots.


### Cross-school application approval — team-confirmed manual test, 20 November 2026

| Operation | Expected outcome | Team-reported result |
| --- | --- | --- |
| Approved teacher applies to an open Wasgenring request | Application is created; status `pending` | **Passed** |
| Volta admin attempts to approve that Wasgenring application | API rejects cross-school approval with HTTP 404 | **Passed** |
| Wasgenring admin approves the same pending application | API returns HTTP 200 | **Passed** |
| Request is retrieved after approval | Request status changes to `filled` | **Passed** |

**Assessment relevance:** This demonstrates an integrated cross-school journey and a negative authorization case, connecting React, the documented FastAPI REST API, shared service/business rules and SQLModel persistence. The results were confirmed by a team member through the manual workflow; no independent network capture or browser automation run was provided for this session. The next priority is an automated regression test using distinct authenticated school administrators, followed by review of remaining usability and submission-readiness tasks.

### Multi-school automated browser regression (20 November 2026)

Added `frontend/e2e/multi-school.spec.js` and expanded the **disposable** E2E database fixture (`backend/tests/e2e_server.py`) to seed five school names, two separate school administrators and one approved teacher. All accounts, passwords and vacancies in this fixture are fictional and are not connected to production or the developer's `edusub.db`.

The Playwright scenario now checks: Wasgenring vacancy creation in React; teacher school filtering and application; Volta's inability to list, update or approve Wasgenring records (`404`); Wasgenring's successful approval (`200`); the request's transition to `filled`; and the teacher's approved application status. The test uses actual authentication tokens from each UI login and discovers record IDs from API responses rather than hardcoding them.

**Verification status:** The test file passed JavaScript syntax checking, the E2E server reached FastAPI startup, and all 17 backend unit/integration tests passed. Browser completion is **not yet confirmed** in the assistant's restricted environment. A group member must run the full Playwright suite locally and record the result before claiming the automated browser test passed.

**Design rationale:** A disposable database and separate authenticated accounts make the security regression reproducible and protect existing test data. Direct API calls within the browser journey test authorization independently of frontend filtering, while React interactions demonstrate the real user-facing integration. This is complementary to FastAPI's faster TestClient security tests, not a replacement for them.

**Playwright execution feedback (20 November 2026):** The first team-run cross-school browser test failed at `multi-school.spec.js` during the final Wasgenring login: `authHeaders()` read `sessionStorage` before the asynchronous login had stored the access token (`Received: null`). Earlier scenario steps had proceeded up to the attempted owning-school approval. The login helper now explicitly waits for the token before returning. This is a **test synchronization correction**, not an authorization-rule change. JavaScript syntax checking passed after the correction; the team must rerun the browser test and report whether it passes.


**Playwright retest — team confirmation, 20 November 2026:** After pulling the login synchronization fix, the group member ran `npx playwright test e2e/multi-school.spec.js` locally and reported **1 passed in 7.3 seconds**. This confirms the automated cross-school browser scenario in the team's Windows development environment. The prior failure and corrective action remain documented above as regression-testing evidence. The next development priority is usability improvements to the substitute-request overview, followed by broader submission-readiness checks.
