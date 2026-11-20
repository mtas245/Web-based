"""Public directory of participating schools; no personal information."""
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_db
from models.school import School

router = APIRouter(prefix="/schools", tags=["schools"])


@router.get("/", response_model=List[School])
def list_schools(db: Session = Depends(get_db)):
    return db.exec(select(School).where(School.is_active == True).order_by(School.name)).all()
