# Milestone 3 — Frontend/API integration (HS26)

## Scope

First integrated **administrator** journey for the EduSub coaching session:

1. Admin signs in on the React web UI (`POST /api/v1/auth/login` with form-encoded credentials).
2. UI checks the session and admin role (`GET /api/v1/auth/me`).
3. UI retrieves subjects and grade levels (`GET /api/v1/subjects/`, `GET /api/v1/requests/grade-levels`).
4. Admin creates a substitute request (`POST /api/v1/requests/` with JSON).
5. UI retrieves saved requests again (`GET /api/v1/requests/`) and displays the persisted record.

The browser requests `/api/v1/...`; Vite proxies these paths to FastAPI on `127.0.0.1:8000` in development. FastAPI validates incoming data in Pydantic schemas, uses service logic for business rules and persists changes in the SQLModel/SQLite database.

The original Milestone 3 administrator slice was manually verified. A subsequent frontend iteration adds an initial teacher view for browsing open requests and applying; **that new teacher UI is not yet manually verified**. Administrator approval of teacher applications is still available through Swagger. See [frontend design decisions](FRONTEND-DECISIONS.md).

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
