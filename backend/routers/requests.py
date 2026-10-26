"""Substitute request REST API, backed by the same services and database as other routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from database import get_db
from core.dependencies import require_admin, require_teacher
from models.user import User
from models.request import GRADE_LEVELS
from schemas.request import RequestCreate, RequestRead, RequestUpdate
from services import request_service

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("/", response_model=List[RequestRead])
def list_all_requests(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Admin: list all substitute requests."""
    return request_service.get_all_requests(db)


@router.post("/", response_model=RequestRead, status_code=201, responses={
    400: {"description": "Invalid business data, such as an unknown subject"},
    401: {"description": "Missing or invalid bearer token"},
    403: {"description": "Administrator role required"},
    422: {"description": "Input schema validation failed"},
})
def create_request(
    payload: RequestCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: create a substitute request from a documented JSON request body."""
    return request_service.create_request(
        payload.date, payload.grade_level, payload.subject_id,
        payload.time_slot, payload.note, admin.id, db
    )


@router.get("/open", response_model=List[RequestRead])
def list_open_requests(
    grade_level: Optional[str] = None,
    _teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher: list currently open requests, optionally filtered by grade."""
    reqs = request_service.get_open_requests(db)
    if grade_level:
        if grade_level not in GRADE_LEVELS:
            raise HTTPException(status_code=422, detail="Invalid grade_level")
        return [r for r in reqs if r.grade_level == grade_level]
    return reqs


@router.get("/grade-levels", response_model=List[str])
def grade_levels():
    """Public: supported grade-level identifiers."""
    return GRADE_LEVELS


@router.delete("/cleanup/expired", response_model=dict)
def cleanup_expired(
    _admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """Admin: remove expired open requests (legacy maintenance operation)."""
    return {"deleted": request_service.delete_expired_requests(db)}


@router.get("/{request_id}", response_model=RequestRead, responses={
    404: {"description": "Request not found"},
})
def get_request(
    request_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: retrieve a single substitute request."""
    return request_service.get_request(request_id, db)


@router.patch("/{request_id}", response_model=RequestRead, responses={
    404: {"description": "Request not found"},
    409: {"description": "Only open requests can be edited"},
    422: {"description": "Invalid update"},
})
def update_request(
    request_id: int,
    payload: RequestUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: partially update an open substitute request."""
    return request_service.update_request(request_id, payload.model_dump(exclude_unset=True), db)


@router.delete("/{request_id}", status_code=204, responses={
    404: {"description": "Request not found"},
    409: {"description": "Only open requests without applications can be deleted"},
})
def delete_request(
    request_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: delete an open request that has no applications."""
    request_service.delete_request(request_id, db)


@router.patch("/{request_id}/close", response_model=RequestRead)
def close_request(
    request_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: close an open request."""
    return request_service.close_request(request_id, db)


@router.post("/{request_id}/apply", response_model=dict, status_code=201)
def apply(
    request_id: int,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Teacher: apply for an open request."""
    application = request_service.apply_for_request(request_id, teacher.id, db)
    return {"id": application.id, "request_id": application.request_id, "status": application.status}
