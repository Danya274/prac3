from typing import Annotated

from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import auth_user, create_access_token
from app.api.routers.dependencies import UserOrNoneDep
from fastapi.responses import RedirectResponse

from app.database.db import get_session
from app.database.db_utils import get_item_with_relationship
from app.database.models import UserModel

from app.logger.logger import set_logger

logger = set_logger('AUTH_WEB')
SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix='/pages', tags=['Frontend_auth'])
templates = Jinja2Templates(directory='app/templates')

@router.get('/')
async def index_page(request: Request, current_user: UserOrNoneDep):
    if current_user is None:
        return templates.TemplateResponse(name='index.html', context={'request': request, 'login': 1})
    return templates.TemplateResponse(name= 'index.html', context={'request': request, 'login': 0})


@router.get('/profile')
async def profile_page(request: Request, current_user: UserOrNoneDep, session: SessionDep):
    if not current_user:
        logger.info(f'User not logged in visited profile page')
        return templates.TemplateResponse(name='profile.html', context={'request': request, 'current_user': None})
    logger.info(f'User {current_user.login} visited profile page')
    user = await get_item_with_relationship(
        UserModel,
        current_user.id,
        session,
        relations=['employee', 'employee.department', 'employee.position'])


    return templates.TemplateResponse(name='profile.html', context={'request': request, 'current_user': user})


@router.get('/login')
async def get_login_html(request: Request):
    logger.info('User visited login page')
    return templates.TemplateResponse(name='login_form.html', context={'request': request})


@router.post('/login')
async def login_user(request: Request, session: SessionDep, login: str = Form(...), password: str = Form(...)):
    user = await auth_user(login, password, session)
    if not user:
        logger.info('User try to log in with incorrect login or password')
        return templates.TemplateResponse(name='login_form.html', context={'request': request, 'error': 'Invalid login or password'})

    access_token = create_access_token({'sub': str(user.id)})
    redirect = RedirectResponse(url='/pages/', status_code=303)
    redirect.set_cookie(key='users_access_token', value=access_token, httponly=True, path='/')
    logger.info(f'User {user.login} log in successfully')
    return redirect


@router.get('/logout')
async def logout_user():
    redirect = RedirectResponse(url='/pages/', status_code=303)
    redirect.delete_cookie(key='users_access_token')
    logger.info(f'User log out successfully')
    return redirect