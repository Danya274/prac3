from pydantic import BaseModel


class DepartmentSchema(BaseModel):
    name: str