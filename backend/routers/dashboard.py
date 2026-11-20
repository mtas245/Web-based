from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from database import get_db
from core.dependencies import require_admin, require_teacher
from models.user import User, Role
from models.request import SubstituteRequest, RequestStatus
from models.school import School
from models.application import Application, ApplicationStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=dict)
def admin_stats(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin dashboard summary:
    - total open / filled / closed requests
    - pending applications count
    - pending teacher approvals count
    """
    total_open = db.exec(
        select(func.count(SubstituteRequest.id))
        .where(SubstituteRequest.school_id == _admin.school_id)
        .where(SubstituteRequest.status == RequestStatus.OPEN)
    ).one()

    total_filled = db.exec(
        select(func.count(SubstituteRequest.id))
        .where(SubstituteRequest.school_id == _admin.school_id)
        .where(SubstituteRequest.status == RequestStatus.FILLED)
    ).one()

    total_closed = db.exec(
        select(func.count(SubstituteRequest.id))
        .where(SubstituteRequest.school_id == _admin.school_id)
        .where(SubstituteRequest.status == RequestStatus.CLOSED)
    ).one()

    pending_applications = db.exec(
        select(func.count(Application.id))
        .join(SubstituteRequest)
        .where(SubstituteRequest.school_id == _admin.school_id)
        .where(Application.status == ApplicationStatus.PENDING)
    ).one()

    # Teacher approval is a platform responsibility, not a school-admin action.
    pending_teachers = 0

    return {
        "school_id": _admin.school_id,
        "requests": {
            "open": total_open,
            "filled": total_filled,
            "closed": total_closed,
        },
        "pending_applications": pending_applications,
        "pending_teacher_approvals": pending_teachers,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/teacher", response_model=dict)
def teacher_stats(
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """
    Teacher dashboard summary:
    - number of available (open, non-expired) requests
    - number of my pending / approved applications
    """
    now = datetime.utcnow()

    available = db.exec(
        select(func.count(SubstituteRequest.id))
        .where(SubstituteRequest.status == RequestStatus.OPEN)
        .where(
            (SubstituteRequest.expires_at == None) |
            (SubstituteRequest.expires_at > now)
        )
    ).one()

    my_pending = db.exec(
        select(func.count(Application.id))
        .where(Application.teacher_id == teacher.id)
        .where(Application.status == ApplicationStatus.PENDING)
    ).one()

    my_approved = db.exec(
        select(func.count(Application.id))
        .where(Application.teacher_id == teacher.id)
        .where(Application.status == ApplicationStatus.APPROVED)
    ).one()

    return {
        "available_requests": available,
        "my_pending_applications": my_pending,
        "my_approved_assignments": my_approved,
        "generated_at": datetime.utcnow().isoformat(),
    }
