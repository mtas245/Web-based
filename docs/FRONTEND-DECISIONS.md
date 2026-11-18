# EduSub frontend: Course concepts and justified design decisions (HS26)

## Connection to the course material

Source: *07-Frontend-and-API-Integration-HS26*, especially slides 8–13 (HTML, CSS, JavaScript and events), 48–55 (`try/catch/finally`, `fetch`, JSON and network requests), and 57–63 (frontend alternatives and the integrated workflow). The supplementary materials *07A-Static-to-Jinja-HS26* and *07B-Frontend-Alternatives-HS26* present alternative approaches; they are optional.

| Course concept | Implementation in EduSub | Rationale |
| --- | --- | --- |
| HTML structure and accessible forms | Semantic `<form>`, `<label>`, `<input>`, `<select>`, `<button>` elements and tables in React components | Browsers can interpret input fields correctly; structured interfaces are easier to use. |
| CSS and responsive layouts | `frontend/src/style.css` with flexible layouts and media queries | Desktop and mobile devices need different arrangements. |
| JavaScript events | `onSubmit`, `onClick`, `onChange` | User interactions trigger explicit, traceable operations. |
| State management | React `useState` for forms, loading states, lists and messages | HTTP responses change UI data; React keeps the view synchronized with state. |
| HTTP/JSON API calls | `frontend/src/api.js` uses `fetch`, `JSON.stringify`, HTTP methods and bearer tokens | Frontend and backend remain separate; the same FastAPI endpoints can be tested independently through Swagger. |
| Error handling | `try/catch/finally`, visible alerts, disabled buttons during requests | Invalid input and API errors are understandable to users. |
| Evidence of persistence | `POST /requests/` or `POST /requests/{id}/apply`, followed by another `GET` | A success message alone does not prove persistence; the saved server-side state is fetched again. |
| Data and permissions | Admin views call admin endpoints; teacher views use teacher-specific endpoints | A role-specific UI improves usability, but authorization must still be enforced by the backend. |
| Components | Separate `TeacherDashboard.jsx` for the teacher workflow | Responsibilities are easier to maintain, extend and test. |
| CRUD methods | `RequestRow.jsx` sends `PATCH` for changes and `DELETE` to remove requests | HTTP methods express intent. `PATCH` updates selected fields; a successful `DELETE` returns HTTP 204 without a JSON body. |

## Why React/Vite instead of Jinja or a static page?

- **Static page:** Useful for early sketches, but without an API connection it cannot persist substitute requests.
- **Jinja2:** Explicitly permitted by the course and suitable for a smaller application with conventional page and form submissions. For EduSub, adopting it now would require a second rendering approach in FastAPI and a rewrite of the working React frontend.
- **React with the browser API:** EduSub needs repeatedly refreshed lists, changing statuses and distinct role-specific views. The existing React/Vite frontend already communicates with the documented REST API. We therefore retain it. **React is a deliberate project decision, not a module requirement.**
- **NiceGUI:** The original Advanced Programming EduSub provided the domain foundation. For this module, we want the boundaries between independent browser frontend, REST API, services and persistence to be visible.

## Architecture and integration sequence

1. The browser opens the React application on port 5173.
2. In local development, Vite forwards `fetch('/api/v1/requests/open')` to FastAPI on port 8000 (`frontend/vite.config.js`).
3. FastAPI verifies the bearer token and teacher role; services and the database then return only open requests.
4. React renders the list and lets teachers apply through `POST /api/v1/requests/{id}/apply`.
5. After HTTP 201, React reloads open requests and the teacher's own applications (`GET /api/v1/applications/my`).
6. API errors are displayed and are not treated as successful applications. The backend independently enforces permissions and business rules.

The original admin demo (login → create request → retrieve saved request) was **manually confirmed**. The teacher demo was also tested using an approved teacher account.

**Historical status note, 16 November 2026:** The teacher demo was manually verified (login, open requests, grade filter, application and `pending` status). The filter intentionally lists only grades with currently open requests; filled requests have no application action. The additional `AdminApplications.jsx` component calls `GET /applications/pending`, `GET /teachers/` and `PATCH /applications/{id}/approve|reject`, then reloads stored data. At the time of this note, the new admin UI had not yet been manually verified; a later Playwright end-to-end test now covers the approval path.

## Browser evidence for demonstrations and submission

1. Open the browser's DevTools → Network tab.
2. Sign in as an approved teacher; inspect `GET /api/v1/auth/me` and `GET /api/v1/requests/open`.
3. Select an open substitute request and click **Apply** (the actual UI label is currently in German).
4. Check `POST /api/v1/requests/{id}/apply` (expected 201) and the subsequent `GET /api/v1/applications/my`.
5. The teacher's application should appear in the UI; applying to the same request again must not create a duplicate.
6. Demonstrate a negative case, such as an unapproved account or duplicate application. Mark **expected** HTTP statuses as **confirmed** only after observing them.

Never store real passwords, JWTs or personal teacher documents in screenshots or commits.

## Limitations and further work

### Task-oriented administrator dashboard and request filtering

**User need:** The earlier overview showed totals and data tables, but administrators still had to scan several sections to identify upcoming uncovered lessons, pending applications and teacher approvals. A useful dashboard should make the next actions recognizable without hiding the underlying data.

**Chosen solution:** `AdminActionCenter.jsx` presents (1) open substitute requests scheduled within the next seven calendar days, (2) pending applications and (3) pending teacher registrations. Its links jump to existing page sections. Upcoming lessons are derived from the requests already loaded by the admin API. The application and teacher-approval components report their currently loaded counts to the parent via React state callbacks, so no extra HTTP requests or new backend endpoints are required. `dashboard-utils.js` contains pure date and filter functions with unit tests.

The request table now has a text search and status/grade filters. For the modest local dataset, `filterRequests` filters the already retrieved list in React; the server still owns authorization, persistence and business rules. Summary statistics and task counts are based on **all** records, not the filtered subset. Data is refreshed after existing create/update/delete/approval actions.

| Alternative | Advantages | Trade-off / decision |
| --- | --- | --- |
| Full calendar | Rich scheduling and date navigation | More complexity and new UI dependencies; deferred |
| Dedicated backend task-summary endpoint | Efficient for large datasets and multiple clients | Extra API contract and backend work; unnecessary for current scope |
| Duplicate API calls within the overview | Independent component | Avoided because existing admin components already fetch pending records |
| Client-side summary and filters | Fast to implement, uses existing REST contracts, easy to test | **Selected** for the current dataset; server-side filtering would be better at large scale |

**Course concepts:** User-centred design, visibility of system status, recognition rather than recall, React props/state, conditional rendering, functional data transformation and API-first separation of concerns. No notification or scheduling job has been introduced: the overview is a live summary when the page loads or the underlying data is refreshed, not a push-notification service.

**Verification:** Pure-function tests and the production frontend build are part of this change. A new Playwright scenario checks the task overview, filtering and reset behavior with an isolated seeded backend; its **local browser result is still pending team confirmation**.

### Responsive administrator dashboard (iteration after Milestone 3 integration)

**Problem:** The initial admin layout used a fixed desktop sidebar, three statistic columns, and wide tables. At phone widths, crowded controls and horizontal scrolling reduced readability, particularly for request editing.

**Chosen implementation:** Keep native CSS Grid and Flexbox and add focused media queries in `frontend/src/responsive-admin.css`. At widths up to 720 px, statistic cards stack vertically, forms and action buttons adapt to available space, and the top bar uses a compact layout. At widths up to 600 px, **only the main substitute-request table** becomes individual cards. Each cell retains a `data-label` for a visible field name; the actual table headers remain in the document for assistive technologies. Other administration tables retain horizontal scrolling for now. Visible keyboard focus and reduced-motion preferences are also supported.

**Alternatives considered:**

| Alternative | Benefit | Why it was not selected for this iteration |
| --- | --- | --- |
| Bootstrap | Ready-made responsive grid and components | Additional CSS conventions and dependency for a small existing UI |
| Tailwind CSS | Flexible utility classes | New build configuration and a larger markup refactor without a clear current benefit |
| Make every table horizontally scrollable | Smallest code change | The request table's frequent actions remain difficult to read and use on phones |
| CSS Grid, Flexbox and media queries | Native browser support, no new framework | **Selected:** matches existing code and the course's frontend concepts |

**Trade-off and evidence:** The new card presentation requires a separate responsive stylesheet and `data-label` attributes. It avoids changing API behavior or replacing React components. A Playwright viewport regression scenario was added and the team confirmed a successful local Windows run on **18 November 2026 (`2 passed`, including the existing application workflow test)**. A manual mobile-browser usability and keyboard/touch review is still needed; the automated result is not proof of full accessibility.

**Course connection:** CSS box model, responsive layouts, Grid/Flexbox, media queries, semantic HTML, progressive enhancement and user-centred design. Verification should include a 1440 px desktop, 768 px tablet and 375 px mobile viewport, plus keyboard and touch interactions.

### Administrator: editing and deleting requests

The admin request table provides **Edit** and **Delete** actions for open requests. Editing pre-fills an HTML form with saved values. `validateTimeRange` checks the lesson times before submission; FastAPI also validates the payload. `PATCH /api/v1/requests/{id}` updates the record, and React then reloads the full list through `GET /requests/`. Deletion requires a `window.confirm` confirmation and sends `DELETE /api/v1/requests/{id}`; the API client handles HTTP 204 without parsing JSON.

**Decision:** We use `PATCH` rather than `PUT` because we are updating fields of an existing resource. Displaying a button does not grant permission: the backend rejects edits to non-open requests and deletion when applications exist (HTTP 409 conflict). The UI hides these actions for filled requests, displays server-side errors and disables buttons while requests are in progress. The logic lives in a separate component rather than enlarging `main.jsx`.

**Evidence, 16 November 2026:** The team confirmed four successful manual browser checks: edit an open request, reject an invalid time range, delete an open request without applications, and hide editing/deletion controls for filled requests. The separate **manual** HTTP-409 deletion-conflict scenario was not performed; automated API and Playwright tests cover this rule. The seven frontend unit tests and the build also passed.

**Test strategy:** Pydantic/FastAPI tests check validation, business rules and database state quickly in isolation. An additional API test verifies that a request with an application cannot be deleted (HTTP 409, both records preserved). Playwright adds actual browser clicks and state changes across React, the Vite proxy, FastAPI and SQLite, using fictional accounts and a temporary database. After fixing a brittle form selector, a team member confirmed a successful Windows browser test on 16 November 2026 (`1 passed`, 11.1 seconds). Chromium could not start in the assistant's sandbox. **Lesson learned:** UI tests should use stable semantic or component-specific selectors instead of assuming a particular depth of HTML nesting.

### Teacher registration and administrator approval

The added components are `frontend/src/RegisterForm.jsx` and `frontend/src/AdminTeacherApprovals.jsx`:

1. An HTML form collects name, email, phone number and password. The browser checks password confirmation and minimum length.
2. `FormData` submits `multipart/form-data` to `POST /api/v1/auth/register`. Sending JSON would violate the existing FastAPI contract, which expects `Form(...)` fields.
3. The backend creates the teacher with `is_approved = false`; the UI does **not** claim the account can already sign in.
4. `POST /api/v1/auth/login` rejects unapproved teachers (HTTP 403, covered by a backend test).
5. An administrator uses `GET /api/v1/teachers/pending` and `PATCH /api/v1/teachers/{id}/approve` to approve the account.
6. Approved teachers can then access the existing React teacher dashboard.

**Course connection:** HTML forms, JavaScript events, `fetch`, choosing FormData or JSON according to the API contract, HTTP status codes, error feedback, role-based permissions and persistence. React manages presentation; FastAPI remains responsible for authorization.

**Intentional limitation:** Public registration does not yet include document uploads or subject selection. The existing backend document-upload implementation requires a security review covering access, validation and storage before real personal documents are accepted. Use only fictional test accounts.

- The frontend build and seven existing unit tests passed. At the time of the registration change, the backend suite passed 13 tests; a team member subsequently confirmed the registration → admin approval → teacher login browser workflow.
- The large `main.jsx` can be split into smaller components as the interface grows.
- Additional accessibility reviews, mobile-device tests and a broader range of browser error scenarios remain outstanding.
- Actual individual contributions and coaching decisions must be supplied by the team.
