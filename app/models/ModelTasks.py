

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


def get_all_tasks():
    """ get the task with the client and the user assigned """

    response = supabase.table("tasks").select(
        "id, title, status, due_date, client_id, clients(name), assigned_to_id, users(username)"
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
            "assigned_to": task["users"]["username"] if task["users"] else "Sin Asignado"
        }
        for task in response.data
    ]

    return tasks


def get_tasks_by_user_id(user_id: int):

    """ get a task by user id """

    response = supabase.table("tasks").select("*").eq("assigned_to_id", user_id).execute()

    return response.data



def update_task(task_id: int, task_data: TaskUpdate):
    """ Update a task by id """
    
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