from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# ============================================================
# ATTENDANCE RESPONSE
# ============================================================

class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    working_hours: float
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# MONTHLY ATTENDANCE SUMMARY
# ============================================================

class AttendanceSummaryResponse(BaseModel):
    employee_id: int
    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    total_working_hours: float