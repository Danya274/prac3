from passlib.context import CryptContext

from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_auth_data
from datetime import datetime, timedelta, timezone

from app.database.db_utils import get_item_from_db
from app.database.models import UserModel

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({'exp': expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt

async def auth_user(login, password, session: AsyncSession):
    user = await get_item_from_db(login, UserModel, session, field='login')
    if not user or verify_password(password, user.password) is False:
        return None
    return user