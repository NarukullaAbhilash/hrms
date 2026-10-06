import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
    require_admin_or_hr,
)
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.email_service import send_onboarding_email


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/employees",
    tags=["Employee Management"]
)


# ============================================================
# UPLOAD CONFIGURATION
# ============================================================

UPLOAD_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".doc",
    ".docx",
}

MAX_FILE_SIZE = 5 * 1024 * 1024


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
# CREATE EMPLOYEE
# ============================================================

@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_employee(
    data: EmployeeCreate,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    existing_code = (
        db.query(Employee)
        .filter(
            Employee.employee_code == data.employee_code
        )
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee code is already registered"
        )

    existing_email = (
        db.query(Employee)
        .filter(
            Employee.email == data.email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee email is already registered"
        )

    employee = Employee(
        employee_code=data.employee_code,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        department=data.department,
        designation=data.designation,
        joining_date=data.joining_date,
        salary=data.salary,
        is_active=True,
    )

    db.add(employee)
    db.flush()

    # Create audit record
    create_audit_log(
        db=db,
        current_user=current_user,
        action="EMPLOYEE_CREATED",
        entity="Employee",
        entity_id=employee.id,
        description=(
            f"Employee {employee.employee_code} "
            f"({employee.full_name}) was created"
        ),
    )

    db.commit()
    db.refresh(employee)

    try:
        await send_onboarding_email(
            employee_name=employee.full_name,
            employee_email=employee.email
        )

        print(
            f"Onboarding email sent to {employee.email}"
        )

    except Exception as e:
        print(
            f"Onboarding email failed for "
            f"{employee.email}: {e}"
        )

    return employee


# ============================================================
# GET ALL EMPLOYEES
# ============================================================

@router.get(
    "",
    response_model=list[EmployeeResponse]
)
def get_employees(
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employees = (
        db.query(Employee)
        .order_by(Employee.id.asc())
        .all()
    )

    return employees


# ============================================================
# GET CURRENT LOGGED-IN EMPLOYEE PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=EmployeeResponse
)
def get_my_employee_profile(
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

    return employee


# ============================================================
# GET SINGLE EMPLOYEE
# ============================================================

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee(
    employee_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


# ============================================================
# UPDATE EMPLOYEE
# ============================================================

@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if data.email is not None:

        existing_email = (
            db.query(Employee)
            .filter(
                Employee.email == data.email,
                Employee.id != employee_id
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already used by another employee"
            )

        employee.email = data.email

    if data.full_name is not None:
        employee.full_name = data.full_name

    if data.phone is not None:
        employee.phone = data.phone

    if data.department is not None:
        employee.department = data.department

    if data.designation is not None:
        employee.designation = data.designation

    if data.joining_date is not None:
        employee.joining_date = data.joining_date

    if data.salary is not None:
        employee.salary = data.salary

    create_audit_log(
        db=db,
        current_user=current_user,
        action="EMPLOYEE_UPDATED",
        entity="Employee",
        entity_id=employee.id,
        description=(
            f"Employee {employee.employee_code} "
            f"({employee.full_name}) was updated"
        ),
    )

    db.commit()
    db.refresh(employee)

    return employee


# ============================================================
# DEACTIVATE EMPLOYEE
# ============================================================

@router.patch(
    "/{employee_id}/deactivate",
    response_model=EmployeeResponse
)
def deactivate_employee(
    employee_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    employee.is_active = False

    create_audit_log(
        db=db,
        current_user=current_user,
        action="EMPLOYEE_DEACTIVATED",
        entity="Employee",
        entity_id=employee.id,
        description=(
            f"Employee {employee.employee_code} "
            f"({employee.full_name}) was deactivated"
        ),
    )

    db.commit()
    db.refresh(employee)

    return employee


# ============================================================
# ACTIVATE EMPLOYEE
# ============================================================

@router.patch(
    "/{employee_id}/activate",
    response_model=EmployeeResponse
)
def activate_employee(
    employee_id: int,
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    employee.is_active = True

    create_audit_log(
        db=db,
        current_user=current_user,
        action="EMPLOYEE_ACTIVATED",
        entity="Employee",
        entity_id=employee.id,
        description=(
            f"Employee {employee.employee_code} "
            f"({employee.full_name}) was activated"
        ),
    )

    db.commit()
    db.refresh(employee)

    return employee


# ============================================================
# UPLOAD EMPLOYEE DOCUMENT
# ============================================================

@router.post(
    "/{employee_id}/document",
    response_model=EmployeeResponse
)
async def upload_employee_document(
    employee_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_hr),
    db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    original_filename = file.filename or ""

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid file type. "
                "Allowed: PDF, JPG, JPEG, PNG, DOC, DOCX"
            )
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 5 MB"
        )

    if employee.document:

        old_file_path = os.path.join(
            UPLOAD_DIR,
            employee.document
        )

        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    unique_filename = (
        f"employee_{employee_id}_"
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    employee.document = unique_filename

    create_audit_log(
        db=db,
        current_user=current_user,
        action="EMPLOYEE_DOCUMENT_UPLOADED",
        entity="Employee",
        entity_id=employee.id,
        description=(
            f"Document uploaded for employee "
            f"{employee.employee_code} ({employee.full_name})"
        ),
    )

    db.commit()
    db.refresh(employee)

    return employee