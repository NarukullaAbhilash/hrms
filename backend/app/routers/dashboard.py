from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin_or_hr
from app.database import get_db

from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.payroll import Payroll


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard Management"]
)


@router.get("/admin")
def admin_dashboard(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    today = date.today()

    # ============================================================
    # EMPLOYEE COUNTS
    # ============================================================

    total_employees = (
        db.query(Employee)
        .count()
    )

    active_employees = (
        db.query(Employee)
        .filter(Employee.is_active.is_(True))
        .count()
    )

    inactive_employees = (
        db.query(Employee)
        .filter(Employee.is_active.is_(False))
        .count()
    )

    # ============================================================
    # TODAY'S ATTENDANCE
    # ============================================================

    today_attendance = (
        db.query(Attendance)
        .filter(Attendance.attendance_date == today)
        .all()
    )

    total_attendance_records = len(today_attendance)

    present_today = sum(
        1
        for record in today_attendance
        if record.check_in is not None
    )

    checked_in = sum(
        1
        for record in today_attendance
        if record.check_in is not None
        and record.check_out is None
    )

    checked_out = sum(
        1
        for record in today_attendance
        if record.check_in is not None
        and record.check_out is not None
    )

    # ============================================================
    # LEAVE COUNTS
    # ============================================================

    pending_leaves = (
        db.query(Leave)
        .filter(Leave.status == "pending")
        .count()
    )

    approved_leaves = (
        db.query(Leave)
        .filter(Leave.status == "approved")
        .count()
    )

    rejected_leaves = (
        db.query(Leave)
        .filter(Leave.status == "rejected")
        .count()
    )

    # ============================================================
    # PAYROLL COUNTS
    # ============================================================

    generated_payroll = (
        db.query(Payroll)
        .filter(Payroll.status == "generated")
        .count()
    )

    locked_payroll = (
        db.query(Payroll)
        .filter(Payroll.status == "locked")
        .count()
    )

    credited_payroll = (
        db.query(Payroll)
        .filter(Payroll.status == "credited")
        .count()
    )

    # ============================================================
    # DASHBOARD RESPONSE
    # ============================================================

    return {
        "dashboard_date": today.isoformat(),

        "employees": {
            "total": total_employees,
            "active": active_employees,
            "inactive": inactive_employees
        },

        "attendance_today": {
            "total_records": total_attendance_records,
            "present": present_today,
            "checked_in": checked_in,
            "checked_out": checked_out
        },

        "leaves": {
            "pending": pending_leaves,
            "approved": approved_leaves,
            "rejected": rejected_leaves
        },

        "payroll": {
            "generated": generated_payroll,
            "locked": locked_payroll,
            "credited": credited_payroll
        }
    }