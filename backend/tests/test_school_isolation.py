"""Cross-school access checks: front-end filtering is never an authorization boundary."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from main import app
from database import get_db
from core.dependencies import get_current_user, require_admin, require_teacher
from models.school import School
from models.user import User, Role
from models.subject import Subject


@pytest.fixture
def schools_api():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        north = School(name="Primarschule Volta")
        south = School(name="Primarschule Thierstein")
        db.add_all([north, south])
        db.flush()
        admins = [
            User(full_name="Volta Admin", email="volta@example.test", hashed_password="x", role=Role.ADMIN, school_id=north.id, is_approved=True),
            User(full_name="Thierstein Admin", email="thierstein@example.test", hashed_password="x", role=Role.ADMIN, school_id=south.id, is_approved=True),
        ]
        teacher = User(full_name="Teacher", email="teacher@example.test", hashed_password="x", role=Role.TEACHER, is_approved=True)
        subject = Subject(name="Mathematics", level="primary", grades="1-6")
        db.add_all([*admins, teacher, subject])
        db.commit()
        admin_ids = [admin.id for admin in admins]
        teacher_id, subject_id = teacher.id, subject.id

    selected_admin = [0]

    def test_db():
        with Session(engine) as session:
            yield session

    def admin():
        with Session(engine) as session:
            return session.get(User, admin_ids[selected_admin[0]])

    def educator():
        with Session(engine) as session:
            return session.get(User, teacher_id)

    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[require_admin] = admin
    app.dependency_overrides[require_teacher] = educator
    app.dependency_overrides[get_current_user] = admin
    try:
        with TestClient(app) as client:
            yield client, selected_admin, subject_id
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_cross_school_request_and_application_isolation(schools_api):
    client, selected_admin, subject_id = schools_api
    payload = {"date": (date.today() + timedelta(days=7)).isoformat(), "grade_level": "3a", "subject_id": subject_id, "time_slot": "09:00-11:00"}
    created = client.post("/api/v1/requests/", json={**payload, "school_id": 999})
    assert created.status_code == 201, created.text
    north = created.json()
    assert north["school_name"] is None  # Admin requests have no joined school-name field.
    assert north["school_id"] != 999  # Cannot forge school ownership in JSON.
    requested = client.post(f"/api/v1/requests/{north['id']}/apply")
    assert requested.status_code == 201, requested.text

    selected_admin[0] = 1
    assert client.get("/api/v1/requests/").json() == []
    assert client.get(f"/api/v1/requests/{north['id']}").status_code == 404
    assert client.patch(f"/api/v1/requests/{north['id']}", json={"note": "tampered"}).status_code == 404
    assert client.delete(f"/api/v1/requests/{north['id']}").status_code == 404
    assert client.patch(f"/api/v1/requests/{north['id']}/close").status_code == 404
    assert client.get("/api/v1/applications/pending").json() == []
    app_id = requested.json()["id"]
    assert client.patch(f"/api/v1/applications/{app_id}/approve").status_code == 404
    assert client.patch(f"/api/v1/applications/{app_id}/reject").status_code == 404
    assert client.get("/api/v1/dashboard/admin").json()["pending_applications"] == 0

    south = client.post("/api/v1/requests/", json=payload)
    assert south.status_code == 201
    assert south.json()["school_id"] != north["school_id"]
    open_requests = client.get("/api/v1/requests/open")
    assert open_requests.status_code == 200
    assert {r["school_name"] for r in open_requests.json()} == {"Primarschule Volta", "Primarschule Thierstein"}
    assert {s["name"] for s in client.get("/api/v1/schools/").json()} == {"Primarschule Volta", "Primarschule Thierstein"}

    selected_admin[0] = 0
    assert [r["id"] for r in client.get("/api/v1/requests/").json()] == [north["id"]]
    assert client.patch(f"/api/v1/applications/{app_id}/approve").status_code == 200
    assert client.get("/api/v1/dashboard/admin").json()["requests"]["filled"] == 1


def test_school_admin_cannot_view_or_approve_platform_teacher_accounts(schools_api):
    client, _, _ = schools_api
    assert client.get("/api/v1/teachers/pending").status_code == 403
    assert client.get("/api/v1/teachers/").status_code == 403
    assert client.get("/api/v1/teachers/123").status_code == 403
    assert client.patch("/api/v1/teachers/123/approve").status_code == 403
