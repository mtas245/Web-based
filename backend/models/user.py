from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from models.subject import UserSubject
    from models.application import Application


class Role(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    PLATFORM_ADMIN = "platform_admin"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    personal_number: Optional[str] = Field(default=None, unique=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: Role = Field(default=Role.TEACHER)
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")
    is_approved: bool = Field(default=False)
    phone: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    documents_path: Optional[str] = None  # comma-separated paths
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user_subjects: List["UserSubject"] = Relationship(back_populates="user")
    applications: List["Application"] = Relationship(back_populates="teacher")
