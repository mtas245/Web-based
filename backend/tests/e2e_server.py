"""Disposable local backend for Playwright browser tests; never uses edusub.db in the project."""

import os
from pathlib import Path
import sys
import tempfile

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# SQLite's relative path and upload folders now live in a disposable directory.
os.chdir(tempfile.mkdtemp(prefix="edusub-e2e-"))

from sqlmodel import SQLModel, Session  # noqa: E402
from database import engine  # noqa: E402
from core.security import hash_password  # noqa: E402
from models.user import User, Role  # noqa: E402
from models.subject import Subject  # noqa: E402
from main import app  # noqa: E402
import uvicorn  # noqa: E402

SQLModel.metadata.create_all(engine)
with Session(engine) as db:
    db.add_all([
        User(full_name="E2E Administrator", email="admin@e2e.test",
             hashed_password=hash_password("E2eAdmin123!"), role=Role.ADMIN, is_approved=True),
        User(full_name="E2E Teacher", email="teacher@e2e.test",
             hashed_password=hash_password("E2eTeacher123!"), role=Role.TEACHER, is_approved=True),
        Subject(name="E2E Mathematik", level="primary", grades="1-6"),
    ])
    db.commit()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18000)
