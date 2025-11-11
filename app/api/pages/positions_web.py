from typing import Annotated

from fastapi import Depends, APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse

from app.api.routers.dependencies import UserOrNoneDep
from app.database.db import get_session
from app.database.db_utils import get_items_with_relationship, get_item_from_db
from app.database.models import PositionModel
from app.logger.logger import set_logger


logger = set_logger('POSITIONS_WEB')
SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix='/pages', tags=['Frontend_positions'])
templates = Jinja2Templates(directory='app/templates')


@router.get('/positions')
async def get_positions_list(request: Request, session: SessionDep, current_user: UserOrNoneDep):
    positions = await get_items_with_relationship(PositionModel, session, relations=['employees'])
    return templates.TemplateResponse(name='positions.html', context={
        'request': request,
        'positions': positions,
        'is_admin': current_user.is_admin if current_user else False
    })


@router.get('/positions/create')
async def create_position_form(request: Request, current_user: UserOrNoneDep):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/positions', status_code=303)

    return templates.TemplateResponse(
        name='positions/create.html',
        context={'request': request}
    )


@router.post('/positions/create')
async def create_position(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        name: str = Form(...)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/positions', status_code=303)

    try:
        new_position = PositionModel(name=name)
        session.add(new_position)
        await session.commit()

        logger.info(f'Admin {current_user.login} created position {name}')
        return RedirectResponse(url='/pages/positions', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error creating position: {str(e)}')

        return templates.TemplateResponse(
            name='positions/create.html',
            context={
                'request': request,
                'error': f'Error creating position: {str(e)}'
            }
        )


@router.get('/positions/update/{position_id}')
async def edit_position_form(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        position_id: int
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/positions', status_code=303)

    try:
        position = await get_item_from_db(position_id, PositionModel, session)

        return templates.TemplateResponse(
            name='positions/edit.html',
            context={
                'request': request,
                'position': position
            }
        )

    except Exception as e:
        logger.error(f'Error loading position for edit: {str(e)}')
        return RedirectResponse(url='/pages/positions', status_code=303)


@router.post('/positions/update/{position_id}')
async def update_position(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        position_id: int,
        name: str = Form(...)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/positions', status_code=303)

    try:
        position = await get_item_from_db(position_id, PositionModel, session)
        if not position:
            return RedirectResponse(url='/pages/positions', status_code=303)

        position.name = name
        await session.commit()

        logger.info(f'Admin {current_user.login} updated position {name}')
        return RedirectResponse(url='/pages/positions', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error updating position: {str(e)}')

        position = await get_item_from_db(position_id, PositionModel, session)

        return templates.TemplateResponse(
            name='positions/edit.html',
            context={
                'request': request,
                'position': position,
                'error': f'Error updating position: {str(e)}'
            }
        )
