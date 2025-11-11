import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.responses import FileResponse

from app.api.routers.employees import employee_router
from app.api.routers.departments import department_router
from app.api.routers.positions import positions_router
from app.api.routers.users import user_router

from fastapi.staticfiles import StaticFiles

from app.api.pages.auth_web import router as auth_web_router
from app.api.pages.employees_web import router as employees_web_router
from app.api.pages.departments_web import router as departments_web_router
from app.api.pages.positions_web import router as positions_web_router

from app.database.db import setup_database

from app.logger.logger import set_logger

logger = set_logger('MAIN')



@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('Running startup event')
    await setup_database()
    logger.info('Finished startup event')
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(employee_router)
app.include_router(department_router)
app.include_router(positions_router)
app.include_router(user_router)

app.include_router(auth_web_router)
app.include_router(employees_web_router)
app.include_router(departments_web_router)
app.include_router(positions_web_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get('/images/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("app/static/images/favicon.ico")


if __name__ == '__main__':
    try:
        uvicorn.run('main:app', host='0.0.0.0', port=8000)
    except Exception as e:
        logger.error(f'Error {e}')
    except KeyboardInterrupt:
        logger.info(f'Interrupted by user')