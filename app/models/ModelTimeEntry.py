from app.database.data import supabase
from datetime import datetime, timedelta, timezone
from app.schemas.schemas import TimeEntryCreate, TimeEntryCreateByTime, TimeEntryUpdate, getEntries


def calculate_duration(start_time: datetime, end_time: datetime) -> float:
    """ return the duration in hours """

    return (end_time - start_time).total_seconds() / 3600



def create_time_entry_by_time(data:TimeEntryCreateByTime):
    """create a time entry by time"""

    end_time = data.start_time + timedelta(hours=data.duration)

    response = supabase.table("time_entries").insert({
        "task_id": data.task_id,
        "user_id": data.user_id,
        "start_time": data.start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": data.description

    }).execute()

    if response.data: return response.data[0]
    else: return {"error": response.error}


def create_time_entry(user_id: int, entry_data: TimeEntryCreate):
    """ create a new time entry in supabase """
    
    # Ensure both datetimes are timezone-aware
    if entry_data.start_time.tzinfo is None:
        entry_data.start_time = entry_data.start_time.replace(tzinfo=timezone.utc)
    if entry_data.end_time.tzinfo is None:
        entry_data.end_time = entry_data.end_time.replace(tzinfo=timezone.utc)

    if entry_data.start_time >= entry_data.end_time:
        return {"error": "La hora de inicio debe ser menor a la hora de finalización."}

    duration = calculate_duration(entry_data.start_time, entry_data.end_time)

    response = supabase.table("time_entries").insert({
        "task_id": entry_data.task_id,
        "user_id": user_id,
        "duration": duration,
        "start_time": entry_data.start_time.isoformat(),
        "end_time": entry_data.end_time.isoformat(),
        "description": entry_data.description
    }).execute()

    if response.data:
        return response.data[0]
    else:
        return {"error": response.error}
    

def get_all_time_entries(data: getEntries):

    """ get all the time entries between start_date and end_date """

    response = supabase.table("time_entries").select("*").gte("start_time", data.start_date.isoformat()).lte("end_time", data.end_date.isoformat()).execute()

    return response.data if response.data else []


def get_time_entry(entry_id: int):

    """ get a time entry by the id"""
    
    response = supabase.table("time_entries").select("*").eq("id", entry_id).execute()

    return response.data[0] if response.data else None

def update_time_entry(entry_id: int, entry_data: TimeEntryUpdate):

    """ update a time entry """

    update_data = entry_data.dict(exclude_unset=True)
    
    if "start_time" in update_data and "end_time" in update_data:

        if update_data["start_time"] >= update_data["end_time"]:

            return {"error": "La hora de inicio debe ser menor a la hora de finalización."}
        
        update_data["duration"] = calculate_duration(update_data["start_time"], update_data["end_time"])

    response = supabase.table("time_entries").update(update_data).eq("id", entry_id).execute()

    return response.data[0] if response.data else {"error": response.error}

def delete_time_entry(entry_id: int):

    """ Delete a time Entry """
    
    try:
        response = supabase.table("time_entries").delete().eq("id", entry_id).execute()
        return {"message": "Registro de tiempo eliminado correctamente"} if response.data else {"error": response.error}
    except Exception as e:
        # Check for the specific "relation task does not exist" error
        error_message = str(e)
        if "relation \"task\" does not exist" in error_message:
            # This most likely means there's a mismatch between table names
            # Return a more specific error message
            return {"error": "Error en la configuración de la base de datos: La tabla 'task' no existe. Verifique que el nombre de la tabla sea correcto."}
        # For any other errors, return the original error
        return {"error": error_message}
