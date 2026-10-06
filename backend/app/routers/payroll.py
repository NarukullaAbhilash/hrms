from calendar import month_name, monthrange
from datetime import date, datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_hr,
)
from app.database import get_db

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.payroll import Payroll
from app.models.audit_log import AuditLog
from app.models.user import User

from app.schemas.payroll import PayrollResponse

from app.services.email_service import send_payroll_email


router = APIRouter(
    prefix="/payroll",
    tags=["Payroll Management"],
)


# ============================================================
# AUDIT LOG HELPER
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
# GENERATE MONTHLY PAYROLL
# ============================================================

@router.post(
    "/generate/{employee_id}",
    response_model=PayrollResponse,
)
def generate_payroll(
    employee_id: int,
    month: int,
    year: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Validate month
    # --------------------------------------------------------

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=400,
            detail="Month must be between 1 and 12",
        )

    # --------------------------------------------------------
    # Validate year
    # --------------------------------------------------------

    if year < 2000 or year > 2100:
        raise HTTPException(
            status_code=400,
            detail="Invalid year",
        )

    # --------------------------------------------------------
    # Find employee
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot generate payroll for inactive employee",
        )

    # --------------------------------------------------------
    # Prevent duplicate payroll
    # --------------------------------------------------------

    existing_payroll = (
        db.query(Payroll)
        .filter(
            Payroll.employee_id == employee_id,
            Payroll.month == month,
            Payroll.year == year,
        )
        .first()
    )

    if existing_payroll:
        raise HTTPException(
            status_code=400,
            detail="Payroll already generated for this month",
        )

    # --------------------------------------------------------
    # Month dates
    # --------------------------------------------------------

    first_day = date(year, month, 1)

    last_day = date(
        year,
        month,
        monthrange(year, month)[1],
    )

    # --------------------------------------------------------
    # Attendance records
    # --------------------------------------------------------

    attendance_records = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= first_day,
            Attendance.attendance_date <= last_day,
        )
        .all()
    )

    present_days = sum(
        1
        for record in attendance_records
        if record.check_in is not None
    )

    # --------------------------------------------------------
    # Working days
    # Monday = 0
    # Sunday = 6
    # --------------------------------------------------------

    working_days = sum(
        1
        for day in range(
            1,
            monthrange(year, month)[1] + 1,
        )
        if date(year, month, day).weekday() < 5
    )

    # --------------------------------------------------------
    # Approved leaves
    # --------------------------------------------------------

    approved_leaves = (
        db.query(Leave)
        .filter(
            Leave.employee_id == employee_id,
            Leave.status == "approved",
            Leave.start_date <= last_day,
            Leave.end_date >= first_day,
        )
        .all()
    )

    approved_leave_days = 0.0

    for leave in approved_leaves:

        leave_start = max(
            leave.start_date,
            first_day,
        )

        leave_end = min(
            leave.end_date,
            last_day,
        )

        approved_leave_days += (
            leave_end - leave_start
        ).days + 1

    # --------------------------------------------------------
    # Calculate LOP
    # --------------------------------------------------------

    lop_days = max(
        working_days
        - present_days
        - approved_leave_days,
        0,
    )

    # --------------------------------------------------------
    # Salary calculation
    # --------------------------------------------------------

    basic_salary = employee.salary

    gross_salary = basic_salary

    if working_days > 0:
        daily_salary = basic_salary / working_days
    else:
        daily_salary = 0

    lop_deduction = round(
        daily_salary * lop_days,
        2,
    )

    net_salary = round(
        gross_salary - lop_deduction,
        2,
    )

    # --------------------------------------------------------
    # Create payroll
    # --------------------------------------------------------

    payroll = Payroll(
        employee_id=employee_id,
        month=month,
        year=year,
        basic_salary=basic_salary,
        working_days=working_days,
        present_days=present_days,
        approved_leave_days=approved_leave_days,
        lop_days=lop_days,
        lop_deduction=lop_deduction,
        gross_salary=gross_salary,
        net_salary=net_salary,
        status="generated",
        generated_at=datetime.utcnow(),
        locked_at=None,
    )

    db.add(payroll)

    # Get payroll ID before commit
    db.flush()

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="PAYROLL_GENERATED",
        entity="Payroll",
        entity_id=payroll.id,
        description=(
            f"Payroll generated for employee "
            f"{employee.full_name} ({employee.employee_code}) "
            f"for {month_name[month]} {year}. "
            f"Net salary: Rs. {net_salary:.2f}"
        ),
    )

    db.commit()

    db.refresh(payroll)

    return payroll


# ============================================================
# PAYROLL HISTORY - ADMIN / HR
# ============================================================

@router.get(
    "",
    response_model=list[PayrollResponse],
)
def get_payroll_history(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db),
):

    payrolls = (
        db.query(Payroll)
        .order_by(
            Payroll.year.desc(),
            Payroll.month.desc(),
            Payroll.id.desc(),
        )
        .all()
    )

    return payrolls


# ============================================================
# EMPLOYEE PAYROLL HISTORY
# ============================================================

@router.get(
    "/my",
    response_model=list[PayrollResponse],
)
def get_my_payroll(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
            status_code=404,
            detail="Employee profile not found",
        )

    payrolls = (
        db.query(Payroll)
        .filter(
            Payroll.employee_id == employee.id
        )
        .order_by(
            Payroll.year.desc(),
            Payroll.month.desc(),
            Payroll.id.desc(),
        )
        .all()
    )

    return payrolls


# ============================================================
# DOWNLOAD SALARY SLIP PDF
# ============================================================

@router.get(
    "/{payroll_id}/salary-slip",
)
def download_salary_slip(
    payroll_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Find payroll
    # --------------------------------------------------------

    payroll = (
        db.query(Payroll)
        .filter(
            Payroll.id == payroll_id
        )
        .first()
    )

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    # --------------------------------------------------------
    # Find employee
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == payroll.employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    # --------------------------------------------------------
    # Authorization
    #
    # Employee:
    #     Can download only own salary slip.
    #
    # Admin / HR:
    #     Can download any salary slip.
    # --------------------------------------------------------

    if current_user.role == "employee":

        if employee.email != current_user.email:
            raise HTTPException(
                status_code=403,
                detail="You can only download your own salary slip",
            )

    elif current_user.role not in ["admin", "hr"]:

        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="SALARY_SLIP_DOWNLOADED",
        entity="Payroll",
        entity_id=payroll.id,
        description=(
            f"Salary slip downloaded for employee "
            f"{employee.full_name} ({employee.employee_code}) "
            f"for {month_name[payroll.month]} {payroll.year}"
        ),
    )

    db.commit()

    # --------------------------------------------------------
    # Create PDF in memory
    # --------------------------------------------------------

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="HRMS Salary Slip",
        author="HRMS",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SalaryTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=26,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "SalarySubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )

    right_style = ParagraphStyle(
        "RightText",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    # --------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------

    def money(value):
        try:
            return f"Rs. {float(value):,.2f}"
        except (TypeError, ValueError):
            return "Rs. 0.00"

    def days(value):
        try:
            number = float(value)

            if number.is_integer():
                return str(int(number))

            return f"{number:.2f}"

        except (TypeError, ValueError):
            return "0"

    # --------------------------------------------------------
    # Salary month
    # --------------------------------------------------------

    salary_month = month_name[payroll.month]

    month_year = (
        f"{salary_month} {payroll.year}"
    )

    # --------------------------------------------------------
    # PDF story
    # --------------------------------------------------------

    story = []

    story.append(
        Paragraph(
            "HRMS",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Human Resource Management System",
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            "Monthly Salary Slip",
            subtitle_style,
        )
    )

    story.append(Spacer(1, 8))

    # --------------------------------------------------------
    # Salary period
    # --------------------------------------------------------

    period_data = [
        [
            Paragraph(
                "<b>Salary Period</b>",
                normal_style,
            ),
            Paragraph(
                month_year,
                normal_style,
            ),
        ]
    ]

    period_table = Table(
        period_data,
        colWidths=[45 * mm, 125 * mm],
    )

    period_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(period_table)

    story.append(Spacer(1, 12))

    # --------------------------------------------------------
    # Employee information
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Employee Information",
            section_style,
        )
    )

    employee_data = [
        [
            Paragraph("<b>Employee Code</b>", normal_style),
            Paragraph(
                str(employee.employee_code or "-"),
                normal_style,
            ),
            Paragraph("<b>Employee Name</b>", normal_style),
            Paragraph(
                str(employee.full_name or "-"),
                normal_style,
            ),
        ],
        [
            Paragraph("<b>Email</b>", normal_style),
            Paragraph(
                str(employee.email or "-"),
                normal_style,
            ),
            Paragraph("<b>Phone</b>", normal_style),
            Paragraph(
                str(employee.phone or "-"),
                normal_style,
            ),
        ],
        [
            Paragraph("<b>Department</b>", normal_style),
            Paragraph(
                str(employee.department or "-"),
                normal_style,
            ),
            Paragraph("<b>Designation</b>", normal_style),
            Paragraph(
                str(employee.designation or "-"),
                normal_style,
            ),
        ],
        [
            Paragraph("<b>Joining Date</b>", normal_style),
            Paragraph(
                str(employee.joining_date or "-"),
                normal_style,
            ),
            Paragraph("<b>Status</b>", normal_style),
            Paragraph(
                "Active" if employee.is_active else "Inactive",
                normal_style,
            ),
        ],
    ]

    employee_table = Table(
        employee_data,
        colWidths=[
            32 * mm,
            53 * mm,
            32 * mm,
            53 * mm,
        ],
    )

    employee_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(employee_table)

    # --------------------------------------------------------
    # Salary details
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Salary Details",
            section_style,
        )
    )

    salary_data = [
        [
            Paragraph(
                "<b>Salary Component</b>",
                normal_style,
            ),
            Paragraph(
                "<b>Amount</b>",
                right_style,
            ),
        ],
        [
            Paragraph(
                "Basic Salary",
                normal_style,
            ),
            Paragraph(
                money(payroll.basic_salary),
                right_style,
            ),
        ],
        [
            Paragraph(
                "Gross Salary",
                normal_style,
            ),
            Paragraph(
                money(payroll.gross_salary),
                right_style,
            ),
        ],
        [
            Paragraph(
                "LOP Deduction",
                normal_style,
            ),
            Paragraph(
                money(payroll.lop_deduction),
                right_style,
            ),
        ],
        [
            Paragraph(
                "<b>Net Salary</b>",
                normal_style,
            ),
            Paragraph(
                f"<b>{money(payroll.net_salary)}</b>",
                right_style,
            ),
        ],
    ]

    salary_table = Table(
        salary_data,
        colWidths=[
            105 * mm,
            65 * mm,
        ],
    )

    salary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(salary_table)

    # --------------------------------------------------------
    # Attendance details
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Attendance & LOP Details",
            section_style,
        )
    )

    attendance_data = [
        [
            Paragraph(
                "<b>Attendance Component</b>",
                normal_style,
            ),
            Paragraph(
                "<b>Days</b>",
                right_style,
            ),
        ],
        [
            Paragraph("Working Days", normal_style),
            Paragraph(
                days(payroll.working_days),
                right_style,
            ),
        ],
        [
            Paragraph("Present Days", normal_style),
            Paragraph(
                days(payroll.present_days),
                right_style,
            ),
        ],
        [
            Paragraph("Approved Leave Days", normal_style),
            Paragraph(
                days(payroll.approved_leave_days),
                right_style,
            ),
        ],
        [
            Paragraph("Loss of Pay Days", normal_style),
            Paragraph(
                days(payroll.lop_days),
                right_style,
            ),
        ],
    ]

    attendance_table = Table(
        attendance_data,
        colWidths=[
            105 * mm,
            65 * mm,
        ],
    )

    attendance_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#cbd5e1"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f1f5f9"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(attendance_table)

    story.append(Spacer(1, 14))

    # --------------------------------------------------------
    # Final net salary
    # --------------------------------------------------------

    net_salary_data = [
        [
            Paragraph(
                "<b>NET SALARY</b>",
                normal_style,
            ),
            Paragraph(
                f"<b>{money(payroll.net_salary)}</b>",
                right_style,
            ),
        ]
    ]

    net_salary_table = Table(
        net_salary_data,
        colWidths=[
            105 * mm,
            65 * mm,
        ],
    )

    net_salary_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1.2,
                    colors.HexColor("#111827"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(net_salary_table)

    story.append(Spacer(1, 15))

    # --------------------------------------------------------
    # Payroll status
    # --------------------------------------------------------

    status_text = str(
        payroll.status or "generated"
    ).replace("_", " ").title()

    story.append(
        Paragraph(
            f"<b>Payroll Status:</b> {status_text}",
            normal_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "This is a computer-generated salary slip.",
            subtitle_style,
        )
    )

    # --------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------

    document.build(story)

    buffer.seek(0)

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    filename = (
        f"Salary_Slip_"
        f"{salary_month}_"
        f"{payroll.year}_"
        f"{employee.employee_code}.pdf"
    )

    # --------------------------------------------------------
    # Return PDF download
    # --------------------------------------------------------

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


# ============================================================
# GET SINGLE PAYROLL - ADMIN / HR
# ============================================================

@router.get(
    "/{payroll_id}",
    response_model=PayrollResponse,
)
def get_payroll(
    payroll_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db),
):

    payroll = (
        db.query(Payroll)
        .filter(
            Payroll.id == payroll_id
        )
        .first()
    )

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    return payroll


# ============================================================
# LOCK PAYROLL
# ============================================================

@router.patch(
    "/{payroll_id}/lock",
    response_model=PayrollResponse,
)
def lock_payroll(
    payroll_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db),
):

    payroll = (
        db.query(Payroll)
        .filter(
            Payroll.id == payroll_id
        )
        .first()
    )

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    if payroll.status == "locked":
        raise HTTPException(
            status_code=400,
            detail="Payroll is already locked",
        )

    if payroll.status == "credited":
        raise HTTPException(
            status_code=400,
            detail="Credited payroll cannot be locked again",
        )

    payroll.status = "locked"

    payroll.locked_at = datetime.utcnow()

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="PAYROLL_LOCKED",
        entity="Payroll",
        entity_id=payroll.id,
        description=(
            f"Payroll ID {payroll.id} locked "
            f"for {month_name[payroll.month]} {payroll.year}. "
            f"Employee ID: {payroll.employee_id}"
        ),
    )

    db.commit()

    db.refresh(payroll)

    return payroll


# ============================================================
# SALARY CREDIT + EMAIL NOTIFICATION
# ============================================================

@router.patch(
    "/{payroll_id}/credit",
    response_model=PayrollResponse,
)
async def credit_salary(
    payroll_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db),
):

    payroll = (
        db.query(Payroll)
        .filter(
            Payroll.id == payroll_id
        )
        .first()
    )

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    if payroll.status != "locked":
        raise HTTPException(
            status_code=400,
            detail="Payroll must be locked before salary credit",
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == payroll.employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    payroll.status = "credited"

    # --------------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------------

    create_audit_log(
        db=db,
        current_user=current_user,
        action="SALARY_CREDITED",
        entity="Payroll",
        entity_id=payroll.id,
        description=(
            f"Salary credited for employee "
            f"{employee.full_name} ({employee.employee_code}) "
            f"for {month_name[payroll.month]} {payroll.year}. "
            f"Net salary: Rs. {payroll.net_salary:.2f}"
        ),
    )

    db.commit()

    db.refresh(payroll)

    # --------------------------------------------------------
    # Send payroll email
    # --------------------------------------------------------

    try:

        await send_payroll_email(
            employee_name=employee.full_name,
            employee_email=employee.email,
            month=payroll.month,
            year=payroll.year,
            net_salary=payroll.net_salary,
        )

        print(
            f"Payroll email sent to "
            f"{employee.email}"
        )

    except Exception as e:

        print(
            f"Payroll email failed: {e}"
        )

    return payroll