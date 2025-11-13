from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..logger.logger import set_logger

from .models import EmployeeModel, PositionModel, DepartmentModel, UserModel
from app.schemas.employee import EmployeeSchema
from app.schemas.position import PositionSchema
from app.schemas.department import DepartmentSchema
from sqlalchemy.orm import selectinload

logger = set_logger("DB_UTILS")



async def write_to_db(data, session: AsyncSession):
    try:
        if isinstance(data, EmployeeSchema):
            new_item = EmployeeModel(**data.model_dump())
        elif isinstance(data, PositionSchema):
            new_item = PositionModel(**data.model_dump())
        elif isinstance(data, DepartmentSchema):
            new_item = DepartmentModel(**data.model_dump())
        else:
            logger.error(f"Unsupported data type: {type(data)}")
            return False

        session.add(new_item)
        await session.commit()
        logger.info("Item added to db")
        return True

    except Exception as e:
        logger.error(f"Failed to write to DB: {e}")
        await session.rollback()
        return False


async def get_all_items(model, session: AsyncSession, **filters):
    try:
        query = select(model)

        if filters:
            query = query.filter_by(**filters)

        result = await session.execute(query)
        items = result.scalars().all()

        logger.info(f'Items found: {len(items)} with filters: {filters}')
        return items

    except Exception as e:
        logger.error(f'Error get all items with {model} ===> {e}')
        return None

async def get_item_from_db(value, model, session: AsyncSession, field: str = 'id'):
    item = None
    try:
        if not hasattr(model, field):
            logger.info(f'Field {field} not found in model {model}')
            return None

        model_field = getattr(model, field)
        query = select(model).where(model_field == value) #type: ignore
        result = await session.execute(query)
        item = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f'Error get item with {field} = {value}: {item} ===> {e}')

    if item:
        logger.info(f'Item found with {field} = {value}: {item}')
        return item
    logger.info(f'Item not found with {field} = {value}: {item}')
    return None


async def update_item_in_db(id: int, model, new_data, session: AsyncSession):
    try:
        item = await get_item_from_db(id, model, session)
        if not item:
            logger.info(f"Item with id {id} not found for update")
            return False

        if isinstance(item, EmployeeModel):
            for field, value in new_data.model_dump(exclude_unset=True, exclude_none=True).items():
                if value is not None:
                    setattr(item, field, value)
        elif isinstance(item, PositionModel):
            item.name = new_data.name
        elif isinstance(item, DepartmentModel):
            item.name = new_data.name
        else:
            logger.error(f"Unsupported model type: {type(item)}")
            return False

        await session.commit()
        logger.info(f"Item with id {id} updated successfully")
        return True

    except Exception as e:
        logger.error(f"Error updating item with id={id} : {e}")
        await session.rollback()
        return False


async def delete_item_from_db(id, model, session: AsyncSession):
    try:
        item = await get_item_from_db(id, model, session)
        if item:
            await session.delete(item)
            await session.commit()
            logger.info('Item deleted')
            return True
        else:
            return False
    except Exception as e:
        logger.error(f'Error delete item with {id} : {model} ===> {e}')


async def get_items_with_relationship(model, session: AsyncSession, relations: list[str] = None, page: int = 1,
                                      size: int = 5, **filters):
    try:
        query = select(model)

        if relations:
            for relation in relations:
                query = query.options(selectinload(getattr(model, relation)))

        if filters:
            query = query.filter_by(**filters)

        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await session.execute(query)
        items = result.scalars().all()

        return items

    except Exception as e:
        logger.error(f'Error get items with relationship: {e}')
        return None


async def get_item_with_relationship(model, item_id, session: AsyncSession, relations: list[str] = None):

    query = select(model).where(model.id == item_id) #type: ignore

    if relations:
        for relation in relations:
            if relation == 'employee.department':
                query = query.options(
                    selectinload(UserModel.employee).selectinload(EmployeeModel.department)
                )
            elif relation == 'employee.position':
                query = query.options(
                    selectinload(UserModel.employee).selectinload(EmployeeModel.position)
                )
            elif relation == 'employee':
                query = query.options(selectinload(UserModel.employee))
            else:
                query = query.options(selectinload(getattr(model, relation)))

    result = await session.execute(query)
    return result.scalar_one_or_none()