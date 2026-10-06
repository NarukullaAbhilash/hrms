from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LeaveCreate(BaseModel):
    leave_type: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    start_date: date

    end_date: date

    reason: str | None = Field(
        default=None,
        max_length=500
    )


class LeaveResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    reason: str | None
    status: str
    approved_by: int | None
    applied_at: datetime
    approved_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )


class LeaveBalanceResponse(BaseModel):
    employee_id: int
    casual_leave: float
    sick_leave: float
    earned_leave: float
    lop_days: float

    model_config = ConfigDict(
        from_attributes=True
    )