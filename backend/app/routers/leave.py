from datetime import date, datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_hr,
)
from app.database import get_db

from app.models.employee import Employee
from app.models.leave import Leave
from app.models.leave_balance import LeaveBalance
from app.models.user import User
from app.models.audit_log import AuditLog

from app.schemas.leave import (
    LeaveCreate,
    LeaveResponse,
    LeaveBalanceResponse,
)

from app.services.email_service import (
    send_leave_application_email,
    send_leave_decision_email,
)


router = APIRouter(
    prefix="/leaves",
    tags=["Leave Management"]
)


# ============================================================
# HELPER - GET OR CREATE LEAVE BALANCE
# ============================================================

def get_or_create_balance(
    employee_id: int,
    db: Session
):
    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id
        )
        .first()
    )

    if not balance:
        balance = LeaveBalance(
            employee_id=employee_id,
            casual_leave=10,
            sick_leave=10,
            earned_leave=15,
            lop_days=0,
        )

        db.add(balance)
        db.commit()
        db.refresh(balance)

    return balance


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
# EMPLOYEE - APPLY FOR LEAVE
# ============================================================

@router.post(
    "",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED
)
async def apply_leave(
    data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
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

    # --------------------------------------------------------
    # DATE VALIDATION
    # --------------------------------------------------------

    if data.end_date < data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date"
        )

    if data.start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave cannot be applied for a past date"
        )

    # --------------------------------------------------------
    # LEAVE TYPE VALIDATION
    # --------------------------------------------------------

    leave_type = data.leave_type.lower().strip()

    allowed_leave_types = [
        "casual",
        "sick",
        "earned",
    ]

    if leave_type not in allowed_leave_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave type must be casual, sick, or earned"
        )

    # --------------------------------------------------------
    # CALCULATE TOTAL DAYS
    # --------------------------------------------------------

    total_days = (
        data.end_date - data.start_date
    ).days + 1

    # --------------------------------------------------------
    # CHECK OVERLAPPING LEAVE
    # --------------------------------------------------------

    overlapping_leave = (
        db.query(Leave)
        .filter(
            Leave.employee_id == employee.id,
            Leave.status.in_(
                ["pending", "approved"]
            ),
            Leave.start_date <= data.end_date,
            Leave.end_date >= data.start_date,
        )
        .first()
    )

    if overlapping_leave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Leave dates overlap with an existing "
                "leave request"
            )
        )

    # --------------------------------------------------------
    # CREATE LEAVE BALANCE IF REQUIRED
    # --------------------------------------------------------

    get_or_create_balance(
        employee.id,
        db
    )

    # --------------------------------------------------------
    # CREATE LEAVE REQUEST
    # --------------------------------------------------------

    leave = Leave(
        employee_id=employee.id,
        leave_type=leave_type,
        start_date=data.start_date,
        end_date=data.end_date,
        total_days=total_days,
        reason=data.reason,
        status="pending",
    )

    db.add(leave)

    # Flush so leave.id is available before commit
    db.flush()

    # --------------------------------------------------------
    # AUDIT LOG - LEAVE APPLIED
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="LEAVE_APPLIED",
        entity="Leave",
        entity_id=leave.id,
        description=(
            f"Employee {employee.full_name} applied for "
            f"{leave.leave_type} leave from "
            f"{leave.start_date} to {leave.end_date} "
            f"for {leave.total_days} day(s)"
        ),
    )

    db.commit()
    db.refresh(leave)

    # --------------------------------------------------------
    # SEND LEAVE APPLICATION EMAIL
    # --------------------------------------------------------

    try:
        await send_leave_application_email(
            employee_name=employee.full_name,
            employee_email=employee.email,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
        )

        print(
            f"Leave application email sent to "
            f"{employee.email}"
        )

    except Exception as e:
        print(
            f"Leave application email failed for "
            f"{employee.email}: {e}"
        )

    return leave


# ============================================================
# EMPLOYEE - VIEW MY LEAVES
# ============================================================

@router.get(
    "/my",
    response_model=list[LeaveResponse]
)
def get_my_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    leaves = (
        db.query(Leave)
        .filter(
            Leave.employee_id == employee.id
        )
        .order_by(
            Leave.applied_at.desc()
        )
        .all()
    )

    return leaves


# ============================================================
# EMPLOYEE - VIEW MY LEAVE BALANCE
# ============================================================

@router.get(
    "/balance",
    response_model=LeaveBalanceResponse
)
def get_my_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )

    balance = get_or_create_balance(
        employee.id,
        db
    )

    return balance


# ============================================================
# ADMIN / HR - VIEW ALL LEAVES
# ============================================================

@router.get(
    "",
    response_model=list[LeaveResponse]
)
def get_all_leaves(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    leaves = (
        db.query(Leave)
        .order_by(
            Leave.applied_at.desc()
        )
        .all()
    )

    return leaves


# ============================================================
# ADMIN / HR - APPROVE LEAVE
# ============================================================

@router.patch(
    "/{leave_id}/approve",
    response_model=LeaveResponse
)
async def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # FIND LEAVE
    # --------------------------------------------------------

    leave = (
        db.query(Leave)
        .filter(
            Leave.id == leave_id
        )
        .first()
    )

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # --------------------------------------------------------
    # PREVENT DUPLICATE APPROVAL
    # --------------------------------------------------------

    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave is already {leave.status}"
        )

    # --------------------------------------------------------
    # GET EMPLOYEE BALANCE
    # --------------------------------------------------------

    balance = get_or_create_balance(
        leave.employee_id,
        db
    )

    requested_days = leave.total_days

    # --------------------------------------------------------
    # SELECT CORRECT BALANCE
    # --------------------------------------------------------

    if leave.leave_type == "casual":
        available_days = balance.casual_leave

    elif leave.leave_type == "sick":
        available_days = balance.sick_leave

    elif leave.leave_type == "earned":
        available_days = balance.earned_leave

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid leave type"
        )

    # --------------------------------------------------------
    # CALCULATE REGULAR LEAVE AND LOP
    # --------------------------------------------------------

    regular_leave_days = min(
        requested_days,
        available_days
    )

    lop_days = max(
        requested_days - available_days,
        0
    )

    # --------------------------------------------------------
    # DEDUCT LEAVE BALANCE
    # --------------------------------------------------------

    if leave.leave_type == "casual":

        balance.casual_leave = max(
            balance.casual_leave - regular_leave_days,
            0
        )

    elif leave.leave_type == "sick":

        balance.sick_leave = max(
            balance.sick_leave - regular_leave_days,
            0
        )

    elif leave.leave_type == "earned":

        balance.earned_leave = max(
            balance.earned_leave - regular_leave_days,
            0
        )

    # --------------------------------------------------------
    # ADD LOP DAYS
    # --------------------------------------------------------

    balance.lop_days += lop_days

    # --------------------------------------------------------
    # APPROVE LEAVE
    # --------------------------------------------------------

    leave.status = "approved"

    leave.approved_by = current_user.id

    leave.approved_at = datetime.utcnow()

    # --------------------------------------------------------
    # AUDIT LOG - LEAVE APPROVED
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="LEAVE_APPROVED",
        entity="Leave",
        entity_id=leave.id,
        description=(
            f"Leave request {leave.id} approved by "
            f"{current_user.email}. "
            f"Leave type: {leave.leave_type}, "
            f"requested days: {requested_days}, "
            f"regular leave days: {regular_leave_days}, "
            f"LOP days: {lop_days}"
        ),
    )

    db.commit()
    db.refresh(leave)

    # --------------------------------------------------------
    # SEND APPROVAL EMAIL
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == leave.employee_id
        )
        .first()
    )

    if employee:
        try:
            await send_leave_decision_email(
                employee_name=employee.full_name,
                employee_email=employee.email,
                leave_type=leave.leave_type,
                status="approved"
            )

            print(
                f"Leave approval email sent to "
                f"{employee.email}"
            )

        except Exception as e:
            print(
                f"Leave approval email failed for "
                f"{employee.email}: {e}"
            )

    return leave


# ============================================================
# ADMIN / HR - REJECT LEAVE
# ============================================================

@router.patch(
    "/{leave_id}/reject",
    response_model=LeaveResponse
)
async def reject_leave(
    leave_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # FIND LEAVE
    # --------------------------------------------------------

    leave = (
        db.query(Leave)
        .filter(
            Leave.id == leave_id
        )
        .first()
    )

    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )

    # --------------------------------------------------------
    # ONLY PENDING LEAVE CAN BE REJECTED
    # --------------------------------------------------------

    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave is already {leave.status}"
        )

    # --------------------------------------------------------
    # REJECT LEAVE
    # --------------------------------------------------------

    leave.status = "rejected"

    leave.approved_by = current_user.id

    leave.approved_at = datetime.utcnow()

    # --------------------------------------------------------
    # AUDIT LOG - LEAVE REJECTED
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="LEAVE_REJECTED",
        entity="Leave",
        entity_id=leave.id,
        description=(
            f"Leave request {leave.id} rejected by "
            f"{current_user.email}. "
            f"Leave type: {leave.leave_type}, "
            f"requested days: {leave.total_days}"
        ),
    )

    db.commit()
    db.refresh(leave)

    # --------------------------------------------------------
    # SEND REJECTION EMAIL
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == leave.employee_id
        )
        .first()
    )

    if employee:
        try:
            await send_leave_decision_email(
                employee_name=employee.full_name,
                employee_email=employee.email,
                leave_type=leave.leave_type,
                status="rejected"
            )

            print(
                f"Leave rejection email sent to "
                f"{employee.email}"
            )

        except Exception as e:
            print(
                f"Leave rejection email failed for "
                f"{employee.email}: {e}"
            )

    return leave