"""Create a local EduSub administrator for development and Swagger testing.

Usage (run from backend/):
    python scripts/create_local_admin.py

Never commit passwords or the local SQLite database.
"""
from getpass import getpass
from pathlib import Path
import sys

# Allow running the script directly from any working directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlmodel import Session, select

# Import API registration to ensure all relationship models are loaded.
from main import app as _app  # noqa: F401
from database import create_db_and_tables, engine
from models.user import Role, User
from models.school import School
from core.security import hash_password


def main():
    db_file = BACKEND_DIR / "edusub.db"
    print("EduSub local administrator setup")
    print(f"Database: {db_file}")
    # database.py uses a relative SQLite URL. Fail instead of silently writing
    # to the wrong SQLite file if launched from outside backend/.
    if Path.cwd().resolve() != BACKEND_DIR:
        print("Please run this command from the backend directory.")
        print("  python scripts/create_local_admin.py")
        sys.exit(1)

    create_db_and_tables()
    email = input("Administrator email: ").strip().lower()
    if not email or "@" not in email:
        print("Please enter a valid email address.")
        sys.exit(1)

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing is not None:
            print("An account with this email already exists. No changes were made.")
            sys.exit(1)

        name = input("Administrator name: ").strip()
        if not name:
            print("A name is required.")
            sys.exit(1)

        print("Administrator type: 1 = school administrator, 2 = platform administrator")
        role_choice = input("Select type [1]: ").strip() or "1"
        if role_choice not in {"1", "2"}:
            sys.exit("Invalid administrator type")
        school_id = None
        role = Role.PLATFORM_ADMIN if role_choice == "2" else Role.ADMIN
        if role == Role.ADMIN:
            schools = session.exec(select(School).order_by(School.name)).all()
            for school in schools:
                print(f"{school.id}: {school.name}")
            try:
                school_id = int(input("School ID: "))
            except ValueError:
                sys.exit("Invalid school ID")
            if not session.get(School, school_id):
                sys.exit("School does not exist. Run seed_demo_schools.py first.")

        password = getpass("Password (minimum 12 characters): ")
        confirm = getpass("Confirm password: ")
        if len(password) < 12 or password != confirm:
            print("Passwords must match and contain at least 12 characters.")
            sys.exit(1)
        if len(password.encode("utf-8")) > 72:
            print("Bcrypt passwords must be at most 72 UTF-8 bytes. Choose a shorter password.")
            sys.exit(1)

        admin = User(
            full_name=name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            school_id=school_id,
            is_approved=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)

    print(f"Administrator created successfully (id={admin.id}).")
    print("Open /docs and authenticate using POST /api/v1/auth/login.")
    print("Use your email as the username. Do not share your password.")


if __name__ == "__main__":
    main()
