from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_db
from core.dependencies import require_admin, require_teacher
from models.user import User
from services import request_service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/pending", response_model=List[dict])
def list_pending(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: list all pending applications."""
    apps = request_service.get_pending_applications(db, _admin.school_id)
    return [_serialize(a) for a in apps]


@router.patch("/{application_id}/approve", response_model=dict)
def approve(
    application_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: approve an application (auto-rejects all others for same request)."""
    app = request_service.approve_application(application_id, db, _admin.school_id)
    return _serialize(app)


@router.patch("/{application_id}/reject", response_model=dict)
def reject(
    application_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: reject an application."""
    app = request_service.reject_application(application_id, db, _admin.school_id)
    return _serialize(app)


@router.get("/my", response_model=List[dict])
def my_applications(
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher: list all of my applications with their status."""
    apps = request_service.get_applications_for_teacher(teacher.id, db)
    return [_serialize(a) for a in apps]


@router.get("/my/approved", response_model=List[dict])
def my_approved(
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher: list only approved (confirmed) assignments."""
    apps = request_service.get_approved_assignments_for_teacher(teacher.id, db)
    return [_serialize(a) for a in apps]


def _serialize(a) -> dict:
    return {
        "id": a.id,
        "request_id": a.request_id,
        "teacher_id": a.teacher_id,
        "status": a.status,
        "applied_at": a.applied_at.isoformat(),
    }
