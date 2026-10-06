from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# DATABASE
# ============================================================

from app.database import Base, engine


# ============================================================
# MODELS
# ============================================================

from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.leave_balance import LeaveBalance
from app.models.payroll import Payroll
from app.models.audit_log import AuditLog


# ============================================================
# ROUTERS
# ============================================================

from app.routers.auth import router as auth_router
from app.routers.rbac import router as rbac_router
from app.routers.users import router as users_router
from app.routers.employees import router as employees_router
from app.routers.attendance import router as attendance_router
from app.routers.leave import router as leave_router
from app.routers.payroll import router as payroll_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router
from app.routers.audit_logs import router as audit_logs_router


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="HRMS API",
    description="Human Resource Management System API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# INCLUDE ROUTERS
# ============================================================

app.include_router(auth_router)

app.include_router(rbac_router)

app.include_router(users_router)

app.include_router(employees_router)

app.include_router(attendance_router)

app.include_router(leave_router)

app.include_router(payroll_router)

app.include_router(dashboard_router)

app.include_router(reports_router)

app.include_router(audit_logs_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "HRMS API is running",
        "status": "success",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }