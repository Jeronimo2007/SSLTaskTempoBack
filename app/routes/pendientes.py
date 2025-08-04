
from fastapi import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo

from app.schemas.schemas import PendienteCreate, PendienteUpdate
from app.database.data import supabase

router = APIRouter(prefix="/pendiente", tags=["pendientes"])



@router.post('/create_pendiente')
async def create_pendiente(data: PendienteCreate):

    """ Create a pendiente and save it in database"""
    
    # Convert the data to a dict and handle datetime serialization
    pendiente_data = data.model_dump()
    
    # Handle datetime serialization for due_date
    if pendiente_data.get('due_date'):
        due_date = pendiente_data['due_date']
        if isinstance(due_date, datetime):
            # Ensure timezone awareness (Bogotá timezone)
            bogota_tz = ZoneInfo("America/Bogota")
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=bogota_tz)
            else:
                due_date = due_date.astimezone(bogota_tz)
            pendiente_data['due_date'] = due_date.isoformat()
    
    response = supabase.table("pendientes").insert(pendiente_data).execute()
    if not response.data:
        raise Exception(f"Error creating pendiente: {response}")
        return []
    
    return response.data
    


@router.get('/get_pendientes')
async def get_pendientes():

    """ Get all pendientes """
    
    response = supabase.table("pendientes").select("*").execute()
    
    if not response.data:
        return []
    
    
    return response.data



@router.put('/update_pendiente')
async def update_pendiente(data: PendienteUpdate):

    """ Update a pendiente """
    
    # Convert the data to a dict and handle datetime serialization
    pendiente_data = data.model_dump(exclude_unset=True)
    
    # Handle datetime serialization for due_date
    if pendiente_data.get('due_date'):
        due_date = pendiente_data['due_date']
        if isinstance(due_date, datetime):
            # Ensure timezone awareness (Bogotá timezone)
            bogota_tz = ZoneInfo("America/Bogota")
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=bogota_tz)
            else:
                due_date = due_date.astimezone(bogota_tz)
            pendiente_data['due_date'] = due_date.isoformat()
    
    response = supabase.table("pendientes").update(pendiente_data).eq("id", data.id).execute()
    
    if not response.data:
        raise Exception(f"Error updating pendiente: {response}")
    
    return response.data


@router.delete('/delete_pendiente/{id}')
async def delete_pendiente(id: int):
    """ Delete a pendiente """
    
    response = supabase.table("pendientes").delete().eq("id", id).execute()
    
    if not response.data:
        raise Exception(f"Error deleting pendiente: {response}")
    
    return {"message": "Pendiente deleted successfully"}
