from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import create_db_and_tables
from routers import auth, requests, applications, subjects, teachers, dashboard, profile, schools
from models.school import School  # noqa: F401 - register SQLModel metadata

app = FastAPI(
    title="EduSub API",
    description="Substitute Teacher Coordination Platform — FHNW Web-based Applications HS26",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Profile pictures may be displayed in the UI. Teacher qualification documents
# are private and MUST NOT be exposed through StaticFiles.
os.makedirs("uploads/documents", exist_ok=True)
os.makedirs("uploads/profile_pictures", exist_ok=True)
app.mount("/uploads/profile_pictures", StaticFiles(directory="uploads/profile_pictures"), name="profile_pictures")

# Routers
PREFIX = "/api/v1"
app.include_router(auth.router,         prefix=PREFIX)
app.include_router(requests.router,     prefix=PREFIX)
app.include_router(applications.router, prefix=PREFIX)
app.include_router(subjects.router,     prefix=PREFIX)
app.include_router(teachers.router,     prefix=PREFIX)
app.include_router(dashboard.router,    prefix=PREFIX)
app.include_router(profile.router,      prefix=PREFIX)
app.include_router(schools.router,      prefix=PREFIX)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"message": "EduSub API is running"}
