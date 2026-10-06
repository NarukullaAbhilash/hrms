from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class Leave(Base):
    __tablename__ = "leaves"

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

    leave_type = Column(
        String(50),
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    total_days = Column(
        Float,
        nullable=False
    )

    reason = Column(
        String(500),
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )

    approved_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    applied_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    approved_at = Column(
        DateTime,
        nullable=True
    )