from datetime import date
from typing import Annotated

from fastapi import Depends, APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import get_password_hash
from app.api.routers.dependencies import UserOrNoneDep
from fastapi.responses import RedirectResponse

from app.database.db import get_session
from app.database.db_utils import get_all_items, get_items_with_relationship, get_item_with_relationship, \
    update_item_in_db, delete_item_from_db
from app.database.models import EmployeeModel, DepartmentModel, PositionModel, UserModel

from app.logger.logger import set_logger
from app.schemas.employee import EmployeeUpdateSchema, EmployeeSchema

logger = set_logger('EMPLOYEES_WEB')
SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix='/pages', tags=['Frontend_employees'])
templates = Jinja2Templates(directory='app/templates')




@router.get('/employee_list')
async def get_employee_list(request: Request,
                            session: SessionDep,
                            current_user: UserOrNoneDep,
                            page: int = 1,
                            size: int = 5,
                            FIO_search: str = None,
                            department_id: str = None,
                            position_id: str = None,
                            salary_from: str = None,
                            salary_to: str = None,
                            ):
    department_id_int = int(department_id) if department_id and department_id != "" else None
    position_id_int = int(position_id) if position_id and position_id != "" else None
    salary_from_float = float(salary_from) if salary_from and salary_from != "" else None
    salary_to_float = float(salary_to) if salary_to and salary_to != "" else None

    filters = {}

    if department_id_int:
        filters['department_id'] = department_id_int
    if position_id_int:
        filters['position_id'] = position_id_int

    all_employees = await get_all_items(EmployeeModel, session, **filters)
    filtered_employees = all_employees if all_employees else []
    if FIO_search and FIO_search != '':
        filtered_employees = [
            emp for emp in filtered_employees if FIO_search.lower() in emp.name.lower()
        ]

    if salary_from_float is not None:
        filtered_employees = [
            emp for emp in filtered_employees if emp.salary >= salary_from_float
        ]

    if salary_to_float is not None:
        filtered_employees = [
            emp for emp in filtered_employees if emp.salary <= salary_to_float
        ]

    total_employees = len(filtered_employees)
    total_pages = (total_employees + size - 1) // size if total_employees > 0 else 1

    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_employees = filtered_employees[start_idx:end_idx]

    for employee in paginated_employees:
        await session.refresh(employee, ['department', 'position', 'user'])

    departments = await get_all_items(DepartmentModel, session)
    positions = await get_all_items(PositionModel, session)

    return templates.TemplateResponse(name='employee_list.html', context={
        'request': request,
        'employees': paginated_employees,
        'current_user': current_user,
        'is_admin': current_user.is_admin if current_user else False,
        'current_page': page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'FIO_search': FIO_search or '',
        'selected_department_id': department_id_int,
        'selected_position_id': position_id_int,
        'salary_from': salary_from or '',
        'salary_to': salary_to or '',
        'departments': departments,
        'positions': positions,
    })


@router.get('/employees/create')
async def create_employee_form(request: Request, session: SessionDep, current_user: UserOrNoneDep):
    if not current_user or not current_user.is_admin:
        logger.info('Unauthorized user tried to create employee')
        return RedirectResponse(url='/pages/employee_list', status_code=303)

    departments = await get_all_items(DepartmentModel, session)
    positions = await get_all_items(PositionModel, session)

    logger.info(f'Admin {current_user.login} visited create employee page')
    return templates.TemplateResponse(
        name='employees/create.html',
        context={
            'request': request,
            'departments': departments,
            'positions': positions
        }
    )


@router.post('/employees/create')
async def create_employee(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        name: str = Form(...),
        date_of_birth: str = Form(...),
        status: str = Form(...),
        department_id: str = Form(...),
        position_id: str = Form(...),
        rate: str = Form(...),
        salary: str = Form(...),
        date_of_employment: str = Form(...),
        login: str = Form(...),
        password: str = Form(...)
):
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url='/pages/employee_list', status_code=303)

    try:
        employee_data = EmployeeSchema(
            name=name,
            date_of_birth=date.fromisoformat(date_of_birth),
            status=status,
            department_id=int(department_id),
            position_id=int(position_id),
            rate=float(rate),
            salary=float(salary),
            date_of_employment=date.fromisoformat(date_of_employment)
        )


        new_employee = EmployeeModel(**employee_data.model_dump())
        session.add(new_employee)
        await session.flush()
        hash_password = get_password_hash(password)
        new_user = UserModel(
            login=login,
            password=hash_password,
            employee_id=new_employee.id
        )

        session.add(new_user)
        await session.commit()

        logger.info(f'Admin {current_user.login} created employee {name} with user {login}')
        return RedirectResponse(url='/pages/employee_list', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error creating employee: {str(e)}')

        departments = await get_all_items(DepartmentModel, session)
        positions = await get_all_items(PositionModel, session)

        return templates.TemplateResponse(
            name='employees/create.html',
            context={
                'request': request,
                'departments': departments,
                'positions': positions,
                'error': f'Error creating employee'
            }
        )



@router.get('/employees/delete/{employee_id}')
async def delete_employee(employee_id: int, session: SessionDep, current_user: UserOrNoneDep):

    if not current_user or not current_user.is_admin:
        logger.info('User not logged in try to delete employee or user not admin')
        return RedirectResponse(url='/pages/employee_list', status_code=303)

    try:
        logger.info(f'Admin {current_user.login} try to delete employee with id: {employee_id}')
        result = await delete_item_from_db(employee_id, EmployeeModel, session)
        if result:
            logger.info(f'Employee with id: {employee_id} deleted successfully')
        else:
            logger.info(f'Employee with id: {employee_id} not found')

    except Exception as e:
        await session.rollback()
        logger.error(f'Error deleting employee {employee_id} ===> {e}')

    return RedirectResponse(url='/pages/employee_list', status_code=303)

@router.get('/employees/update/{employee_id}')
async def update_employee_form(request: Request, employee_id: int, session: SessionDep, current_user: UserOrNoneDep):
    if not current_user or not current_user.is_admin:
        logger.info(f'User (not admin) try to update employee with id: {employee_id}')
        return RedirectResponse(url='/pages/employee_list', status_code=303)
    try:
        employee = get_item_with_relationship(EmployeeModel, employee_id, session, relations=['department', 'position', 'user'])
        if not employee:
            logger.info(f'Employee with id: {employee_id} not found')
            return RedirectResponse(url='/pages/employee_list', status_code=303)
        else:
            departments = await get_items_with_relationship(DepartmentModel, session)
            positions = await get_items_with_relationship(PositionModel, session)
            return templates.TemplateResponse(name='employees/edit.html', context={
                'request': request,
                'employee': employee,
                'departments': departments,
                'positions': positions,
            })

    except Exception as e:
        await session.rollback()
        logger.error(f'Error updating employee {employee_id} ===> {e}')


@router.post('/employees/update/{employee_id}')
async def update_employee(
        request: Request,
        session: SessionDep,
        current_user: UserOrNoneDep,
        employee_id: int,
        name: str = Form(None),
        date_of_birth: str = Form(None),
        status: str = Form(None),
        department_id: str = Form(None),
        position_id: str = Form(None),
        rate: str = Form(None),
        salary: str = Form(None),
        date_of_employment: str = Form(None)
):

    if not current_user or not current_user.is_admin:
        logger.info(f'User (not admin) try to update employee with id: {employee_id}')
        return RedirectResponse(url='/pages/employee_list', status_code=303)

    try:
        department_id_int = int(department_id) if department_id else None
        position_id_int = int(position_id) if position_id else None
        rate_float = float(rate) if rate else None
        salary_float = float(salary) if salary else None

        date_of_birth_date = date.fromisoformat(date_of_birth) if date_of_birth and date_of_birth != "" else None
        date_of_employment_date = date.fromisoformat(
        date_of_employment) if date_of_employment and date_of_employment != "" else None

        update_dict = {}
        if name is not None and name != "": update_dict['name'] = name
        if date_of_birth_date is not None: update_dict['date_of_birth'] = date_of_birth_date
        if status is not None and status != "": update_dict['status'] = status
        if department_id_int is not None: update_dict['department_id'] = department_id_int
        if position_id_int is not None: update_dict['position_id'] = position_id_int
        if rate_float is not None: update_dict['rate'] = rate_float
        if salary_float is not None: update_dict['salary'] = salary_float
        if date_of_employment_date is not None: update_dict['date_of_employment'] = date_of_employment_date

        update_data = EmployeeUpdateSchema(**update_dict)
        result = await update_item_in_db(employee_id, EmployeeModel, update_data, session)

        if result:
            logger.info(f'Employee with id: {employee_id} updated successfully')
            return RedirectResponse(url='/pages/employee_list', status_code=303)
        else:
            logger.info(f'Failed to update employee with id: {employee_id}')
            return RedirectResponse(url='/pages/employee_list', status_code=303)

    except Exception as e:
        await session.rollback()
        logger.error(f'Error updating employee {employee_id} ===> {e}')

        departments = await get_items_with_relationship(DepartmentModel, session)
        positions = await get_items_with_relationship(PositionModel, session)
        employee = await get_item_with_relationship(EmployeeModel, employee_id, session, relations=['department', 'position', 'user'])


        return templates.TemplateResponse(
            name='employees/edit.html',
            context={
                'request': request,
                'employee': employee,
                'departments': departments,
                'positions': positions,
                'current_user': current_user,
                'error': 'Error updating employee'
            }
        )
