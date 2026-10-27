# EduSub — Web-based Application

> Substitute Teacher Coordination Platform  
> FHNW — Web-based Applications (HS26) | Dr. Devid Montecchiari

**Current stage (27 October 2026):** Milestone 1 design documentation + Milestone 2 functional backend/API slice; the planned React/Vite frontend has **not** been implemented or demonstrated.

This is the living project README, retaining the original Milestone 1 design draft and recording the subsequently implemented Milestone 2 backend. The source-of-truth OpenAPI contract is generated at `/openapi.json`; the earlier examples further down are **historical design examples** and may differ from the actual endpoints. For verified endpoint names and JSON payloads, use the current API summary below and `/docs`.

**Development and evidence:** Work is committed on [`mtas245/Web-based` branch `feature/milestone1-2`](https://github.com/mtas245/Web-based/tree/feature/milestone1-2), a fork of the [team repository](https://github.com/uAhmet1907/Web-based). The team repository has not been updated by this work. See [the detailed Milestone 1–2 implementation and test record](docs/MILESTONE-1-2.md).

## Milestone 2 — working backend, API and evidence

### Implemented slice and boundaries

The browser-independent FastAPI backend uses SQLModel with local SQLite persistence (`backend/edusub.db`). The tested core workflow is: administrator authenticates → creates an open substitute request for an existing subject → an approved teacher signs in and applies → administrator approves an application → the request changes to `filled`. An administrator can also read, update and delete an open request, subject to rules and validation.

The application layers are:
- **API boundary and contracts:** `backend/routers/` plus `backend/schemas/` (FastAPI/OpenAPI and Pydantic).
- **Business logic:** `backend/services/` (request status transitions, application decisions, account workflows).
- **Relational persistence:** `backend/models/` and `backend/database.py` (SQLModel + SQLite).
- **Authentication / access checks:** `backend/core/` (JWT and role dependencies).

The proposed React/Vite UI, responsive layout and UI→API integration are still **planned**. The earlier NiceGUI-based [EduSub Advanced Programming project](https://github.com/mtas245/EduSub_Project) supplied domain concepts/workflows but is not evidence that this project's new frontend works.

### Reproduce locally (Windows / PowerShell)

From the cloned repository root:

```powershell
cd backend
py -3.12 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m pytest -q
.\\.venv\\Scripts\\python.exe -m uvicorn main:app --reload
```

The API root is `http://127.0.0.1:8000/`, Swagger UI is `http://127.0.0.1:8000/docs`, and machine-readable OpenAPI is `http://127.0.0.1:8000/openapi.json`. Run from `backend/`, because the SQLite database URL is relative to that directory.

To bootstrap a **local-only** administrator after installing dependencies, open another terminal in `backend/`:

```powershell
.\\.venv\\Scripts\\python.exe scripts/create_local_admin.py
```

Enter a test email, name and unique password interactively; do not commit passwords, local databases or JWTs. The script refuses to overwrite an account with the same email. In `POST /api/v1/auth/login`, enter the email in the form's **username** field, then authorize Swagger using the issued token. Subject fixtures can be created using the admin-only `POST /api/v1/subjects/seed`, followed by `GET /api/v1/subjects/` to discover real subject IDs.

### Implemented API contracts — examples

| Method | Route | Access / behavior |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | Public form login; email in `username`, password in `password` |
| POST | `/api/v1/auth/register` | Public teacher registration via `multipart/form-data`, initially unapproved |
| GET / PATCH | `/api/v1/teachers/pending`; `/api/v1/teachers/{teacher_id}/approve` | Admin lists pending teachers and approves one (GET and PATCH respectively) |
| GET / POST | `/api/v1/subjects/`; `/api/v1/subjects/seed` | Authenticated list / admin seed |
| GET / POST | `/api/v1/requests/` | Admin list / admin create |
| GET / PATCH / DELETE | `/api/v1/requests/{request_id}` | Admin read / edit open / delete open with no applications |
| GET | `/api/v1/requests/open` | Approved teacher lists open, unexpired requests |
| POST | `/api/v1/requests/{request_id}/apply` | Approved teacher applies |
| GET / PATCH | `/api/v1/applications/pending`; `/api/v1/applications/{application_id}/approve` | Admin list / approval (GET and PATCH respectively) |

Actual admin request-create JSON body (choose a future date and an existing subject ID):

```json
{
  "date": "2026-12-01",
  "grade_level": "3a",
  "subject_id": 1,
  "time_slot": "08:00-10:00",
  "note": "Local API demonstration"
}
```

The API uses `grade_level`, not the older draft field `grade`. `POST /auth/register` is a multipart form, **not** a JSON object, and `POST /auth/login` uses OAuth2 form fields. Request creation returns 201; invalid schema 422, unknown subject 400, missing authentication 401, missing permission 403. Request deletion returns 204, and reading a deleted request returns 404.

### Test evidence

**User-confirmed locally, 27 October 2026:** `python -m pytest -q` with Python 3.12.10 produced **11 passed, 16 warnings in 1.27s** (zero failures). These tests cover schema/API contracts and business workflow, but dependency overrides do not constitute complete real-JWT security testing.

Separately, a team member confirmed **19 successful manual Swagger endpoint checks** covering admin authentication and denial without authentication, subject setup, request CRUD, invalid inputs, teacher sign-in/application, admin approval and final request status `filled`. Registration and teacher-account approval also worked according to the user, though their precise HTTP statuses were not provided. These are user-reported demonstrations, not independent CI results. The detailed scenario-by-scenario results and limitations are in [docs/MILESTONE-1-2.md](docs/MILESTONE-1-2.md).

### Outstanding / not yet evidenced

- Complete the visual design evidence: sketches or wireframes and user feedback for the main role-specific screens.
- Finalize **actual** contributions and responsibilities for all group members; the initial assignment table below is tentative, with a fourth-member placeholder.
- Record lecturer/coaching feedback, scope decisions and agreed deferrals. Dates/deadlines should be checked in Moodle.
- Save redacted evidence screenshots or responses and audit remaining error/authorization cases (`403` for teacher on admin routes; duplicate applications and conflicting approvals).
- Resolve security concerns before real users: hardcoded JWT signing key, uploaded document exposure/name handling, concurrent approval protection and expiry/audit-trail policy.
- Implement and demonstrate the planned responsive frontend and API integration in a subsequent milestone.

---


## Project overview

**EduSub** is a browser-based substitute teacher coordination platform built for a single primary school covering Kindergarten (KG1, KG2) and Primary grades (1a–6b).

The platform digitises the process of finding and assigning substitute teachers when a class cannot be covered by its regular teacher. It provides two role-specific portals (Admin and Teacher) each with dedicated functionality.

### Problem addressed

Schools currently coordinate substitute assignments via phone calls, WhatsApp groups and Excel sheets. This creates gaps, missed assignments and no audit trail.

### Proposed solution

EduSub provides:
- A structured **substitute request** flow (date, grade, subject, time slot, notes)
- A **teacher application** system (teachers self-assign to open requests with expiry countdowns)
- An **admin approval** layer (admins confirm assignments, manage users, close requests)
- A **teacher onboarding** flow including document upload and account approval
- A **teacher profile** system (profile picture, bio, subjects, personal staff number)

This module adapts the earlier NiceGUI EduSub concepts into an independently callable **FastAPI REST backend** with JWT-based authentication. A **React (Vite) frontend is planned but not yet implemented**; API/UI separation is an architectural goal until integration is demonstrated.

**GitHub Repository:** https://github.com/uAhmet1907/Web-based

### Team and initial responsibilities (provisional; actual contributions still to confirm)

| Member | Initial responsibility | Next action |
|---|---|---|
| Mert Kirtas | Coordination and README | Keep decisions, questions and the milestone commit together |
| Ugur Ahmet Iyidogan | Users and workflow | Describe needs and the steps of one workflow |
| Ata Erduran | Sketches and interaction | Sketch the screens and feedback for that workflow |
|  | Data and API exploration | Prepare sample JSON and clarify the proposed operations |

These are suggested starting responsibilities, not permanent silos. Discuss and review each other's work; everyone should understand the draft. Adjust or rotate responsibilities as needed.

## 1. Analysis

### Scenario, users and goals

- Situation or problem: Substitute assignments are coordinated through phone calls, WhatsApp groups and Excel sheets, causing gaps, missed assignments and a missing audit trail.
- Intended users: School administrators and substitute teachers at one primary school, including KG1/KG2 and grades 1a–6b.
- Proposed benefit: Structured coverage requests, teacher applications and administrative approval make assignments and their status visible.
- Initial scope: The existing README describes the full planned feature set but does not select a first implementation workflow or explicitly defer features. W-02 → W-03 → W-04 below is a candidate already described in the draft; the team must confirm the initial scope after coaching.

| Role | Description |
|------|-------------|
| **Admin** | School administrator. Creates substitute requests, reviews teacher applications, approves/rejects teacher accounts, manages users, closes requests. |
| **Teacher** | Registered substitute teacher. Browses open requests, submits and withdraws applications, tracks application status, manages their profile. |

### User stories and first workflow

The following stories are retained from the existing README. Their inclusion does not mean that every story belongs to the first implementation scope.

#### Admin

| ID | As an admin, I want to… | So that… |
|----|-------------------------|----------|
| A-01 | Log in with email and password | I can access the admin dashboard securely |
| A-02 | Create a substitute request with date, grade, subject, time slot and notes | Teachers know exactly what coverage is needed |
| A-03 | View all substitute requests in a table with status | I have a full overview of all coverage gaps |
| A-04 | See the details of a request (grade, subject, date, notes, expiry) | I can review what was created |
| A-05 | See which teachers have applied for a request | I can pick the most suitable substitute |
| A-06 | Approve or reject a teacher's application | The assignment is confirmed and the request is marked filled |
| A-07 | Close a substitute request manually | Outdated or filled requests are archived |
| A-08 | View all registered teachers and their approval status | I have an overview of who is on the platform |
| A-09 | View a teacher's full profile including documents and subjects | I can verify their qualifications |
| A-10 | Approve or reject a newly registered teacher account | Only verified teachers can access the platform |
| A-11 | View aggregated dashboard stats (open requests, pending applications, pending teachers) | I get an instant overview without navigating multiple pages |
| A-12 | Log out | My session is ended securely |

#### Teacher

| ID | As a teacher, I want to… | So that… |
|----|--------------------------|----------|
| T-01 | Register with my name, email, phone, password and subjects | I can request access to the platform |
| T-02 | Upload my CV and teaching certificates during registration | The admin can verify my qualifications |
| T-03 | Log in with email and password after my account is approved | I can access the teacher dashboard |
| T-04 | Browse all open substitute requests | I can find available assignments |
| T-05 | Filter requests by educational level (KG / Primary) | I only see relevant assignments for my qualifications |
| T-06 | See the time remaining before a request expires | I know how urgently I need to apply |
| T-07 | Apply for an open substitute request | I can express interest in a specific coverage slot |
| T-08 | See if I have already applied for a request | I avoid applying twice |
| T-09 | View all my applications with their current status (pending / approved / rejected) | I can track where each application stands |
| T-10 | Withdraw a pending application | I can back out if my availability changes |
| T-11 | View my confirmed assignments | I know exactly when and where I am teaching |
| T-12 | Edit my profile (name, phone, bio, subjects, profile picture) | My information stays accurate |
| T-13 | Change my password | I can keep my account secure |
| T-14 | Log out | My session is ended securely |

#### Workflow Table

| # | Workflow | Actor(s) | Steps | Outcome |
|---|----------|----------|-------|---------|
| W-01 | Teacher Registration & Approval | Teacher → Admin | 1. Teacher fills registration form (name, email, phone, password, subjects). 2. Teacher uploads documents (PDF/JPG/PNG). 3. Account created with `is_approved = false`. 4. Admin reviews profile and documents. 5. Admin approves or rejects. | Teacher can log in (approved) or account is deleted (rejected). |
| W-02 | Create Substitute Request | Admin | 1. Admin opens "New Request" form. 2. Enters date, grade, subject (dynamically filtered by grade), time slot, notes. 3. Submits. 4. System creates request with status `open` and calculates `expires_at` (12h before assignment start). | Request is visible to all approved teachers. |
| W-03 | Teacher Applies for Request | Teacher | 1. Teacher browses open, non-expired requests. 2. Filters by level (KG / Primary) if needed. 3. Clicks "Apply". 4. System creates application with status `pending`. | Admin sees new application; teacher sees "Applied" badge on the request. |
| W-04 | Admin Approves Application | Admin → Teacher | 1. Admin views pending applications. 2. Opens teacher profile to verify qualifications. 3. Approves one application → status becomes `approved`. 4. Request status automatically changes to `filled`. | Teacher sees confirmed assignment; request is no longer open. |
| W-05 | Teacher Withdraws Application | Teacher | 1. Teacher views "My Applications" list. 2. Clicks "Withdraw" on a pending application. 3. System deletes the application. | Teacher is removed from the applicant list; request returns to open if no other approved application exists. |
| W-06 | Admin Closes Request | Admin | 1. Admin opens the requests table. 2. Clicks "Close" on a filled or outdated request. 3. System sets status to `closed`. | Request is archived; no new applications accepted. |
| W-07 | Request Expires Automatically | System | 1. System checks `expires_at` on all open requests. 2. Requests past expiry are automatically deleted. | Platform stays clean; teachers only see actionable requests. |
| W-08 | Teacher Updates Profile | Teacher | 1. Teacher opens profile page. 2. Edits name, phone, bio, subjects or uploads new profile picture. 3. Saves. | Teacher's profile is updated in the database. |
| W-09 | Teacher Changes Password | Teacher | 1. Teacher submits current password + new password. 2. Backend verifies current password, hashes and saves the new one. | Password is updated; existing JWT remains valid until expiry. |
| W-10 | Login (any role) | Admin / Teacher | 1. User enters email and password. 2. Backend verifies credentials; checks `is_approved` for teachers. 3. Issues JWT access token. | User is redirected to their role-specific dashboard. |
| W-11 | Logout | Admin / Teacher | 1. User clicks "Logout". 2. Frontend deletes the JWT from storage. 3. User is redirected to the login page. | Session is terminated client-side. |

These are intended behaviours from the original draft. W-07's automatic deletion conflicts with the stated audit-trail need; W-05's reopening behaviour also needs clarification. See the open questions in Project management.

## 2. Design

### Screens and navigation

Link or embed your sketches for the workflow (paper photos, draw.io or another tool). Explain the main inputs, actions and feedback. This builds on exercise 2. A polished or clickable prototype is not required; add one if you already have it.

#### Planned screens

| Screen | Role | Description |
|--------|------|-------------|
| Login | All | Email + password form |
| Teacher Registration | Teacher | Name, email, phone, password, subject selection, document upload |
| Admin Dashboard | Admin | Stats overview (open requests, pending applications, pending teachers) |
| Substitute Requests List | Admin / Teacher | Full requests table with status badges; filter by level for teachers |
| Request Detail | Admin | Full request info + applicants list with approve button |
| Admin — Teacher List | Admin | All teachers with approval status and link to profile |
| Admin — Teacher Profile | Admin | Full teacher details, documents, approve/reject buttons |
| Teacher Dashboard — Available | Teacher | Open requests with grade/subject, date, time slot, expiry countdown, apply button |
| Teacher Dashboard — My Applications | Teacher | All own applications with pending / approved / rejected status + withdraw button |
| Teacher Profile | Teacher | Edit name, phone, bio, subjects; upload profile picture; change password; staff number display |

### Domain concepts and example data

Link your sample JSON files for relevant things in the workflow. Use fictional data. Explain important fields, value types and references between objects; mark uncertainties. The bar catalogue and order examples are available as a starting point. There is no new fixed entity quota for this draft.

#### Sample JSON and draft API examples

The following historical Milestone 1 API ideas use `/api/v1` and show **draft** status codes and payloads, not a reliable description of the running API. Refer to the Milestone 2 section at the top and live `/docs` for implemented endpoints. The existing authentication design uses `Authorization: Bearer <token>`. Its blanket JWT requirement conflicts with login/registration; the access rules are an **Open question**. Sample dates are example data, not milestone dates.

#### Auth

##### `POST /api/v1/auth/login`

**Request**
```json
{
  "email": "admin@edusub.ch",
  "password": "admin123"
}
```

**Response `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin"
}
```

##### `POST /api/v1/auth/register`

**Request**
```json
{
  "full_name": "Anna Müller",
  "email": "anna.mueller@edusub.ch",
  "phone": "0791234567",
  "password": "securepass",
  "subjects": [1, 3, 7]
}
```

**Response `201 Created`**
```json
{
  "id": 5,
  "email": "anna.mueller@edusub.ch",
  "is_approved": false,
  "message": "Registration successful. Waiting for admin approval."
}
```

##### `POST /api/v1/auth/change-password`

**Request**
```json
{
  "current_password": "securepass",
  "new_password": "newsecurepass"
}
```

**Response `200 OK`**
```json
{
  "message": "Password updated successfully."
}
```

---

#### Substitute Requests

##### `GET /api/v1/requests`

**Response `200 OK`**
```json
[
  {
    "id": 12,
    "date": "2026-10-15",
    "grade": "3a",
    "subject": { "id": 3, "name": "Mathematics" },
    "time_slot": "08:00-12:00",
    "note": "Please bring exercise sheets.",
    "reason": "Illness",
    "status": "open",
    "expires_at": "2026-10-14T20:00:00Z",
    "created_at": "2026-10-02T09:00:00Z",
    "created_by": { "id": 1, "name": "Admin Schulhaus" }
  }
]
```

##### `POST /api/v1/requests` *(Admin only)*

**Request**
```json
{
  "date": "2026-10-15",
  "grade": "3a",
  "subject_id": 3,
  "time_slot": "08:00-12:00",
  "note": "Please bring exercise sheets."
}
```

**Response `201 Created`**
```json
{
  "id": 13,
  "date": "2026-10-15",
  "grade": "3a",
  "subject_id": 3,
  "time_slot": "08:00-12:00",
  "status": "open",
  "expires_at": "2026-10-14T20:00:00Z"
}
```

##### `GET /api/v1/requests/{id}/applications` *(Admin only)*

**Response `200 OK`**
```json
[
  {
    "id": 8,
    "teacher": { "id": 5, "full_name": "Anna Müller", "personal_number": "T-0042" },
    "status": "pending",
    "applied_at": "2026-10-03T11:30:00Z"
  }
]
```

##### `PATCH /api/v1/requests/{id}/close` *(Admin only)*

**Response `200 OK`**
```json
{
  "id": 12,
  "status": "closed"
}
```

---

#### Applications

##### `POST /api/v1/requests/{request_id}/applications` *(Teacher only)*

**Response `201 Created`**
```json
{
  "id": 8,
  "request_id": 12,
  "teacher_id": 5,
  "status": "pending",
  "applied_at": "2026-10-03T11:30:00Z"
}
```

##### `GET /api/v1/applications/my` *(Teacher only)*

**Response `200 OK`**
```json
[
  {
    "id": 8,
    "request": {
      "id": 12,
      "date": "2026-10-15",
      "grade": "3a",
      "subject": { "id": 3, "name": "Mathematics" },
      "time_slot": "08:00-12:00"
    },
    "status": "pending",
    "applied_at": "2026-10-03T11:30:00Z"
  }
]
```

##### `PATCH /api/v1/applications/{id}/approve` *(Admin only)*

**Response `200 OK`**
```json
{
  "id": 8,
  "status": "approved",
  "request": { "id": 12, "status": "filled" }
}
```

##### `DELETE /api/v1/applications/{id}` *(Teacher — own pending application only)*

**Response `204 No Content`**

---

#### Subjects

##### `GET /api/v1/subjects`

**Response `200 OK`**
```json
[
  { "id": 1, "name": "German",      "level": "primary", "grades": "1-6" },
  { "id": 2, "name": "Mathematics", "level": "primary", "grades": "1-6" },
  { "id": 3, "name": "French",      "level": "primary", "grades": "3-6" },
  { "id": 4, "name": "English",     "level": "primary", "grades": "5-6" },
  { "id": 5, "name": "Free Play",   "level": "kg",      "grades": "KG"  }
]
```

---

#### Teachers (Admin view)

##### `GET /api/v1/teachers` *(Admin only)*

**Response `200 OK`**
```json
[
  {
    "id": 5,
    "full_name": "Anna Müller",
    "personal_number": "T-0042",
    "email": "anna.mueller@edusub.ch",
    "phone": "0791234567",
    "is_approved": false,
    "subjects": [{ "id": 3, "name": "Mathematics" }]
  }
]
```

##### `GET /api/v1/teachers/{id}` *(Admin only)*

**Response `200 OK`**
```json
{
  "id": 5,
  "full_name": "Anna Müller",
  "personal_number": "T-0042",
  "email": "anna.mueller@edusub.ch",
  "phone": "0791234567",
  "bio": "Experienced primary school teacher with 5 years in Basel.",
  "profile_picture": "/uploads/profile_pictures/user_5.jpg",
  "documents": ["cv_anna.pdf", "certificate_math.pdf"],
  "is_approved": false,
  "subjects": [
    { "id": 3, "name": "Mathematics" },
    { "id": 7, "name": "English" }
  ]
}
```

##### `PATCH /api/v1/teachers/{id}/approve` *(Admin only)*

**Request**
```json
{ "approved": true }
```

**Response `200 OK`**
```json
{
  "id": 5,
  "is_approved": true
}
```

---

#### Dashboard Stats (Admin)

##### `GET /api/v1/dashboard/admin` *(Admin only)*

**Response `200 OK`**
```json
{
  "total_requests": 24,
  "open_requests": 6,
  "pending_applications": 3,
  "pending_teachers": 2
}
```

---

#### Profile (Teacher)

##### `GET /api/v1/profile`

**Response `200 OK`**
```json
{
  "id": 5,
  "full_name": "Anna Müller",
  "personal_number": "T-0042",
  "email": "anna.mueller@edusub.ch",
  "phone": "0791234567",
  "bio": "Experienced primary school teacher.",
  "profile_picture": "/uploads/profile_pictures/user_5.jpg",
  "subjects": [
    { "id": 3, "name": "Mathematics" },
    { "id": 7, "name": "English" }
  ],
  "is_approved": true
}
```

##### `PATCH /api/v1/profile`

**Request**
```json
{
  "full_name": "Anna Müller-Schmidt",
  "phone": "0799876543",
  "bio": "Updated bio.",
  "subjects": [3, 5, 7]
}
```

**Response `200 OK`**
```json
{
  "id": 5,
  "full_name": "Anna Müller-Schmidt",
  "phone": "0799876543",
  "bio": "Updated bio.",
  "subjects": [
    { "id": 3, "name": "Mathematics" },
    { "id": 5, "name": "German" },
    { "id": 7, "name": "English" }
  ]
}
```

### Business rules and possible operations

Describe a rule and an exception in plain language. Example: order quantities must be positive; discuss what happens when an item is unavailable. Later, explain where the implementation enforces the rule.

| User goal | Proposed action | Example input | Expected output | Open question |
|---|---|---|---|---|
| Access the platform | Register; sign in; change password | Registration fields; email/password; current/new password | Pending account, access token or password-change confirmation | Which operations are public, and how long is a token valid? |
| Publish coverage needs | Create and read substitute requests | Date, grade, subject ID, time slot, note | Request ID, `open` status, calculated expiry; request list | How do `grade` and `grade_level` map, and what if the time slot is absent? |
| Find suitable coverage | Read subjects and open requests | Request/subject selection; educational level | Catalogue and available requests | How is filtering represented, and which subject IDs are correct? |
| Express interest | Create an application | Request ID; current teacher | Application ID and `pending` status | How are duplicate or expired-request applications handled? |
| Review applications | Read request applicants and own applications | Request ID or current teacher | Applicants or application statuses with request details | What feedback accompanies rejection? |
| Confirm an assignment | Approve an application | Application ID | `approved` application and `filled` request | What happens to other pending applications? |
| Withdraw interest | Remove own pending application | Application ID | No content (`204` in the draft) | When, if ever, should this reopen a request? |
| Stop accepting applications | Close a request | Request ID | `closed` status | How are pending applications handled? |
| Handle expired requests | Automatically remove expired open requests, as currently drafted | `expires_at` | Request no longer available | How is the audit trail preserved? |
| Verify teachers | Read teacher list/profile; approve or reject an account | Teacher ID; `approved: true` in the approval sample | Teacher details and updated approval flag | Account rejection/deletion is described, but the operation is not specified. |
| Review workload | Read admin dashboard statistics | Signed-in admin | Request, application and teacher counts | Exact counting rules are TBD. |
| Maintain own profile | Read/change profile; upload documents or picture | Name, phone, bio, subject IDs; selected files | Updated profile | File-upload operations and restrictions are TBD. |
| Reject an application | Change application status, as described in A-06 | Application ID; remaining details TBD | Intended `rejected` state | No rejection endpoint or sample is defined. |
| End a session | Remove the client-side token and return to login | Current session | Login screen | Confirm the intended treatment of tokens that remain valid. |

Use plain language; final endpoints and implementation can follow after coaching. These are draft ideas, not a complete CRUD implementation.


### Inspiration from existing apps or APIs — optional 
If useful for your design, link an existing app, website or API and add one or two sentences about what you would adopt or improve for your users. No separate research report or external API integration is required for this milestone.

EduSub builds on the group's NiceGUI monolith from Advanced Programming (SS26). The existing proposal separates that application into a FastAPI REST backend and React frontend.

## 3. Project management

### Decisions, open questions and next steps

| Question / decision | Current position | Next step / person |
|---|---|---|
| Project idea | EduSub for a single school, KG and primary grades. | Confirm first implementation scope after coaching / TBD. |
| Sketches | `wireframes.pdf` is planned, not supplied in the README. | Add sketches with screens, actions and feedback / TBD. |
| First workflow and deferred features | Full story/workflow catalogue exists; first scope is not selected. | Confirm candidate W-02 → W-04 and identify what can wait / TBD. |
| Team membership and allocation | Member A–C are placeholders. | Record actual members and confirm responsibilities / TBD. |

### Milestone progress

| Milestone | Available evidence | Status / next step |
|---|---|---|
| 1 — Design draft | Project problem, intended users and initial scope, user stories and workflow table, planned interface screens; sample JSON, proposed API operations, business rules and documented open questions. | Ready for design coaching. Add the final interface sketches, confirm team responsibilities and discuss the remaining open questions during coaching. After coaching, record the agreed changes and select the initial implementation workflow. |

Use the Moodle assignment for the complete milestones, dates and assessment criteria. Describe contributions and decisions; commit counts do not measure individual effort.

## 4. References and acknowledgements

- [EduSub repository](https://github.com/uAhmet1907/Web-based): repository identified in the existing README.
- **EduSub, Advanced Programming (SS26):** earlier NiceGUI project identified as the starting point. Repository link, reused components and specific adaptations: **TBD**.
- **Official FHNW Web-based Applications HS26 Milestone 1 README template:** supplied by the user; source of this document's structure and handoff checklist. Moodle link: **TBD**.
- **Template lineage:** the earlier [Pizzeria Reference Project](https://github.com/FHNW-INT/Pizzeria_Reference_Project) organised documentation around analysis, design, implementation, execution and project management. The supplied template updates that structure for the HS26 Python/FastAPI teaching path; its Java/Spring and hosted Budibase setup instructions do not apply here.
- **Documentation, reused assets, libraries and other assistance:** the technology proposal lists planned tools, but actual use, documentation references and further acknowledgements are **TBD**.

## Friday handoff checklist

- Commit this README and the available draft material before the milestone.
- First join the module's MS Team using the link in Moodle. The lecturer will then add you to your group's private channel during the week.
- Submit the GitHub repository link in Moodle by Friday, following the milestone instructions published after class.
- Ensure the lecturer can access the repository; public visibility is not required.
- If you do not yet have a group channel and your team composition is not recorded in Moodle's team formation activity, email the lecturer with all team members' names. If the composition is already recorded, join the Team so you can be added to the channel. Contact the lecturer if the channel is still unavailable before the deadline.
- Refer to Moodle for the milestone date and the full assignment requirements.

Keep credentials and personal data out of the repository. The draft and its progress are useful evidence for project management; commit counts or lines of code are not measures of individual contribution.
