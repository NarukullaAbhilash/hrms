
import os
from email.message import EmailMessage

import aiosmtplib
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587"
    )
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME"
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)

SMTP_FROM = os.getenv(
    "SMTP_FROM",
    SMTP_USERNAME
)


# ============================================================
# SEND EMAIL
# ============================================================

async def send_email(
    to_email: str,
    subject: str,
    body: str
):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP credentials are not configured"
        )

    message = EmailMessage()

    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        start_tls=True,
    )


# ============================================================
# EMPLOYEE ONBOARDING EMAIL
# ============================================================

async def send_onboarding_email(
    employee_name: str,
    employee_email: str
):
    subject = "Welcome to the Organization"

    body = f"""
Hello {employee_name},

Welcome to the organization!

Your employee profile has been successfully created
in the Human Resource Management System.

Employee Name: {employee_name}
Employee Email: {employee_email}

You can contact the HR department if you need
any additional information.

Regards,
HR Department
"""

    await send_email(
        employee_email,
        subject,
        body
    )


# ============================================================
# LEAVE APPLICATION EMAIL
# ============================================================

async def send_leave_application_email(
    employee_name: str,
    employee_email: str,
    leave_type: str,
    start_date: str,
    end_date: str
):
    subject = "Leave Application Submitted"

    body = f"""
Hello {employee_name},

Your leave application has been submitted successfully.

Leave Type: {leave_type}
Start Date: {start_date}
End Date: {end_date}

Your application is currently pending approval.

Regards,
HR Department
"""

    await send_email(
        employee_email,
        subject,
        body
    )


# ============================================================
# LEAVE DECISION EMAIL
# ============================================================

async def send_leave_decision_email(
    employee_name: str,
    employee_email: str,
    leave_type: str,
    status: str
):
    subject = f"Leave Application {status.capitalize()}"

    body = f"""
Hello {employee_name},

Your leave application has been {status}.

Leave Type: {leave_type}
Status: {status.capitalize()}

Please contact HR if you have any questions.

Regards,
HR Department
"""

    await send_email(
        employee_email,
        subject,
        body
    )


# ============================================================
# PAYROLL EMAIL
# ============================================================

async def send_payroll_email(
    employee_name: str,
    employee_email: str,
    month: int,
    year: int,
    net_salary: float
):
    subject = "Salary Payroll Generated"

    body = f"""
Hello {employee_name},

Your payroll has been generated successfully.

Salary Month: {month:02d}/{year}
Net Salary: ₹{net_salary:,.2f}

Your salary slip is available in the HRMS.

Regards,
HR Department
"""

    await send_email(
        employee_email,
        subject,
        body
    )

