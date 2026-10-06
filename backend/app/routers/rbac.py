from fastapi import APIRouter, Depends

from app.auth.dependencies import (
    get_current_user,
    require_admin,
    require_hr,
    require_admin_or_hr,
)
from app.models.user import User


router = APIRouter(
    prefix="/rbac",
    tags=["Role-Based Access Control"]
)


# ============================================================
# ANY LOGGED-IN USER
# ============================================================

@router.get("/employee")
def employee_access(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": "Authenticated user access granted",
        "user_id": current_user.id,
        "role": current_user.role
    }


# ============================================================
# ADMIN ONLY
# ============================================================

@router.get("/admin")
def admin_access(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "role": current_user.role
    }


# ============================================================
# HR ONLY
# ============================================================

@router.get("/hr")
def hr_access(
    current_user: User = Depends(require_hr)
):
    return {
        "message": "HR access granted",
        "user_id": current_user.id,
        "role": current_user.role
    }


# ============================================================
# ADMIN OR HR
# ============================================================

@router.get("/admin-or-hr")
def admin_or_hr_access(
    current_user: User = Depends(require_admin_or_hr)
):
    return {
        "message": "Admin or HR access granted",
        "user_id": current_user.id,
        "role": current_user.role
    }