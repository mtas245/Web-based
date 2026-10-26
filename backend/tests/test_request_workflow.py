"""Milestone 2: API + SQLite persistence, including negative cases."""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from main import app
from database import get_db
from core.dependencies import require_admin, require_teacher
from models.user import User, Role
from models.subject import Subject
from models.request import SubstituteRequest, RequestStatus
from models.application import Application, ApplicationStatus


@pytest.fixture
def setup_api():
    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        users = [
            User(full_name="Admin", email="admin@demo.local", hashed_password="none",
                 role=Role.ADMIN, is_approved=True),
            User(full_name="Teacher1", email="teacher1@demo.local", hashed_password="none",
                 role=Role.TEACHER, is_approved=True),
            User(full_name="Teacher2", email="teacher2@demo.local", hashed_password="none",
                 role=Role.TEACHER, is_approved=True),
        ]
        subject = Subject(name="Math", level="primary", grades="1-6")
        db.add_all([*users, subject])
        db.commit()
        for obj in [*users, subject]:
            db.refresh(obj)
        admin_id, teacher1_id, teacher2_id = [u.id for u in users]
        subject_id = subject.id
    current_teacher = [teacher1_id]

    def get_test_db():
        with Session(engine) as db:
            yield db

    def admin_role():
        with Session(engine) as db:
            return db.get(User, admin_id)

    def teacher_role():
        with Session(engine) as db:
            return db.get(User, current_teacher[0])

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[require_admin] = admin_role
    app.dependency_overrides[require_teacher] = teacher_role
    try:
        with TestClient(app) as client:
            yield client, engine, subject_id, current_teacher, teacher2_id
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def create(client, subject_id):
    return client.post("/api/v1/requests/", json={
        "date": (date.today() + timedelta(days=7)).isoformat(),
        "grade_level": "3a", "subject_id": subject_id,
        "time_slot": "09:00-11:00", "note": "Teacher missing"
    })


def test_request_crud_and_invalid_input(setup_api):
    client, _, subject_id, _, _ = setup_api
    created = create(client, subject_id)
    assert created.status_code == 201, created.text
    req_id = created.json()["id"]
    assert client.get(f"/api/v1/requests/{req_id}").status_code == 200
    modified = client.patch(f"/api/v1/requests/{req_id}", json={"note": "Changed"})
    assert modified.status_code == 200, modified.text
    assert modified.json()["note"] == "Changed"
    assert client.post("/api/v1/requests/", json={
        "date": "2020-01-01", "grade_level": "3a", "subject_id": subject_id
    }).status_code == 422
    assert create(client, 999999).status_code == 400
    assert client.delete(f"/api/v1/requests/{req_id}").status_code == 204
    assert client.get(f"/api/v1/requests/{req_id}").status_code == 404


def test_application_approval_workflow(setup_api):
    client, engine, subject_id, current_teacher, second_teacher = setup_api
    request = create(client, subject_id)
    assert request.status_code == 201, request.text
    request_id = request.json()["id"]
    first = client.post(f"/api/v1/requests/{request_id}/apply")
    assert first.status_code == 201, first.text
    assert client.post(f"/api/v1/requests/{request_id}/apply").status_code == 400
    current_teacher[0] = second_teacher
    second = client.post(f"/api/v1/requests/{request_id}/apply")
    assert second.status_code == 201, second.text
    approve = client.patch(f"/api/v1/applications/{first.json()['id']}/approve")
    assert approve.status_code == 200, approve.text
    with Session(engine) as db:
        assert db.get(SubstituteRequest, request_id).status == RequestStatus.FILLED
        assert db.get(Application, second.json()["id"]).status == ApplicationStatus.REJECTED
    assert client.patch(f"/api/v1/applications/{second.json()['id']}/approve").status_code == 409
    assert client.patch(f"/api/v1/requests/{request_id}", json={"note": "No"}).status_code == 409
