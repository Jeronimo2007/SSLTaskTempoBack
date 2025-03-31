

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from app.database.data import supabase

from app.schemas.schemas import TaskCreate, TaskUpdate



def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """ Convierte un objeto datetime a string en formato ISO 8601 """
    return dt.isoformat() if dt else None


def create_task(task_data: TaskCreate):

    """ creates a new task in the database """

    task_dict = task_data.dict()
    task_dict["due_date"] = format_datetime(task_data.due_date)

    response = supabase.table("tasks").insert(task_dict).execute()

    if response.data:

        return response.data[0]
    
    else:

        return {"error": response.error}


def get_all_tasks(user_id: int = None):
    """get the task with the client and the user assigned"""

    if user_id:
        # Get client IDs associated with the user
        client_user_response = supabase.table('client_user').select('client_id').eq('user_id', user_id).execute()

        if client_user_response.data:
            client_ids = [item['client_id'] for item in client_user_response.data]

            # Filter tasks based on the retrieved client IDs
            response = supabase.table("tasks").select(
                "id, title, status, due_date, client_id, clients(name), area"
            ).in_('client_id', client_ids).execute()
        else:
            return []
    else:
        response = supabase.table("tasks").select(
            "id, title, status, due_date, client_id, clients(name), area"
        ).execute()

    if not response.data:
        return []

    tasks = [
        {
            "id": task["id"],
            "title": task["title"],
            "status": task["status"],
            "due_date": task["due_date"],
            "client": task["clients"]["name"] if task["clients"] else "Sin Cliente",
            "area": task["area"]
        }
        for task in response.data
    ]

    return tasks


def get_tasks_by_user_id(user_id: int):

    """ get a task by user id """

    response = supabase.table("tasks").select("*").eq("assigned_to_id", user_id).execute()

    return response.data



def update_task(task_data: TaskUpdate):
    """ Update a task by id """
    
    task_id = task_data.id

    task_dict = task_data.dict(exclude_unset=True)

    
    if isinstance(task_dict.get("due_date"), str):
        try:
            task_dict["due_date"] = datetime.fromisoformat(task_dict["due_date"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa ISO 8601 (YYYY-MM-DDTHH:MM:SS).")

   
    task_dict["due_date"] = format_datetime(task_dict["due_date"])

    response = supabase.table("tasks").update(task_dict).eq("id", task_id).execute()

    if response.data:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)
    

def delete_task(task_id: int):

    """ remove a tasks """

    response_time_entries = supabase.table("time_entries").delete().eq("task_id", task_id).execute()

    if not response_time_entries.data:
        return {"error": response_time_entries.error}

    response = supabase.table("tasks").delete().eq("id", task_id).execute()

    if response.data:

        return {"message": "Tarea eliminada correctamente"}
    
    else:

        return {"error": response.error}
    



def assigned_tasks(user_id: int):
    """ get the tasks assigned to a user """

    try:
        # Get the client IDs associated with the user
        response_relation = supabase.table("client_user").select("client_id").eq("user_id", user_id).execute()

        if not response_relation.data:
            raise HTTPException(status_code=404, detail="No se encontraron clientes asignados al usuario")
        
        # Get the task IDs associated with the retrieved client IDs
        client_ids = [client["client_id"] for client in response_relation.data]
        response_task = supabase.table("tasks").select("id, client_id").in_("client_id", client_ids).execute()

        if not response_task.data:
            return []
        
        # Return the task IDs along with their associated client IDs
        return [{"task_id": task["id"], "client_id": task["client_id"]} for task in response_task.data]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las tareas asignadas: {str(e)}")

    return response.data if response.data else []