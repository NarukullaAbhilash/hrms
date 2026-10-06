from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# CREATE EMPLOYEE
# ============================================================

class EmployeeCreate(BaseModel):
    employee_code: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    department: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    designation: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    joining_date: date

    salary: float = Field(
        ...,
        ge=0
    )


# ============================================================
# UPDATE EMPLOYEE
# ============================================================

class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    department: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    designation: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    joining_date: date | None = None

    salary: float | None = Field(
        default=None,
        ge=0
    )


# ============================================================
# EMPLOYEE RESPONSE
# ============================================================

class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    full_name: str
    email: EmailStr
    phone: str | None
    department: str
    designation: str
    joining_date: date
    salary: float
    document: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )