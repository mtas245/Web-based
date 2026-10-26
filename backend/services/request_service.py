from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select

from models.request import SubstituteRequest, RequestStatus, GRADE_LEVELS
from models.application import Application, ApplicationStatus
from models.user import User
from models.subject import Subject


# ── helpers ──────────────────────────────────────────────────────────────────

def _calculate_expires_at(date, time_slot: Optional[str]) -> Optional[datetime]:
    """Returns datetime 12h before the assignment starts, or None if no time_slot."""
    if not time_slot:
        return None
    try:
        start_str = time_slot.split("-")[0].strip()   # "HH:MM"
        start_dt = datetime.combine(date, datetime.strptime(start_str, "%H:%M").time())
        return start_dt - timedelta(hours=12)
    except Exception:
        return None


def _assert_not_expired(req: SubstituteRequest) -> None:
    if req.expires_at and datetime.utcnow() > req.expires_at:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This request has expired")


# ── request CRUD ─────────────────────────────────────────────────────────────

def create_request(
    date,
    grade_level: str,
    subject_id: int,
    time_slot: Optional[str],
    note: Optional[str],
    created_by: int,
    db: Session,
) -> SubstituteRequest:
    if grade_level not in GRADE_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid grade level: {grade_level}")

    if not db.get(Subject, subject_id):
        raise HTTPException(status_code=400, detail="Subject does not exist")

    expires_at = _calculate_expires_at(date, time_slot)

    req = SubstituteRequest(
        date=date,
        grade_level=grade_level,
        subject_id=subject_id,
        time_slot=time_slot,
        note=note,
        created_by=created_by,
        expires_at=expires_at,
        status=RequestStatus.OPEN,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_all_requests(db: Session) -> List[SubstituteRequest]:
    return db.exec(select(SubstituteRequest).order_by(SubstituteRequest.date)).all()


def get_open_requests(db: Session) -> List[SubstituteRequest]:
    now = datetime.utcnow()
    return db.exec(
        select(SubstituteRequest)
        .where(SubstituteRequest.status == RequestStatus.OPEN)
        .where(
            (SubstituteRequest.expires_at == None) |
            (SubstituteRequest.expires_at > now)
        )
        .order_by(SubstituteRequest.date)
    ).all()


def get_requests_by_grade(grade_level: str, db: Session) -> List[SubstituteRequest]:
    return db.exec(
        select(SubstituteRequest)
        .where(SubstituteRequest.grade_level == grade_level)
        .order_by(SubstituteRequest.date)
    ).all()


def delete_request(request_id: int, db: Session) -> None:
    req = db.get(SubstituteRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=409, detail="Only open requests may be deleted")
    if db.exec(select(Application).where(Application.request_id == request_id)).first():
        raise HTTPException(status_code=409, detail="Requests with applications cannot be deleted")
    db.delete(req)
    db.commit()


def close_request(request_id: int, db: Session) -> SubstituteRequest:
    req = db.get(SubstituteRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=409, detail="Only open requests may be closed")
    req.status = RequestStatus.CLOSED
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def delete_expired_requests(db: Session) -> int:
    """Delete all OPEN requests that have passed their expires_at. Returns count deleted."""
    now = datetime.utcnow()
    expired = db.exec(
        select(SubstituteRequest)
        .where(SubstituteRequest.status == RequestStatus.OPEN)
        .where(SubstituteRequest.expires_at != None)
        .where(SubstituteRequest.expires_at <= now)
    ).all()
    for req in expired:
        db.delete(req)
    db.commit()
    return len(expired)


# ── application flow ─────────────────────────────────────────────────────────

def apply_for_request(request_id: int, teacher_id: int, db: Session) -> Application:
    req = db.get(SubstituteRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=400, detail="Request is no longer open")
    _assert_not_expired(req)

    # Prevent duplicate application
    existing = db.exec(
        select(Application)
        .where(Application.request_id == request_id)
        .where(Application.teacher_id == teacher_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied for this request")

    app = Application(request_id=request_id, teacher_id=teacher_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_pending_applications(db: Session) -> List[Application]:
    return db.exec(
        select(Application).where(Application.status == ApplicationStatus.PENDING)
    ).all()


def approve_application(application_id: int, db: Session) -> Application:
    app = db.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Status transitions are guarded so a request cannot receive two approvals.
    req = db.get(SubstituteRequest, app.request_id)
    if not req or req.status != RequestStatus.OPEN or app.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Application or request is no longer pending/open")
    app.status = ApplicationStatus.APPROVED

    # Mark request as filled
    if req:
        req.status = RequestStatus.FILLED
        db.add(req)

        # Reject all other pending applications for this request
        others = db.exec(
            select(Application)
            .where(Application.request_id == req.id)
            .where(Application.id != application_id)
            .where(Application.status == ApplicationStatus.PENDING)
        ).all()
        for other in others:
            other.status = ApplicationStatus.REJECTED
            db.add(other)

    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def reject_application(application_id: int, db: Session) -> Application:
    app = db.get(Application, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != ApplicationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Only pending applications can be rejected")
    app.status = ApplicationStatus.REJECTED
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_approved_assignments_for_teacher(teacher_id: int, db: Session) -> List[Application]:
    return db.exec(
        select(Application)
        .where(Application.teacher_id == teacher_id)
        .where(Application.status == ApplicationStatus.APPROVED)
    ).all()


def get_applications_for_teacher(teacher_id: int, db: Session) -> List[Application]:
    return db.exec(
        select(Application).where(Application.teacher_id == teacher_id)
    ).all()


def get_request(request_id: int, db: Session) -> SubstituteRequest:
    """Get a request for the authenticated admin; fail with HTTP 404."""
    req = db.get(SubstituteRequest, request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


def update_request(request_id: int, updates: dict, db: Session) -> SubstituteRequest:
    """Apply validated partial edits to an OPEN request."""
    req = get_request(request_id, db)
    if req.status != RequestStatus.OPEN:
        raise HTTPException(status_code=409, detail="Only open requests may be edited")
    if "subject_id" in updates:
        if updates["subject_id"] is None or not db.get(Subject, updates["subject_id"]):
            raise HTTPException(status_code=400, detail="Subject does not exist")
    if "grade_level" in updates and updates["grade_level"] not in GRADE_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid grade level")
    for name in ("date", "grade_level", "subject_id", "time_slot", "note"):
        if name in updates:
            if updates[name] is None and name in ("date", "grade_level", "subject_id"):
                raise HTTPException(status_code=422, detail=f"{name} must not be null")
            setattr(req, name, updates[name])
    req.expires_at = _calculate_expires_at(req.date, req.time_slot)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req
