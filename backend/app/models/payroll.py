
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from app.database import Base


class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True
    )

    month = Column(
        Integer,
        nullable=False
    )

    year = Column(
        Integer,
        nullable=False
    )

    basic_salary = Column(
        Float,
        nullable=False
    )

    working_days = Column(
        Integer,
        nullable=False,
        default=0
    )

    present_days = Column(
        Integer,
        nullable=False,
        default=0
    )

    approved_leave_days = Column(
        Float,
        nullable=False,
        default=0
    )

    lop_days = Column(
        Float,
        nullable=False,
        default=0
    )

    lop_deduction = Column(
        Float,
        nullable=False,
        default=0
    )

    gross_salary = Column(
        Float,
        nullable=False,
        default=0
    )

    net_salary = Column(
        Float,
        nullable=False,
        default=0
    )

    status = Column(
        String(20),
        nullable=False,
        default="generated"
    )

    generated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    locked_at = Column(
        DateTime,
        nullable=True
    )
