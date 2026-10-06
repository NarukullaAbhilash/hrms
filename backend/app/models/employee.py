from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    employee_code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    full_name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    phone = Column(
        String(20),
        nullable=True
    )

    department = Column(
        String(100),
        nullable=False
    )

    designation = Column(
        String(100),
        nullable=False
    )

    joining_date = Column(
        Date,
        nullable=False
    )

    salary = Column(
        Float,
        nullable=False,
        default=0
    )

    document = Column(
        String(255),
        nullable=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )