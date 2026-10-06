from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from app.database import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        unique=True,
        nullable=False,
        index=True
    )

    casual_leave = Column(
        Float,
        nullable=False,
        default=10
    )

    sick_leave = Column(
        Float,
        nullable=False,
        default=10
    )

    earned_leave = Column(
        Float,
        nullable=False,
        default=15
    )

    lop_days = Column(
        Float,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )