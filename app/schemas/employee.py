from pydantic import BaseModel
from datetime import date

from app.schemas.department import DepartmentSchema
from app.schemas.position import PositionSchema


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


class EmployeeResponseSchema(BaseModel):
    name: str
    date_of_birth: date
    status: str
    department_name: DepartmentSchema
    position_name: PositionSchema
    rate: float
    salary: float
    date_of_employment: date
    has_user_acc: bool