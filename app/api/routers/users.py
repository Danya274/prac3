from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger.logger import set_logger

from .auth import create_access_token, get_password_hash, auth_user

from app.schemas.user import UserRegSchema, UserAuthSchema, UserResponseSchema
from app.schemas.default import DefaultResponse

from app.database.db import get_session
from app.database.models import UserModel, EmployeeModel
from app.database.db_utils import get_item_from_db, get_all_items

from .dependencies import CurrentUserDep, CurrentAdminDep

SessionDep = Annotated[AsyncSession, Depends(get_session)]

logger = set_logger('USERS')
user_router = APIRouter(tags=['Users'])

@user_router.post('/register')
async def register_user(user_data: UserRegSchema, session: SessionDep):
    try:
        employee = await get_item_from_db(user_data.employee_id, EmployeeModel, session)
        if not employee:
            logger.info(f'Employee with id {user_data.employee_id} not found')
            return DefaultResponse(
                error=True,
                message='Employee not found'
            )

        exist_user = await get_all_items(UserModel, session, filters={'login': user_data.login})

        if exist_user:
            logger.info(f'User with login: {user_data.login} already exist')
            return DefaultResponse(
                error=True,
                message='User with this login already exist'
            )

        exist_employee_user = await get_all_items(UserModel, session, filters={'employee_id': user_data.employee_id})

        if exist_employee_user:
            logger.info(f'Employee with id: {user_data.employee_id} already has user accoutn')
            return DefaultResponse(
                error=True,
                message='Employee with this id already has user account'
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = UserModel(
            login=user_data.login,
            password=hashed_password,
            employee_id=user_data.employee_id,
            is_user=True
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info(f'User {user_data.login} registred successfully for employee {user_data.employee_id}')
        return DefaultResponse(
            error=False,
            message='User registred successfully',
            payload=UserResponseSchema(
                id=new_user.id,
                login=new_user.login,
                employee_id=new_user.employee_id,
                is_admin=new_user.is_admin
            )
        )


    except Exception as e:
        await session.rollback()
        logger.error(f'Error register user with id: {user_data.employee_id} ===> {e}')
        return DefaultResponse(
            error=True,
            message=f'Registr error: {e}'
        )

@user_router.post('/login')
async def login_user(user_data: UserAuthSchema, response: Response, session: SessionDep):
    check_user = await auth_user(user_data.login, user_data.password, session)
    if check_user is None:
        logger.info('Incorrect login or password')
        return DefaultResponse(
            error=True,
            message='Incorrect login or password'
        )
    access_token = create_access_token({'sub': str(check_user.id)})
    response.set_cookie(key='users_access_token', value=access_token, httponly=True)
    logger.info('User log in successfully')
    return DefaultResponse(
        error=False,
        message='User log in successfully',
        payload={
            'access_token': access_token,
            'refresh_token': None
        }
    )


@user_router.post('/logout')
async def logouth_user(response: Response):
    response.delete_cookie(key='users_access_token')
    logger.info('User log outh successfully')
    return DefaultResponse(
        error=False,
        message='User log out successfully'
    )

@user_router.get('/me')
async def get_me(user_data: CurrentUserDep):
    return user_data

@user_router.get('/users')
async def get_users(admin: CurrentAdminDep, session: SessionDep):
    if admin is None:
        logger.info(f'User try to get all users')
        return DefaultResponse(
            error=True,
            message='Not enough permissions'
        )

    users = await get_all_items(UserModel, session)
    users_schemas = [UserResponseSchema(
        id=user.id,
        login=user.login,
        employee_id=user.employee_id,
        is_admin=user.is_admin
    ) for user in users]
    logger.info(f'Admin {admin.id} get all users')
    return DefaultResponse(
        error=False,
        message='All users',
        payload=users_schemas
    )