from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_salary_slip_pdf(employee, payroll):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SalarySlipTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=10,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=10,
    )

    story = []

    # ============================================================
    # TITLE
    # ============================================================

    story.append(
        Paragraph(
            "SALARY SLIP",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Salary Period: {payroll.month:02d}/{payroll.year}",
            normal_style
        )
    )

    story.append(Spacer(1, 15))

    # ============================================================
    # EMPLOYEE DETAILS
    # ============================================================

    story.append(
        Paragraph(
            "Employee Details",
            heading_style
        )
    )

    employee_data = [
        ["Employee ID", str(employee.id)],
        ["Employee Code", employee.employee_code],
        ["Employee Name", employee.full_name],
        ["Email", employee.email],
        ["Department", employee.department],
        ["Designation", employee.designation],
        ["Joining Date", str(employee.joining_date)],
    ]

    employee_table = Table(
        employee_data,
        colWidths=[140, 350]
    )

    employee_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(employee_table)

    story.append(Spacer(1, 20))

    # ============================================================
    # ATTENDANCE DETAILS
    # ============================================================

    story.append(
        Paragraph(
            "Attendance Details",
            heading_style
        )
    )

    attendance_data = [
        ["Working Days", str(payroll.working_days)],
        ["Present Days", str(payroll.present_days)],
        ["Approved Leave Days", str(payroll.approved_leave_days)],
        ["LOP Days", str(payroll.lop_days)],
    ]

    attendance_table = Table(
        attendance_data,
        colWidths=[250, 240]
    )

    attendance_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story.append(attendance_table)

    story.append(Spacer(1, 20))

    # ============================================================
    # SALARY DETAILS
    # ============================================================

    story.append(
        Paragraph(
            "Salary Details",
            heading_style
        )
    )

    salary_data = [
        ["Description", "Amount"],
        ["Basic Salary", f"₹{payroll.basic_salary:,.2f}"],
        ["Gross Salary", f"₹{payroll.gross_salary:,.2f}"],
        ["LOP Deduction", f"₹{payroll.lop_deduction:,.2f}"],
        ["Net Salary", f"₹{payroll.net_salary:,.2f}"],
    ]

    salary_table = Table(
        salary_data,
        colWidths=[250, 240]
    )

    salary_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(salary_table)

    story.append(Spacer(1, 20))

    # ============================================================
    # PAYROLL STATUS
    # ============================================================

    story.append(
        Paragraph(
            f"Payroll Status: <b>{payroll.status.upper()}</b>",
            normal_style
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "This is a system-generated salary slip.",
            normal_style
        )
    )

    # ============================================================
    # BUILD PDF
    # ============================================================

    document.build(story)

    buffer.seek(0)

    return buffer