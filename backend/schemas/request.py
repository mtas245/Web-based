"""OpenAPI request/response contracts for substitute-request CRUD."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from models.request import GRADE_LEVELS, RequestStatus


def validate_grade(value: str) -> str:
    if value not in GRADE_LEVELS:
        raise ValueError("Unknown grade level")
    return value


def validate_time_slot(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    parts = value.split("-")
    if len(parts) != 2:
        raise ValueError("Time slot must use HH:MM-HH:MM")
    try:
        start = datetime.strptime(parts[0].strip(), "%H:%M").time()
        end = datetime.strptime(parts[1].strip(), "%H:%M").time()
    except ValueError as exc:
        raise ValueError("Time slot must use HH:MM-HH:MM") from exc
    if start >= end:
        raise ValueError("End time must be after start time")
    return f"{start:%H:%M}-{end:%H:%M}"


class RequestCreate(BaseModel):
    date: date = Field(description="Date of the lesson; today or later")
    grade_level: str = Field(examples=["3a"])
    subject_id: int = Field(gt=0, examples=[1])
    time_slot: Optional[str] = Field(default=None, examples=["08:00-10:00"])
    note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("grade_level")
    @classmethod
    def check_grade(cls, value: str) -> str:
        return validate_grade(value)

    @field_validator("date")
    @classmethod
    def check_date(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Request date must not be in the past")
        return value

    @field_validator("time_slot")
    @classmethod
    def check_slot(cls, value: Optional[str]) -> Optional[str]:
        return validate_time_slot(value)


class RequestUpdate(BaseModel):
    date: Optional[date] = None
    grade_level: Optional[str] = None
    subject_id: Optional[int] = Field(default=None, gt=0)
    time_slot: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("grade_level")
    @classmethod
    def check_grade(cls, value: Optional[str]) -> Optional[str]:
        return validate_grade(value) if value is not None else None

    @field_validator("date")
    @classmethod
    def check_date(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value < date.today():
            raise ValueError("Request date must not be in the past")
        return value

    @field_validator("time_slot")
    @classmethod
    def check_slot(cls, value: Optional[str]) -> Optional[str]:
        return validate_time_slot(value)


class RequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    grade_level: str
    subject_id: int
    time_slot: Optional[str]
    note: Optional[str]
    status: RequestStatus
    expires_at: Optional[datetime]
    created_by: int
    created_at: datetime
