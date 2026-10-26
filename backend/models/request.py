from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import date as DateType, datetime
from enum import Enum

if TYPE_CHECKING:
    from models.application import Application


GRADE_LEVELS = [
    "KG1", "KG2",
    "1a", "1b", "2a", "2b",
    "3a", "3b", "4a", "4b",
    "5a", "5b", "6a", "6b",
]


class RequestStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CLOSED = "closed"


class SubstituteRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: DateType
    grade_level: str
    subject_id: int = Field(foreign_key="subject.id")
    time_slot: Optional[str] = None   # format: "HH:MM-HH:MM"
    note: Optional[str] = None
    status: RequestStatus = Field(default=RequestStatus.OPEN)
    expires_at: Optional[datetime] = None
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    applications: List["Application"] = Relationship(back_populates="request")
