# EduSub: Cross-School Architecture Decision

## Decision and scope

EduSub is a **cross-school substitute-teacher marketplace**, not a single-school administration system. Approved teachers may view and apply for open requests from all participating schools. A school administrator may manage **only their own school's** requests and applications. We use five real Basel school names **solely as fictional demo organisations**. EduSub has no affiliation with these schools. All administrator accounts, vacancies and applications are fictional.

The school names are: Primarschule Volta, Wasgenring, Thierstein, Rittergasse and Bruderholz. The actual number of schools is data-driven rather than hardcoded.

## Architectural decisions and alternatives

| Decision | Alternative | Rationale |
| --- | --- | --- |
| Shared SQLite database; `school_id` ownership | Separate database for every school | Simpler local reproduction for the module; tenant isolation enforced by backend authorization. |
| A school admin belongs to exactly one school | Multi-school membership table | The former covers the assessed user journey with less complexity; membership can be introduced later. |
| Teachers have no school assignment | Teachers restricted to one school | Cross-school discovery is the central product value. |
| Backend checks school ownership for every protected operation | Frontend filters alone | Client-side filtering does not prevent unauthorized API requests. |
| Dedicated `platform_admin` role for teacher approval | School admins approve any registered teacher | A single school's administration should not access all teachers' private application data. |
| Client-side filters and five-item pagination in teacher UI | Full server-side pagination | Appropriate for the small demonstration dataset; database pagination is future work for production scale. |

## Core data and API contract

- `School(id, name, city, is_active)` identifies the participating organisation.
- `User.school_id` scopes `admin` users; it is unset for teachers and `platform_admin`.
- `SubstituteRequest.school_id` is assigned **by the backend** from the authenticated school admin. The creation schema does not accept it.
- `Application` derives the school via `Application.request_id -> SubstituteRequest.school_id`.
- `GET /api/v1/requests/` and all request mutations are school-scoped for admins.
- `GET /api/v1/requests/open` lists public open vacancies across schools and includes `school_id` and `school_name`.
- `GET /api/v1/schools/` lists participating schools (public, no personal information).
- Pending applications, approval, rejection and admin dashboard statistics are school-scoped.
- School administrators cannot manage teacher approval or view global teacher profiles. These endpoints require `platform_admin`.
- For foreign protected records the API returns `404`, avoiding existence disclosure.

## Existing database migration

`create_db_and_tables()` creates the School table, adds nullable `school_id` columns to older SQLite databases and assigns legacy school administrators and requests to **Primarschule Volta**. Existing request/application IDs are retained. This compatibility migration is intended for the local course prototype, not as a replacement for versioned production migrations (for example, Alembic). Back up `backend/edusub.db` before the first launch after updating.

## Reproducible demonstration setup

From the `backend` directory, with the Python virtual environment active:

```powershell
Copy-Item .\edusub.db .\edusub.backup.db  # if a database already exists
python scripts/seed_demo_schools.py
python scripts/create_local_admin.py
```

Create one test school administrator for each school you want to demonstrate; select the school ID printed by the seed script. Use fictional `example.com` login addresses and unique passwords. To approve new substitute teachers locally, create a **platform administrator** using option 2 in the same helper script; the platform administrator can approve teacher registrations from the dedicated React view or Swagger.

Do not commit the local database, personal data, passwords or private uploaded documents. The five schools' real names do not indicate approval or participation.

## Verification

Run `python -m pytest -q` in `backend` and `npm test` / `npm run build` in `frontend`. As of 20 November 2026, 17 backend and nine frontend unit tests passed and the frontend build succeeded. `test_school_isolation.py` checks that a second school's admin cannot read, update, delete or close the first school's request, cannot see or approve its applications, and cannot see its admin statistics. It also checks cross-school teacher discovery, school naming and denial of platform-wide teacher-profile access to school admins. `test_school_migration.py` verifies preserving legacy record IDs and idempotence. The same workflow should be repeated manually with two distinct authenticated accounts through Swagger and the React UI.

## Remaining work

- Add full authenticated browser E2E tests with two distinct school administrators and one teacher.
- Expand automated browser coverage to include platform-level teacher approval.
- Implement production-grade migration tooling, server-side pagination and more flexible school memberships if the product grows.
- Review uploads and personal-data retention before any real-world deployment; no real school or teacher data should be entered in the demo.
