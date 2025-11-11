from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from .models import Base

import asyncio

from ..core.config import get_db_url

from ..logger.logger import set_logger

logger = set_logger('DB')
DB_URL = get_db_url()
engine = create_async_engine(DB_URL)
session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with session() as s:
        yield s


async def setup_database():
    await asyncio.sleep(5)
    async with engine.begin() as conn:
        logger.info('Setting up database')
        await conn.run_sync(Base.metadata.create_all)