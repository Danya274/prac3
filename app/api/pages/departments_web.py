from typing import Annotated

from fastapi import Depends, APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse

from app.api.routers.dependencies import UserOrNoneDep
from app.database.db import get_session
from app.database.db_utils import get_items_with_relationship, get_item_from_db
from app.database.models import DepartmentModel
from app.logger.logger import set_logger


logger = set_logger('DEPARTMENTS_WEB')
SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix='/pages', tags=['Frontend_departments'])
templates = Jinja2Templates(directory='app/templates')


@router.get('/departments')
async def get_departments_list(request: Request, session: SessionDep, current_user: UserOrNoneDep):
    departments = await get_items_with_relationship(DepartmentModel, session, relations=['employees'])
    return templates.TemplateResponse(name='departments.html', context={
        'request': request,
        'departments': departments,
        'is_admin': current_user.is_admin if current_user else False
    })

@router.get('/departments/create')
async def create_department_form(request: Request, current_user: UserOrNoneDep):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/departments', status_code=303)

    return templates.TemplateResponse(
        name='departments/create.html',
        context={'request': request}
    )


@router.post('/departments/create')
async def create_department(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        name: str = Form(...)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/departments', status_code=303)

    try:
        new_department = DepartmentModel(name=name)
        session.add(new_department)
        await session.commit()

        logger.info(f'Admin {current_user.login} created department {name}')
        return RedirectResponse(url='/pages/departments', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error creating department: {str(e)}')

        return templates.TemplateResponse(
            name='departments/create.html',
            context={
                'request': request,
                'error': f'Error creating department: {str(e)}'
            }
        )


@router.get('/departments/update/{department_id}')
async def edit_department_form(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        department_id: int
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/departments', status_code=303)

    try:
        department = await get_item_from_db(department_id, DepartmentModel, session)

        return templates.TemplateResponse(
            name='departments/edit.html',
            context={
                'request': request,
                'department': department
            }
        )

    except Exception as e:
        logger.error(f'Error loading department for edit: {str(e)}')
        return RedirectResponse(url='/pages/departments', status_code=303)


@router.post('/departments/update/{department_id}')
async def update_department(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        department_id: int,
        name: str = Form(...)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/departments', status_code=303)

    try:
        department = await get_item_from_db(department_id, DepartmentModel, session)
        if not department:
            return RedirectResponse(url='/pages/departments', status_code=303)

        department.name = name
        await session.commit()

        logger.info(f'Admin {current_user.login} updated department {name}')
        return RedirectResponse(url='/pages/departments', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error updating department: {str(e)}')

        department = await get_item_from_db(department_id, DepartmentModel, session)

        return templates.TemplateResponse(
            name='departments/edit.html',
            context={
                'request': request,
                'department': department,
                'error': f'Error updating department: {str(e)}'
            }
        )