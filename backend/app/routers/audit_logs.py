from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get("")
def get_audit_logs(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "description": log.description,
            "timestamp": log.timestamp,
            "ip_address": log.ip_address,
        }
        for log in logs
    ]