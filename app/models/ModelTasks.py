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
    print("task_data:", task_data)

    task_dict = task_data.dict()
    

    
    response = supabase.table("tasks").insert(task_dict).execute()

    if response.data:

        return response.data[0]
    
    else:

        return {"error": response.error}


def get_all_tasks_by_client(client_id: int):
    """get all task from de client id"""

    response = supabase.table("tasks").select(
        "id, title, client_id, clients!inner(name, active), area"
    ).eq("client_id", client_id).eq('clients.active', True).execute()


    if not response.data:
        return HTTPException(status_code=404, detail="No se encontraron tareas para el cliente proporcionado")
    

    tasks = [
        {
            "id": task["id"],
            "title": task["title"], 
            "client": task["clients"]["name"] if task["clients"] else "Sin Cliente",
            "area": task.get("area"),
            "billing_type": task.get("billing_type"),
            "note": task.get("note"),
            "total_value": task.get("total_value")
        }
        for task in response.data
    ]
    return tasks


def get_all_tasks(user_id: int = None):
    """get the task with the client and the user assigned"""

    if user_id:
        # Get client IDs associated with the user
        client_user_response = supabase.table('client_user').select('client_id').eq('user_id', user_id).execute()

        if client_user_response.data:
            client_ids = [item['client_id'] for item in client_user_response.data]

            # Filter tasks based on the retrieved client IDs and active clients
            response = supabase.table("tasks").select(
                "id, title, client_id, clients!inner(name, active), area, total_billed, total_value, billing_type, note, permanent, monthly_limit_hours_tasks, assignment_date,facturado,asesoria_tarif,coin, assigned_user_name"
            ).in_('client_id', client_ids).eq('clients.active', True).execute()
        else:
            return []
    else:
        # Get all tasks from active clients
        response = supabase.table("tasks").select(
            "id, title, note, client_id, clients!inner(name, active), area, total_billed,total_value,billing_type, permanent, monthly_limit_hours_tasks,assignment_date,facturado,asesoria_tarif,coin, assigned_user_name"
        ).eq('clients.active', True).execute()

    if not response.data:
        return []

    tasks = [
        {
            "id": task["id"],
            "title": task["title"],
            "assignment_date": task["assignment_date"],
            "client": task["clients"]["name"] if task["clients"] else "Sin Cliente",
            "area": task.get("area"),
            "billing_type": task.get("billing_type"),
            "note": task.get("note"),
            "total_value": task.get("total_value"),
            "total_billed": task.get("total_billed"),
            "permanent": task.get("permanent"),
            "monthly_limit_hours_tasks": task.get("monthly_limit_hours_tasks"),
            "facturado": task.get("facturado"),
            "asesoria_tarif": task.get("asesoria_tarif"),
            "coin": task.get("coin"),
            "assigned_user_name": task.get("assigned_user_name")
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

    
    


    response = supabase.table("tasks").update(task_dict).eq("id", task_id).execute()

    if response.data:
        return response.data
    else:
        raise HTTPException(status_code=400, detail=response.error)
    

def delete_task(task_id: int):
    """ remove a tasks """
    try:
        # Delete time entries first
        response_time_entries = supabase.table("time_entries").delete().eq("task_id", task_id).execute()
        
        # Delete the task
        response = supabase.table("tasks").delete().eq("id", task_id).execute()
        
        if hasattr(response, 'error') and response.error:
            return {"error": f"No se pudo eliminar la tarea: {response.error}"}
        else:
            return {"message": "Tarea eliminada correctamente"}
            
    except Exception as e:
        return {"error": f"Error al eliminar la tarea: {str(e)}"}
    



def assigned_tasks(user_id: int):
    """ get the tasks assigned to a user """

    try:
        # Get the client IDs associated with the user
        response_relation = supabase.table("client_user").select("client_id").eq("user_id", user_id).execute()

        if not response_relation.data:
            raise HTTPException(status_code=404, detail="No se encontraron clientes asignados al usuario")
        
        # Get the task IDs associated with the retrieved client IDs and active clients
        client_ids = [client["client_id"] for client in response_relation.data]
        response_task = supabase.table("tasks").select(
            "id, client_id, clients!inner(active)"
        ).in_("client_id", client_ids).eq('clients.active', True).execute()

        if not response_task.data:
            return []
        
        # Return the task IDs along with their associated client IDs
        return [{"task_id": task["id"], "client_id": task["client_id"]} for task in response_task.data]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener las tareas asignadas: {str(e)}")
