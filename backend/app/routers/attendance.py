from calendar import monthrange
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_hr,
)
from app.database import get_db

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.models.audit_log import AuditLog

from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceSummaryResponse,
)


# ============================================================
# ATTENDANCE ROUTER
# ============================================================

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance Management"]
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
# CHECK-IN
# ============================================================

@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED
)
def check_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # FIND EMPLOYEE USING LOGGED-IN USER EMAIL
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    # --------------------------------------------------------
    # CHECK EMPLOYEE STATUS
    # --------------------------------------------------------

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee account is inactive"
        )

    today = date.today()

    # --------------------------------------------------------
    # PREVENT DUPLICATE CHECK-IN
    # --------------------------------------------------------

    existing_attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == today
        )
        .first()
    )

    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked for today"
        )

    # --------------------------------------------------------
    # CREATE ATTENDANCE
    # --------------------------------------------------------

    attendance = Attendance(
        employee_id=employee.id,
        attendance_date=today,
        check_in=datetime.now(),
        working_hours=0
    )

    db.add(attendance)

    # Get attendance ID before commit
    db.flush()

    # --------------------------------------------------------
    # AUDIT LOG - CHECK IN
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="ATTENDANCE_CHECK_IN",
        entity="Attendance",
        entity_id=attendance.id,
        description=(
            f"Employee {employee.full_name} "
            f"({employee.employee_code}) checked in on "
            f"{today}"
        ),
    )

    db.commit()
    db.refresh(attendance)

    return attendance


# ============================================================
# CHECK-OUT
# ============================================================

@router.post(
    "/check-out",
    response_model=AttendanceResponse
)
def check_out(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # FIND EMPLOYEE
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee account is inactive"
        )

    today = date.today()

    # --------------------------------------------------------
    # FIND TODAY'S ATTENDANCE
    # --------------------------------------------------------

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == today
        )
        .first()
    )

    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please check in first"
        )

    # --------------------------------------------------------
    # PREVENT DUPLICATE CHECK-OUT
    # --------------------------------------------------------

    if attendance.check_out is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already checked out for today"
        )

    # --------------------------------------------------------
    # CHECK-OUT TIME
    # --------------------------------------------------------

    attendance.check_out = datetime.now()

    # --------------------------------------------------------
    # CALCULATE WORKING HOURS
    # --------------------------------------------------------

    duration = (
        attendance.check_out -
        attendance.check_in
    )

    attendance.working_hours = round(
        duration.total_seconds() / 3600,
        2
    )

    # --------------------------------------------------------
    # AUDIT LOG - CHECK OUT
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="ATTENDANCE_CHECK_OUT",
        entity="Attendance",
        entity_id=attendance.id,
        description=(
            f"Employee {employee.full_name} "
            f"({employee.employee_code}) checked out on "
            f"{today}. "
            f"Working hours: {attendance.working_hours}"
        ),
    )

    db.commit()
    db.refresh(attendance)

    return attendance


# ============================================================
# MY ATTENDANCE HISTORY
# ============================================================

@router.get(
    "/my",
    response_model=list[AttendanceResponse]
)
def get_my_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # FIND EMPLOYEE
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.email == current_user.email)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    # --------------------------------------------------------
    # GET ATTENDANCE HISTORY
    # --------------------------------------------------------

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee.id
        )
        .order_by(
            Attendance.attendance_date.desc()
        )
        .all()
    )

    return attendance


# ============================================================
# GET EMPLOYEE ATTENDANCE
# ADMIN / HR
# ============================================================

@router.get(
    "/employee/{employee_id}",
    response_model=list[AttendanceResponse]
)
def get_employee_attendance(
    employee_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    attendance = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id
        )
        .order_by(
            Attendance.attendance_date.desc()
        )
        .all()
    )

    return attendance


# ============================================================
# MONTHLY ATTENDANCE SUMMARY
# ============================================================

@router.get(
    "/summary/{employee_id}",
    response_model=AttendanceSummaryResponse
)
def attendance_summary(
    employee_id: int,
    month: int,
    year: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # VALIDATE MONTH
    # --------------------------------------------------------

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )

    # --------------------------------------------------------
    # VALIDATE YEAR
    # --------------------------------------------------------

    if year < 2000 or year > 2100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid year"
        )

    # --------------------------------------------------------
    # FIND EMPLOYEE
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # --------------------------------------------------------
    # MONTH DATE RANGE
    # --------------------------------------------------------

    first_day = date(
        year,
        month,
        1
    )

    last_day = date(
        year,
        month,
        monthrange(year, month)[1]
    )

    # --------------------------------------------------------
    # GET MONTHLY ATTENDANCE
    # --------------------------------------------------------

    attendance_records = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= first_day,
            Attendance.attendance_date <= last_day
        )
        .all()
    )

    # --------------------------------------------------------
    # CALCULATE SUMMARY
    # --------------------------------------------------------

    total_days = len(
        attendance_records
    )

    present_days = sum(
        1
        for record in attendance_records
        if record.check_in is not None
    )

    absent_days = (
        monthrange(year, month)[1]
        - present_days
    )

    total_working_hours = round(
        sum(
            record.working_hours
            for record in attendance_records
        ),
        2
    )

    return {
        "employee_id": employee_id,
        "month": month,
        "year": year,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "total_working_hours": total_working_hours
    }