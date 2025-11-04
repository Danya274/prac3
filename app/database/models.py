from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from datetime import date, datetime
from sqlalchemy import ForeignKey, text
from typing import List, Annotated

int_pk = Annotated[int, mapped_column(primary_key=True)]
str_unique = Annotated[str, mapped_column(unique=True)]
create_at = Annotated[datetime, mapped_column(default=datetime.now())]

class Base(DeclarativeBase):
    pass


class EmployeeModel(Base):
    __tablename__ = "employees"

    id: Mapped[int_pk]
    name: Mapped[str]
    date_of_birth: Mapped[date]
    status: Mapped[str]

    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    department: Mapped["DepartmentModel"] = relationship("DepartmentModel", back_populates="employees")

    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    position: Mapped["PositionModel"] = relationship("PositionModel", back_populates="employees")

    rate: Mapped[float]
    salary: Mapped[float]
    date_of_employment: Mapped[date]

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="employee")




class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int_pk]
    login: Mapped[str_unique]
    password: Mapped[str]

    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", back_populates="user")

    is_user: Mapped[bool] = mapped_column(default=True, server_default=text('true'), nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, server_default=text('false'), nullable=False)

    # created_at: Mapped[create_at]



class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[int_pk]
    name: Mapped[str_unique]

    employees: Mapped[List["EmployeeModel"]] = relationship("EmployeeModel", back_populates="position")


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[int_pk]
    name: Mapped[str_unique]

    employees: Mapped[List["EmployeeModel"]] = relationship("EmployeeModel", back_populates="department")