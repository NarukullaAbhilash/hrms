from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db

from app.models.user import User
from app.models.audit_log import AuditLog


router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# ============================================================
# HELPER - CREATE AUDIT LOG
# ============================================================

def create_audit_log(
    db: Session,
    current_user: User,
    action: str,
    entity: str,
    entity_id: int,
    description: str,
):
    audit_log = AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description,
        ip_address=None,
    )

    db.add(audit_log)


# ============================================================
# ASSIGN USER ROLE
# ADMIN ONLY
# ============================================================

@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # ALLOWED ROLES
    # --------------------------------------------------------

    allowed_roles = [
        "admin",
        "hr",
        "employee"
    ]

    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be admin, hr, or employee"
        )

    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # SAVE OLD ROLE
    # --------------------------------------------------------

    old_role = user.role

    # --------------------------------------------------------
    # UPDATE ROLE
    # --------------------------------------------------------

    user.role = role

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_admin,
        action="USER_ROLE_CHANGED",
        entity="User",
        entity_id=user.id,
        description=(
            f"User {user.full_name} ({user.email}) role changed "
            f"from {old_role} to {role} by "
            f"{current_admin.email}"
        ),
    )

    # --------------------------------------------------------
    # SAVE CHANGES
    # --------------------------------------------------------

    db.commit()
    db.refresh(user)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }