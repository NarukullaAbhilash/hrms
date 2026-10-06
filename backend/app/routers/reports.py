import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from app.auth.dependencies import require_admin_or_hr
from app.database import get_db

from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.payroll import Payroll


router = APIRouter(
    prefix="/reports",
    tags=["Reports Management"]
)


# ============================================================
# HELPER: CREATE CSV RESPONSE
# ============================================================

def create_csv_response(filename, headers, rows):

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(headers)

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ============================================================
# HELPER: CREATE PDF RESPONSE
# ============================================================

def create_pdf_response(title, headers, rows, filename):

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    elements = []

    elements.append(
        Paragraph(title, title_style)
    )

    table_data = [
        headers
    ]

    table_data.extend(rows)

    table = Table(
        table_data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.lightgrey]
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            )
        ])
    )

    elements.append(table)

    document.build(elements)

    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# ============================================================
# EMPLOYEE CSV REPORT
# ============================================================

@router.get("/employees/csv")
def employee_csv_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employees = (
        db.query(Employee)
        .order_by(Employee.id)
        .all()
    )

    headers = [
        "ID",
        "Employee Code",
        "Full Name",
        "Email",
        "Phone",
        "Department",
        "Designation",
        "Joining Date",
        "Salary",
        "Active"
    ]

    rows = []

    for employee in employees:

        rows.append([
            employee.id,
            employee.employee_code,
            employee.full_name,
            employee.email,
            employee.phone,
            employee.department,
            employee.designation,
            employee.joining_date,
            employee.salary,
            employee.is_active
        ])

    return create_csv_response(
        "employee_report.csv",
        headers,
        rows
    )


# ============================================================
# EMPLOYEE PDF REPORT
# ============================================================

@router.get("/employees/pdf")
def employee_pdf_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employees = (
        db.query(Employee)
        .order_by(Employee.id)
        .all()
    )

    headers = [
        "ID",
        "Code",
        "Name",
        "Email",
        "Department",
        "Designation",
        "Joining Date",
        "Salary",
        "Active"
    ]

    rows = []

    for employee in employees:

        rows.append([
            str(employee.id),
            employee.employee_code,
            employee.full_name,
            employee.email,
            employee.department,
            employee.designation,
            str(employee.joining_date),
            str(employee.salary),
            str(employee.is_active)
        ])

    return create_pdf_response(
        "Employee Report",
        headers,
        rows,
        "employee_report.pdf"
    )


# ============================================================
# ATTENDANCE CSV REPORT
# ============================================================

@router.get("/attendance/csv")
def attendance_csv_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    records = (
        db.query(Attendance)
        .order_by(
            Attendance.attendance_date.desc()
        )
        .all()
    )

    headers = [
        "ID",
        "Employee ID",
        "Attendance Date",
        "Check In",
        "Check Out",
        "Working Hours"
    ]

    rows = []

    for record in records:

        rows.append([
            record.id,
            record.employee_id,
            record.attendance_date,
            record.check_in,
            record.check_out,
            record.working_hours
        ])

    return create_csv_response(
        "attendance_report.csv",
        headers,
        rows
    )


# ============================================================
# ATTENDANCE PDF REPORT
# ============================================================

@router.get("/attendance/pdf")
def attendance_pdf_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    records = (
        db.query(Attendance)
        .order_by(
            Attendance.attendance_date.desc()
        )
        .all()
    )

    headers = [
        "ID",
        "Employee",
        "Date",
        "Check In",
        "Check Out",
        "Hours"
    ]

    rows = []

    for record in records:

        rows.append([
            str(record.id),
            str(record.employee_id),
            str(record.attendance_date),
            str(record.check_in),
            str(record.check_out),
            str(record.working_hours)
        ])

    return create_pdf_response(
        "Attendance Report",
        headers,
        rows,
        "attendance_report.pdf"
    )


# ============================================================
# LEAVE CSV REPORT
# ============================================================

@router.get("/leaves/csv")
def leave_csv_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    leaves = (
        db.query(Leave)
        .order_by(Leave.id)
        .all()
    )

    headers = [
        "ID",
        "Employee ID",
        "Leave Type",
        "Start Date",
        "End Date",
        "Status"
    ]

    rows = []

    for leave in leaves:

        rows.append([
            leave.id,
            leave.employee_id,
            leave.leave_type,
            leave.start_date,
            leave.end_date,
            leave.status
        ])

    return create_csv_response(
        "leave_report.csv",
        headers,
        rows
    )


# ============================================================
# LEAVE PDF REPORT
# ============================================================

@router.get("/leaves/pdf")
def leave_pdf_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    leaves = (
        db.query(Leave)
        .order_by(Leave.id)
        .all()
    )

    headers = [
        "ID",
        "Employee",
        "Leave Type",
        "Start Date",
        "End Date",
        "Status"
    ]

    rows = []

    for leave in leaves:

        rows.append([
            str(leave.id),
            str(leave.employee_id),
            str(leave.leave_type),
            str(leave.start_date),
            str(leave.end_date),
            str(leave.status)
        ])

    return create_pdf_response(
        "Leave Report",
        headers,
        rows,
        "leave_report.pdf"
    )


# ============================================================
# PAYROLL CSV REPORT
# ============================================================

@router.get("/payroll/csv")
def payroll_csv_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    payroll_records = (
        db.query(Payroll)
        .order_by(
            Payroll.year.desc(),
            Payroll.month.desc()
        )
        .all()
    )

    headers = [
        "ID",
        "Employee ID",
        "Month",
        "Year",
        "Basic Salary",
        "Working Days",
        "Present Days",
        "Approved Leave Days",
        "LOP Days",
        "LOP Deduction",
        "Gross Salary",
        "Net Salary",
        "Status"
    ]

    rows = []

    for payroll in payroll_records:

        rows.append([
            payroll.id,
            payroll.employee_id,
            payroll.month,
            payroll.year,
            payroll.basic_salary,
            payroll.working_days,
            payroll.present_days,
            payroll.approved_leave_days,
            payroll.lop_days,
            payroll.lop_deduction,
            payroll.gross_salary,
            payroll.net_salary,
            payroll.status
        ])

    return create_csv_response(
        "payroll_report.csv",
        headers,
        rows
    )


# ============================================================
# PAYROLL PDF REPORT
# ============================================================

@router.get("/payroll/pdf")
def payroll_pdf_report(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    payroll_records = (
        db.query(Payroll)
        .order_by(
            Payroll.year.desc(),
            Payroll.month.desc()
        )
        .all()
    )

    headers = [
        "ID",
        "Employee",
        "Month",
        "Year",
        "Basic",
        "Present",
        "Leave",
        "LOP",
        "Deduction",
        "Gross",
        "Net",
        "Status"
    ]

    rows = []

    for payroll in payroll_records:

        rows.append([
            str(payroll.id),
            str(payroll.employee_id),
            str(payroll.month),
            str(payroll.year),
            str(payroll.basic_salary),
            str(payroll.present_days),
            str(payroll.approved_leave_days),
            str(payroll.lop_days),
            str(payroll.lop_deduction),
            str(payroll.gross_salary),
            str(payroll.net_salary),
            str(payroll.status)
        ])

    return create_pdf_response(
        "Payroll Report",
        headers,
        rows,
        "payroll_report.pdf"
    )