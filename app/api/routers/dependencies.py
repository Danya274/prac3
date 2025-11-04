from datetime import datetime, timezone
from typing import Annotated

from fastapi import Request, Depends
from jose import jwt

from app.core.config import get_auth_data

from app.database.db_utils import get_item_from_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_session
from app.database.models import UserModel

from app.logger.logger import set_logger


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserOrNone = UserModel | None
TokenOrNone = str | None

logger = set_logger('DEPENDENCIES')
def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        return None
    return token
TokenOrNoneDep = Annotated[TokenOrNone, Depends(get_token)]


async def get_current_user(token: TokenOrNoneDep, session: SessionDep):
    if token is None:
        logger.info('No token found')
        return None
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except Exception as e:
        logger.error(f'Invalid token: {e}')
        return None

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        logger.info('Token expired')
        return None
    user_id = payload.get('sub')
    if not user_id:
        logger.info('User not found')
        return None

    user = await get_item_from_db(int(user_id), UserModel, session)
    if not user:
        logger.info('User not found')
        return None

    return user

UserOrNoneDep = Annotated[UserOrNone, Depends(get_current_user)]

async def get_current_admin(current_user: UserOrNoneDep):
    if current_user is None:
        return None
    if current_user.is_admin:
        return current_user
    return None


CurrentUserDep = Annotated[UserOrNone, Depends(get_current_user)]
CurrentAdminDep = Annotated[UserOrNone, Depends(get_current_admin)]