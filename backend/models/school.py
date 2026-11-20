from typing import Optional

from sqlmodel import Field, SQLModel


class School(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    city: str = Field(default="Basel")
    is_active: bool = Field(default=True)
