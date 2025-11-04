from fastapi import APIRouter, Depends

from typing import Annotated

from app.database.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.default import DefaultResponse
from app.schemas.department import DepartmentSchema
from app.database.db_utils import get_item_from_db, update_item_in_db, delete_item_from_db, write_to_db, get_all_items
from app.database.models import DepartmentModel


from app.logger.logger import set_logger

SessionDep = Annotated[AsyncSession, Depends(get_session)]

department_router = APIRouter(tags=['Departments'])
logger = set_logger('DEPARTMENTS')


@department_router.get("/departments")
async def get_departments(session: SessionDep):
    items = await get_all_items(DepartmentModel, session)
    if items:
        all_departments = []
        for item in items:
            department = DepartmentSchema(
                    name=item.name,
                )
            all_departments.append(department)
        logger.info(f'Departments found: {len(all_departments)}')
        return DefaultResponse(
            error=False,
            message='All departments',
            payload=all_departments
        )
    else:
        logger.info('No departments found')
        return DefaultResponse(
            error=True,
            message='No departments found',
        )


@department_router.delete("/departments")
async def delete_department(id: int, session: SessionDep):
    try:
        deleted = await delete_item_from_db(id, DepartmentModel, session)
        if deleted:
            logger.info(f'Department with id: {id} deleted from db')
            return DefaultResponse(
                error=False,
                message='Department deleted successfuly'
            )
        else:
            logger.info(f'Department with id: {id} not deleted')
            return DefaultResponse(
                error=True,
                message='Department not deleted'
            )
    except Exception as e:
        logger.error(f'Error delete department with id: {id}  ===> {e}')


@department_router.get("/departments/{department_id}")
async def get_position(department_id: int, session: SessionDep):
    try:
        item = await get_item_from_db(department_id, DepartmentModel, session)
        if item:
            logger.info(f'Department with id: {department_id} found')
            return DefaultResponse(
                error=False,
                message='Department found',
                payload=DepartmentSchema(
                    name=item.name,
                )
            )
    except Exception as e:
        logger.error(f'Error get department with id: {department_id}  ===> {e}')
    logger.info(f'Department with id: {department_id} not found')
    return DefaultResponse(
            error=True,
            message='Department not found',
        )


@department_router.post("/departments")
async def post_department(department: DepartmentSchema, session: SessionDep):
    logger.info(f'Department added to db')
    result = await write_to_db(department, session)
    if result:
        logger.info('Department added successfuly')
        return DefaultResponse(
            error=False,
            message='Department added successfuly'
        )
    else:
        logger.info('Department not added')
        return DefaultResponse(
            error=True,
            message='Department not added'
        )


@department_router.put("/departments/{department_id}")
async def update_department(department_id: int, department: DepartmentSchema, session: SessionDep):
    try:
        logger.info(f'Update request for department with id: {department_id}: {department}')
        update_data = department.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            return DefaultResponse(
                error=True,
                message='No fields to update'
            )

        logger.info(f'Fields to update: {update_data}')

        success = await update_item_in_db(department_id, DepartmentModel, department, session)

        if success:
            logger.info(f'Department with id: {department_id} updated successfuly')
            return DefaultResponse(
                error=False,
                message='Department updated successfully'
            )
        else:
            logger.info('Department not found or update failed')
            return DefaultResponse(
                error=True,
                message='Department not found or update failed'
            )

    except Exception as e:
        await session.rollback()
        logger.error(f'Error update department with id: {department_id}: {e}')
        return DefaultResponse(
            error=True,
            message=f'Error update failed: {e}'
        )