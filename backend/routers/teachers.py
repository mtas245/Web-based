from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlmodel import Session

from database import get_db
from core.dependencies import require_platform_admin
from models.user import User
from services import profile_service

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("/", response_model=List[dict])
def list_teachers(
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Admin: list all registered teachers."""
    return [_serialize(t) for t in profile_service.get_all_teachers(db)]


@router.get("/pending", response_model=List[dict])
def list_pending_teachers(
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Admin: list teachers waiting for approval."""
    return [_serialize(t) for t in profile_service.get_pending_teachers(db)]


@router.patch("/{teacher_id}/approve", response_model=dict)
def approve_teacher(
    teacher_id: int,
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Admin: approve a teacher account."""
    teacher = profile_service.approve_teacher(teacher_id, db)
    return _serialize(teacher)


@router.delete("/{teacher_id}/reject", status_code=204)
def reject_teacher(
    teacher_id: int,
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Admin: reject (delete) a teacher account."""
    profile_service.reject_teacher(teacher_id, db)


@router.get("/{teacher_id}", response_model=dict)
def get_teacher_profile(
    teacher_id: int,
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Admin: view a teacher's full profile."""
    teacher = profile_service.get_user_by_id(teacher_id, db)
    subjects = profile_service.get_user_subjects(teacher_id, db)
    data = _serialize(teacher)
    data["subjects"] = [{"id": s.id, "name": s.name} for s in subjects]
    return data


def _serialize(u: User) -> dict:
    return {
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "personal_number": u.personal_number,
        "is_approved": u.is_approved,
        "bio": u.bio,
        "profile_picture": u.profile_picture,
        "documents_path": u.documents_path,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
