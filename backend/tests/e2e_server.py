"""Disposable local backend for Playwright browser tests; never uses edusub.db in the project."""

import os
from pathlib import Path
import sys
import tempfile

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# SQLite's relative path and upload folders now live in a disposable directory.
os.chdir(tempfile.mkdtemp(prefix="edusub-e2e-"))

from sqlmodel import Session, select  # noqa: E402
from database import engine, create_db_and_tables  # noqa: E402
from core.security import hash_password  # noqa: E402
from models.user import User, Role  # noqa: E402
from models.school import School  # noqa: E402
from models.subject import Subject  # noqa: E402
from scripts.seed_demo_schools import SCHOOL_NAMES  # noqa: E402
from main import app  # noqa: E402
import uvicorn  # noqa: E402

create_db_and_tables()
with Session(engine) as db:
    for school_name in SCHOOL_NAMES:
        if not db.exec(select(School).where(School.name == school_name)).first():
            db.add(School(name=school_name, city="Basel"))
    db.commit()
    volta = db.exec(select(School).where(School.name == "Primarschule Volta")).one()
    wasgenring = db.exec(select(School).where(School.name == "Primarschule Wasgenring")).one()
    db.add_all([
        User(full_name="E2E Administrator", email="admin@e2e.test",
             hashed_password=hash_password("E2eAdmin123!"), role=Role.ADMIN, school_id=volta.id, is_approved=True),
        User(full_name="E2E Wasgenring Admin", email="wasgenring@e2e.test",
             hashed_password=hash_password("E2eWasgenring123!"), role=Role.ADMIN, school_id=wasgenring.id, is_approved=True),
        User(full_name="E2E Teacher", email="teacher@e2e.test",
             hashed_password=hash_password("E2eTeacher123!"), role=Role.TEACHER, is_approved=True),
        Subject(name="E2E Mathematik", level="primary", grades="1-6"),
    ])
    db.commit()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18000)
