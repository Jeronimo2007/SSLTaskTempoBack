
from fastapi import APIRouter

from app.schemas.schemas import PendienteCreate, PendienteUpdate
from app.database.data import supabase

router = APIRouter(prefix="/pendiente", tags=["pendientes"])



@router.post('/create_pendiente')
async def create_pendiente(data: PendienteCreate):

    """ Create a pendiente and save it in database"""
    
    response = supabase.table("pendientes").insert(data.model_dump()).execute()
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
    
    response = supabase.table("pendientes").update(data.model_dump(exclude_unset=True)).eq("id", data.id).execute()
    
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
