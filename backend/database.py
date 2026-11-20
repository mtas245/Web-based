from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import inspect, text

DATABASE_URL = "sqlite:///./edusub.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    # Register models before metadata.create_all(), including the new School entity.
    import models.school  # noqa: F401
    import models.user  # noqa: F401
    import models.subject  # noqa: F401
    import models.request  # noqa: F401
    import models.application  # noqa: F401

    SQLModel.metadata.create_all(engine)
    # Backward-compatible migration for existing local SQLite installations.
    # SQLite ADD COLUMN cannot introduce a populated NOT NULL foreign key directly.
    with engine.begin() as connection:
        for table in ("user", "substituterequest"):
            columns = {col["name"] for col in inspect(connection).get_columns(table)}
            if "school_id" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN school_id INTEGER REFERENCES school(id)"))

    from models.school import School
    from models.user import User, Role
    from models.request import SubstituteRequest
    with Session(engine) as session:
        default = session.exec(select(School).where(School.name == "Primarschule Volta")).first()
        if default is None:
            default = School(name="Primarschule Volta", city="Basel")
            session.add(default)
            session.flush()
        for admin in session.exec(select(User).where(User.role == Role.ADMIN, User.school_id == None)).all():
            admin.school_id = default.id
            session.add(admin)
        for request in session.exec(select(SubstituteRequest).where(SubstituteRequest.school_id == None)).all():
            request.school_id = default.id
            session.add(request)
        session.commit()


def get_db():
    with Session(engine) as session:
        yield session
