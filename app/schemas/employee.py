from pydantic import BaseModel
from datetime import date


class EmployeeSchema(BaseModel):
    name: str
    date_of_birth: date
    status: str
    department_id: int
    position_id: int
    rate: float
    salary: float
    date_of_employment: date

class EmployeeUpdateSchema(BaseModel):
    name: str | None = None
    date_of_birth: date | None = None
    status: str | None = None
    department_id: int | None = None
    position_id: int | None = None
    rate: float | None = None
    salary: float | None = None
    date_of_employment: date | None = None
