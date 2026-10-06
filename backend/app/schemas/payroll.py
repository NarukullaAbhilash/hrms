from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PayrollResponse(BaseModel):
    id: int
    employee_id: int
    month: int
    year: int
    basic_salary: float
    working_days: int
    present_days: int
    approved_leave_days: float
    lop_days: float
    lop_deduction: float
    gross_salary: float
    net_salary: float
    status: str
    generated_at: datetime
    locked_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )