from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

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

    attendance_date = Column(
        Date,
        nullable=False,
        default=date.today,
        index=True
    )

    check_in = Column(
        DateTime,
        nullable=True
    )

    check_out = Column(
        DateTime,
        nullable=True
    )

    working_hours = Column(
        Float,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )