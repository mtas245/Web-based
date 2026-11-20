from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import List, Optional
import os, shutil

from database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.school import School
from schemas.auth import RegisterRequest, RegisterResponse, TokenResponse, ChangePasswordRequest
from services.auth_service import register_user, authenticate_user, change_password

router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email + password, returns JWT."""
    return authenticate_user(form_data.username, form_data.password, db)


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    subjects: Optional[str] = Form(default=""),   # comma-separated subject IDs
    documents: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    """
    Register a new teacher account.
    Accepts multipart/form-data so documents can be uploaded alongside the form fields.
    """
    # Parse subject IDs
    subject_ids = []
    if subjects:
        subject_ids = [int(s) for s in subjects.split(",") if s.strip().isdigit()]

    data = RegisterRequest(
        full_name=full_name,
        email=email,
        phone=phone,
        password=password,
        subjects=subject_ids,
    )
    user = register_user(data, db)

    # Save uploaded documents
    saved_paths = []
    for doc in documents:
        if doc.filename:
            dest = os.path.join(UPLOAD_DIR, f"{user.id}_{doc.filename}")
            with open(dest, "wb") as f:
                shutil.copyfileobj(doc.file, f)
            saved_paths.append(dest)

    if saved_paths:
        user.documents_path = ",".join(saved_paths)
        db.add(user)
        db.commit()

    return RegisterResponse(
        id=user.id,
        email=user.email,
        is_approved=user.is_approved,
        message="Registration successful. Waiting for admin approval.",
    )


@router.post("/change-password", status_code=204)
def change_pwd(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password."""
    change_password(current_user, data.current_password, data.new_password, db)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return basic info about the currently logged-in user."""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "school_id": current_user.school_id,
        "school_name": (school.name if current_user.school_id and (school := db.get(School, current_user.school_id)) else None),
        "is_approved": current_user.is_approved,
        "personal_number": current_user.personal_number,
    }
