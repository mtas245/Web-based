"""Seed fictional EduSub demo organisations using real Basel school names.

Run from backend/: python scripts/seed_demo_schools.py
No real school is affiliated with EduSub and no real vacancies are created.
"""
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from main import app as _app  # noqa: F401
from database import create_db_and_tables, engine
from models.school import School
from sqlmodel import Session, select

SCHOOL_NAMES = (
    "Primarschule Volta",
    "Primarschule Wasgenring",
    "Primarschule Thierstein",
    "Primarschule Rittergasse",
    "Primarschule Bruderholz",
)


def main():
    if Path.cwd().resolve() != BACKEND_DIR:
        sys.exit("Please run this script from the backend directory.")
    create_db_and_tables()
    with Session(engine) as session:
        for name in SCHOOL_NAMES:
            if not session.exec(select(School).where(School.name == name)).first():
                session.add(School(name=name, city="Basel"))
        session.commit()
        for school in session.exec(select(School).order_by(School.name)).all():
            print(f"{school.id}: {school.name}")
    print("Demo only: no affiliation with any listed school.")


if __name__ == "__main__":
    main()
