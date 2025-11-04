from fastapi import APIRouter, Depends

from typing import Annotated

from app.database.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db_utils import get_item_from_db, update_item_in_db, delete_item_from_db, write_to_db, get_all_items
from app.database.models import EmployeeModel

from app.schemas.default import DefaultResponse
from app.schemas.employee import EmployeeSchema, EmployeeUpdateSchema

from app.logger.logger import set_logger

SessionDep = Annotated[AsyncSession, Depends(get_session)]

employee_router = APIRouter(tags=['Employees'])
logger = set_logger('EMPLOYEES')

@employee_router.get("/employees")
async def get_employees(session: SessionDep):
    items = await get_all_items(EmployeeModel, session)
    if items:
        all_employees = []
        for item in items:
            employee = EmployeeSchema(
                    name=item.name,
                    date_of_birth=item.date_of_birth,
                    status=item.status,
                    department_id=item.department_id,
                    position_id=item.position_id,
                    rate=item.rate,
                    salary=item.salary,
                    date_of_employment=item.date_of_employment
                )
            all_employees.append(employee)
        logger.info(f'Employees found: {len(all_employees)}')
        return DefaultResponse(
            error=False,
            message='All employees',
            payload=all_employees
        )
    else:
        logger.info('No employees found')
        return DefaultResponse(
            error=True,
            message='No employees found',
        )


@employee_router.get("/employees/{employee_id}")
async def get_employee(employee_id: int, session: SessionDep):
    try:
        item = await get_item_from_db(employee_id, EmployeeModel, session)
        if item:
            logger.info(f'Employee with id: {employee_id} found')
            return DefaultResponse(
                error=False,
                message='Employee found',
                payload=EmployeeSchema(
                    name=item.name,
                    date_of_birth=item.date_of_birth,
                    department_id=item.department_id,
                    position_id=item.position_id,
                    status=item.status,
                    rate=item.rate,
                    salary=item.salary,
                    date_of_employment=item.date_of_employment
                )
            )
    except Exception as e:
        logger.error(f'Error get employee with id: {employee_id }  ===> {e}')
    return DefaultResponse(
            error=True,
            message='Employee not found',
        )

@employee_router.delete("/employees")
async def delete_employee(id: int, session: SessionDep):
    try:
        deleted = await delete_item_from_db(id, EmployeeModel, session)
        if deleted:
            logger.info(f'Employee with id: {id} deleted from db')
            return DefaultResponse(
                error=False,
                message='Employee deleted successfuly'
            )
        else:
            logger.info(f'Employee with id: {id} not deleted')
            return DefaultResponse(
                error=True,
                message='Employee not deleted'
            )
    except Exception as e:
        logger.error(f'Error delete employee with {id}  ===> {e}')

@employee_router.post("/employees")
async def post_employee(employee: EmployeeSchema, session: SessionDep):
    result = await write_to_db(employee, session)
    logger.info(f'Employee added to db')
    if result:
        return DefaultResponse(
            error=False,
            message='Employee added successfuly'
        )
    else:
        return DefaultResponse(
            error=True,
            message='Employee not added'
        )


@employee_router.put("/employees/{employee_id}")
async def update_employee(employee_id: int, employee: EmployeeUpdateSchema, session: SessionDep):
    try:
        logger.info(f'Update request for employee with id: {employee_id}: {employee}')

        update_data = employee.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            return DefaultResponse(
                error=True,
                message='No fields to update'
            )

        logger.info(f'Fields to update: {update_data}')

        success = await update_item_in_db(employee_id, EmployeeModel, employee, session)

        if success:
            logger.info(f'Employee with id: {employee_id} updated successfuly')
            return DefaultResponse(
                error=False,
                message='Employee updated successfully'
            )
        else:
            logger.info(f'Employee with id: {employee_id} not found or update failed')
            return DefaultResponse(
                error=True,
                message='Employee not found or update failed'
            )

    except Exception as e:
        await session.rollback()
        logger.error(f'Error update employee with id: {employee_id} ===> {e}')
        return DefaultResponse(
            error=True,
            message=f'Error update failed: {e}'
        )
