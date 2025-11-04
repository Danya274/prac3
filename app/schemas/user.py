from pydantic import BaseModel



class UserRegSchema(BaseModel):
    login: str
    password: str
    employee_id: int


class UserAuthSchema(BaseModel):
    login: str
    password: str


class UserResponseSchema(BaseModel):
    id: int
    login: str
    employee_id: int
    is_admin: bool


class UserCreateSchema(BaseModel):
    login: str
    password: str
    employee_id: int
    is_admin: bool