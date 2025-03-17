from fastapi import APIRouter, HTTPException, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer
from app.models.ModelTasks import create_task, delete_task, get_all_tasks, get_tasks_by_user_id, update_task
from app.schemas.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services.utils import get_current_user, payload, role_required


router = APIRouter(prefix="/tasks", tags=["tasks"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.post("/create", response_model=TaskResponse, dependencies=[Depends(role_required(["socio", "senior", "consultor"]))])
async def create_task_endpoint(task_data: TaskCreate,  token: str = Depends(oauth2_scheme)):

    """ creates a new task """

    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    task = create_task(task_data)
    if "error" in task:
        raise HTTPException(status_code=400, detail=task["error"])
    return task


@router.get("/get_task")
async def get_tasks_endpoint( token: str = Depends(oauth2_scheme)):

    """ get all the tasks """

    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    return get_all_tasks()


@router.get("/get_tasks_by_user")
async def get_task_endpoint(token: str = Depends(oauth2_scheme)):

    """ get a task by the user id """

    user_data = payload(token)
    
    if not user_data or "id" not in user_data:

        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    return get_tasks_by_user_id(user_data["id"])


@router.put("/{task_id}")
async def update_task_endpoint(task_id: int, task_data: TaskUpdate, user : dict = Depends(role_required(["socio", "senior", "consultor"])), token: str = Depends(oauth2_scheme)):

    """  update a tasks """

    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    task = update_task(task_id, task_data)

    if "error" in task:

        raise HTTPException(status_code=400, detail=task["error"])
    
    return task


@router.delete("/delete/{task_id}", dependencies=[Depends(role_required(["socio", "senior"]))])
async def delete_task_endpoint(task_id: int, token: str = Depends(oauth2_scheme)):

    """ delete a task """

    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    result = delete_task(task_id)

    if "error" in result:

        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
