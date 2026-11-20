"""Regression test: the SQLite compatibility migration preserves legacy IDs/data."""
from sqlalchemy import text
from sqlmodel import Session, create_engine, select

import database
from models.school import School
from models.user import User
from models.request import SubstituteRequest


def test_legacy_rows_get_default_school_and_migration_is_idempotent(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}", connect_args={"check_same_thread": False})
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE user (id INTEGER PRIMARY KEY, full_name TEXT, personal_number TEXT, email TEXT, hashed_password TEXT, role TEXT, is_approved BOOLEAN, phone TEXT, bio TEXT, profile_picture TEXT, documents_path TEXT, created_at DATETIME)"))
        connection.execute(text("CREATE TABLE substituterequest (id INTEGER PRIMARY KEY, date DATE, grade_level TEXT, subject_id INTEGER, time_slot TEXT, note TEXT, status TEXT, expires_at DATETIME, created_by INTEGER, created_at DATETIME)"))
        connection.execute(text("INSERT INTO user (id,full_name,email,hashed_password,role,is_approved) VALUES (7, 'Legacy Admin', 'legacy@example.test', 'unused', 'ADMIN', 1)"))
        connection.execute(text("INSERT INTO substituterequest (id,date,grade_level,subject_id,created_by,status) VALUES (13, '2027-01-10', '3a', 1, 7, 'OPEN')"))
    monkeypatch.setattr(database, "engine", engine)
    database.create_db_and_tables()
    database.create_db_and_tables()
    with Session(engine) as session:
        admin = session.get(User, 7)
        request = session.get(SubstituteRequest, 13)
        assert admin.school_id == request.school_id
        assert session.get(School, admin.school_id).name == "Primarschule Volta"
        assert len(session.exec(select(School)).all()) == 1
    engine.dispose()
