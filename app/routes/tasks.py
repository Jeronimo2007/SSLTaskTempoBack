from fastapi import APIRouter, HTTPException, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer
from app.models.ModelTasks import create_task, delete_task, get_all_tasks, get_all_tasks_by_client, get_tasks_by_user_id, update_task, assigned_tasks
from app.schemas.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services.utils import get_current_user, payload, role_required


router = APIRouter(prefix="/tasks", tags=["tasks"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.post("/create", dependencies=[Depends(role_required(["socio", "senior", "consultor"]))])
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
async def get_tasks_endpoint(token: str = Depends(oauth2_scheme)):
    """get all the tasks"""

    user_data = payload(token)

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    user_id = user_data.get("id")
    user_role = user_data.get("role")  # Assuming the role is in the payload

    if user_role == "consultor":
        response = get_all_tasks(user_id=user_id)
    else:
        response = get_all_tasks()

    return response



@router.get('/get_tasks_by_client')
async def get_tasks_by_client(client_id: int):
    """
    Get all tasks by client ID.
    """
    try:
        # Llamar a la función get_tasks_by_client con el client_id proporcionado
        response = get_all_tasks_by_client(client_id=client_id)
        return response

    except HTTPException as e:
        # Re-lanzar excepciones HTTP conocidas
        raise e
    except Exception as e:
        # Manejo genérico de errores
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    


@router.get("/get_tasks_by_user")
async def get_task_endpoint(token: str = Depends(oauth2_scheme)):

    """ get a task by the user id """

    user_data = payload(token)
    
    if not user_data or "id" not in user_data:

        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    return get_tasks_by_user_id(user_data["id"])


@router.put("/update/{task_id}")
async def update_task_endpoint(task_data: TaskUpdate, user : dict = Depends(role_required(["socio", "senior", "consultor"])), token: str = Depends(oauth2_scheme)):

    """  update a tasks """

    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    task = update_task(task_data)

    if "error" in task:

        raise HTTPException(status_code=400, detail=task["error"])
    
    return task


@router.delete("/delete/{task_id}", dependencies=[Depends(role_required(["socio", "senior"]))])
async def delete_task_endpoint(task_id: int, token: str = Depends(oauth2_scheme)):

    """ delete a task """

    user_data = payload(token)

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # Validate task_id
    if not isinstance(task_id, int) or task_id <= 0:
        raise HTTPException(status_code=400, detail="ID de tarea inválido")

    result = delete_task(task_id)

    if "error" in result:
        # Determine appropriate status code based on error type
        if "no existe" in result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    # Return success response with the expected format
    return {"success": True, "message": result.get("message", "Tarea eliminada correctamente")}




@router.get('/get_assigned_tasks')
async def get_assigned_tasks(user_id: int, token: str = Depends(oauth2_scheme)):
    """
    Get the tasks assigned to a specific user.
    """
    try:
        # Validar el token y obtener los datos del usuario
        user_data = payload(token)
        if not user_data or "id" not in user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        # Llamar a la función assigned_tasks con el user_id proporcionado
        response = assigned_tasks(user_id)
        return response

    except HTTPException as e:
        # Re-lanzar excepciones HTTP conocidas
        raise e
    except Exception as e:
        # Manejo genérico de errores
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")