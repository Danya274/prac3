from fastapi import APIRouter, Depends

from typing import Annotated

from app.database.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.default import DefaultResponse
from app.schemas.position import PositionSchema
from app.database.db_utils import get_item_from_db, update_item_in_db, delete_item_from_db, write_to_db, get_all_items
from app.database.models import PositionModel


from app.logger.logger import set_logger

SessionDep = Annotated[AsyncSession, Depends(get_session)]

positions_router = APIRouter(tags=['Positions'])
logger = set_logger('POSITIONS')

@positions_router.get("/positions")
async def get_positions(session: SessionDep):
    items = await get_all_items(PositionModel, session)
    if items:
        all_positions = []
        for item in items:
            position = PositionSchema(
                    name=item.name,
                )
            all_positions.append(position)
        logger.info(f'Positions found: {len(all_positions)}')
        return DefaultResponse(
            error=False,
            message='All positions',
            payload=all_positions
        )
    else:
        logger.info('No positions found')
        return DefaultResponse(
            error=True,
            message='No positions found',
        )


@positions_router.delete("/positions")
async def delete_position(id: int, session: SessionDep):
    try:
        deleted = await delete_item_from_db(id, PositionModel, session)
        if deleted:
            logger.info(f'Position with id: {id} deleted from db')
            return DefaultResponse(
                error=False,
                message='Position deleted successfuly'
            )
        else:
            logger.info(f'Position with id: {id} not deleted')
            return DefaultResponse(
                error=True,
                message='Position not deleted'
            )
    except Exception as e:
        logger.error(f'Error delete position with id: {id}  ===> {e}')

@positions_router.get("/positions/{position_id}")
async def get_position(position_id: int, session: SessionDep):
    try:
        item = await get_item_from_db(position_id, PositionModel, session)
        if item:
            logger.info(f'Position with id: {position_id} found')
            return DefaultResponse(
                error=False,
                message='Position found',
                payload=PositionSchema(
                    name=item.name,
                )
            )
    except Exception as e:
        logger.error(f'Error get position with id: {position_id}  ===> {e}')
    logger.info(f'Position with id: {position_id} not found')
    return DefaultResponse(
            error=True,
            message='Position not found',
        )

@positions_router.post("/positions")
async def post_position(position: PositionSchema, session: SessionDep):
    logger.info(f'Position added to db')
    result = await write_to_db(position, session)
    if result:
        logger.info('Position added successfuly')
        return DefaultResponse(
            error=False,
            message='Position added successfuly'
        )
    else:
        logger.info('Position not added')
        return DefaultResponse(
            error=True,
            message='Position not added'
        )


@positions_router.put("/positions/{position_id}")
async def update_position(position_id: int, position: PositionSchema, session: SessionDep):
    try:
        logger.info(f'Update request for position with id: {position_id}: {position}')
        update_data = position.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            return DefaultResponse(
                error=True,
                message='No fields to update'
            )

        logger.info(f'Fields to update: {update_data}')

        success = await update_item_in_db(position_id, PositionModel, position, session)

        if success:
            logger.info(f'Position with id: {position_id} updated successfuly')
            return DefaultResponse(
                error=False,
                message='Position updated successfully'
            )
        else:
            logger.info('Position not found or update failed')
            return DefaultResponse(
                error=True,
                message='Position not found or update failed'
            )

    except Exception as e:
        await session.rollback()
        logger.error(f'Error update position with id: {position_id}: {e}')
        return DefaultResponse(
            error=True,
            message=f'Error update failed: {e}'
        )