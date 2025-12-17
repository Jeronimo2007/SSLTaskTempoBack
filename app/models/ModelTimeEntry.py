from app.database.data import supabase
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from app.schemas.schemas import TimeEntryCreate, TimeEntryCreateByTime, TimeEntryUpdate, getEntries, TimeEntryCreateShared
from typing import List

def calculate_duration(start_time: datetime, end_time: datetime) -> float:
    """ return the duration in hours """

    return (end_time - start_time).total_seconds() / 3600



def create_time_entry_by_time(data:TimeEntryCreateByTime):
    """create a time entry by time, ensuring Bogotá time zone"""

    bogota_tz = ZoneInfo("America/Bogota")
    
    # Ensure start_time is in Bogotá timezone
    if data.start_time.tzinfo is None:
        # Assume naive datetimes are in Bogotá time
        start_time = data.start_time.replace(tzinfo=bogota_tz)
    else:
        # Convert to Bogotá time if not already
        start_time = data.start_time.astimezone(bogota_tz)
    
    end_time = start_time + timedelta(hours=data.duration)

    response = supabase.table("time_entries").insert({
        "task_id": data.task_id,
        "user_id": data.user_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "description": data.description
    }).execute()

    if response.data: return response.data[0]
    else: return {"error": "Error creating time entry"}


def create_time_entry(user_id: int, entry_data: TimeEntryCreate):
    """ create a new time entry in supabase, ensuring Bogotá time zone """

    bogota_tz = ZoneInfo("America/Bogota")

    # Ensure both datetimes are timezone-aware and in Bogotá time
    if entry_data.start_time.tzinfo is None:
        # Assume naive datetimes are in Bogotá time
        entry_data.start_time = entry_data.start_time.replace(tzinfo=bogota_tz)
    else:
        # Convert to Bogotá time if not already
        entry_data.start_time = entry_data.start_time.astimezone(bogota_tz)

    if entry_data.end_time.tzinfo is None:
        entry_data.end_time = entry_data.end_time.replace(tzinfo=bogota_tz)
    else:
        entry_data.end_time = entry_data.end_time.astimezone(bogota_tz)

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
        return {"error": "Error getting time entry"}
    

def get_all_time_entries(data: getEntries):

    """ get all the time entries between start_date and end_date """

    response = supabase.table("time_entries").select("*").gte("start_time", data.start_date.isoformat()).lte("end_time", data.end_date.isoformat()).execute()

    return response.data if response.data else []


def get_time_entry(entry_id: int):

    """ get a time entry by the id"""
    
    response = supabase.table("time_entries").select("*").eq("id", entry_id).execute()

    return response.data[0] if response.data else None

def update_time_entry(entry_data: TimeEntryUpdate):
    print("update_time_entry function called")
    """
    Update a time entry.
    Supports updating start_time, end_time, and description fields.
    Only fields provided in entry_data will be updated.
    Automatically recalculates duration when start_time or end_time are updated.
    """

    print("Raw entry_data:", entry_data)
    print("entry_data dict:", entry_data.dict())
    
    # First, check if the time entry exists and get current values if needed
    try:
        check_response = supabase.table("time_entries").select("*").eq("id", entry_data.id).execute()
        if not check_response.data:
            return {"error": f"Time entry with id {entry_data.id} not found"}
        current_entry = check_response.data[0]
    except Exception as e:
        print(f"Error checking if time entry exists: {e}")
        return {"error": f"Error checking time entry existence: {str(e)}"}
    
    # Build update_data dict only with fields that are set
    update_data = entry_data.dict(exclude_unset=True)
    print("update_data to be sent to DB:", update_data)
    
    # Remove the id field as it's used for the WHERE clause, not for updating
    if 'id' in update_data:
        del update_data['id']
    
    # If no fields to update, return error
    if not update_data:
        return {"error": "No fields provided for update"}
    
    # Handle timezone conversion for datetime fields if they exist
    bogota_tz = ZoneInfo("America/Bogota")
    
    # Track if we need to recalculate duration
    needs_duration_recalc = False
    final_start_time = None
    final_end_time = None
    
    if 'start_time' in update_data and update_data['start_time']:
        try:
            if update_data['start_time'].tzinfo is None:
                final_start_time = update_data['start_time'].replace(tzinfo=bogota_tz)
            else:
                final_start_time = update_data['start_time'].astimezone(bogota_tz)
            update_data['start_time'] = final_start_time.isoformat()
            needs_duration_recalc = True
        except Exception as e:
            print(f"Error processing start_time: {e}")
            return {"error": f"Invalid start_time format: {str(e)}"}
    else:
        # Use current start_time if not being updated
        if current_entry.get('start_time'):
            final_start_time = datetime.fromisoformat(current_entry['start_time'].replace('Z', '+00:00'))
            if final_start_time.tzinfo is None:
                final_start_time = final_start_time.replace(tzinfo=bogota_tz)
            else:
                final_start_time = final_start_time.astimezone(bogota_tz)
    
    if 'end_time' in update_data and update_data['end_time']:
        try:
            if update_data['end_time'].tzinfo is None:
                final_end_time = update_data['end_time'].replace(tzinfo=bogota_tz)
            else:
                final_end_time = update_data['end_time'].astimezone(bogota_tz)
            update_data['end_time'] = final_end_time.isoformat()
            needs_duration_recalc = True
        except Exception as e:
            print(f"Error processing end_time: {e}")
            return {"error": f"Invalid end_time format: {str(e)}"}
    else:
        # Use current end_time if not being updated
        if current_entry.get('end_time'):
            final_end_time = datetime.fromisoformat(current_entry['end_time'].replace('Z', '+00:00'))
            if final_end_time.tzinfo is None:
                final_end_time = final_end_time.replace(tzinfo=bogota_tz)
            else:
                final_end_time = final_end_time.astimezone(bogota_tz)
    
    # If either start_time or end_time is being updated, recalculate duration
    if needs_duration_recalc and final_start_time and final_end_time:
        # Validate the relationship
        if final_start_time >= final_end_time:
            return {"error": "La hora de inicio debe ser menor a la hora de finalización."}
        
        # Calculate and update duration
        duration = calculate_duration(final_start_time, final_end_time)
        update_data['duration'] = duration
        print(f"Recalculated duration: {duration} hours")
    
    print("Final update_data to be sent to DB:", update_data)
    
    try:
        response = supabase.table("time_entries").update(update_data).eq("id", entry_data.id).execute()
        print("Supabase response:", response)
        print("Response data:", response.data)
        
        if response.data:
            return response.data[0]
        else:
            return {"error": "Error updating time entry: No data returned from update"}
            
    except Exception as e:
        print(f"Exception during update: {e}")
        return {"error": f"Error updating time entry: {str(e)}"}

def delete_time_entry(entry_id: int):

    """ Delete a time Entry """
    
    try:
        response = supabase.table("time_entries").delete().eq("id", entry_id).execute()
        return {"message": "Registro de tiempo eliminado correctamente"} if response.data else {"error": "Error deleting time entry"}
    except Exception as e:
        # Check for the specific "relation task does not exist" error
        error_message = str(e)
        if "relation \"task\" does not exist" in error_message:
            # This most likely means there's a mismatch between table names
            # Return a more specific error message
            return {"error": "Error en la configuración de la base de datos: La tabla 'task' no existe. Verifique que el nombre de la tabla sea correcto."}
        # For any other errors, return the original error
        return {"error": error_message}





def shared_time_entry(user_id: int,entry_data: TimeEntryCreateShared):


    """ shared a time entry between multiple users """

    try:


        bogota_tz = ZoneInfo("America/Bogota")

        # Ensure both datetimes are timezone-aware and in Bogotá time
        if entry_data.start_time.tzinfo is None:
            # Assume naive datetimes are in Bogotá time
            entry_data.start_time = entry_data.start_time.replace(tzinfo=bogota_tz)
        else:
            # Convert to Bogotá time if not already
            entry_data.start_time = entry_data.start_time.astimezone(bogota_tz)

        if entry_data.end_time.tzinfo is None:
            entry_data.end_time = entry_data.end_time.replace(tzinfo=bogota_tz)
        else:
            entry_data.end_time = entry_data.end_time.astimezone(bogota_tz)

        if entry_data.start_time >= entry_data.end_time:
            return {"error": "La hora de inicio debe ser menor a la hora de finalización."}

        duration = calculate_duration(entry_data.start_time, entry_data.end_time)


       

        created_entries = []
        for i in entry_data.ids:
            response = supabase.table("time_entries").insert({
                "task_id": entry_data.task_id,
                "user_id": i,
                "duration": duration,
                "start_time": entry_data.start_time.isoformat(),
                "end_time": entry_data.end_time.isoformat(),
                "description": entry_data.description
            }).execute()

            if response.data:
                created_entries.append(response.data[0])
            else:
                return {"error": "Error creating shared time entry"}

        return {"message": "Registros de tiempo creados correctamente", "entries": created_entries}
        
    except Exception as e:
        return {"error": f"Error creating shared time entry: {str(e)}"}
