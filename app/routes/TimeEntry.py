from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.models.ModelTimeEntry import create_time_entry, create_time_entry_by_time, delete_time_entry, get_all_time_entries, get_time_entry, update_time_entry, shared_time_entry
from app.schemas.schemas import TimeEntryCreate, TimeEntryCreateByTime, TimeEntryResponse, TimeEntryUpdate, getEntries, FacturadoUpdate, TimeEntryCreateShared
from app.services.utils import get_current_user
from app.database.data import supabase


router = APIRouter(prefix="/timeEntry", tags=["Time Entries"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")



@router.post("/create_by_time")
async def create_timeEntry_by_time(req: TimeEntryCreateByTime):
    """ create a time entry by time """

    entry = create_time_entry_by_time(req)

    if "error" in entry:

        raise HTTPException(status_code=400, detail=entry["error"])
    
    return entry


@router.post("/create")
async def create_time_entry_endpoint(entry_data: TimeEntryCreate, user: dict = Depends(get_current_user)):
    

    """ register the time in a task """

    entry = create_time_entry(user["id"], entry_data)
   

    if "error" in entry:

        raise HTTPException(status_code=400, detail=entry["error"])
    
    return entry


@router.post("/create_shared")
async def create_time_entry_shared_endpoint(entry_data: TimeEntryCreateShared, user: dict = Depends(get_current_user)):
    """ create a shared time entry """

    entry = shared_time_entry(user["id"], entry_data)
   
    if "error" in entry:

        raise HTTPException(status_code=400, detail=entry["error"])
    
    return entry

@router.post("/get_all_time_entries")
async def get_time_entries_endpoint(data: getEntries):

    """ get all time entries"""

    return get_all_time_entries(data)


@router.get("/get_time_entry/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry_endpoint(entry_id: int):

    """ get a time entrie by the id """

    entry = get_time_entry(entry_id)

    if not entry:

        raise HTTPException(status_code=404, detail="Registro de tiempo no encontrado")
    
    return entry


@router.put("/update")
async def update_time_entry_endpoint(entry_data: TimeEntryUpdate):
    print("=== UPDATE TIME ENTRY ENDPOINT ===")
    print("entry_data:", entry_data)
    print("entry_data type:", type(entry_data))
    print("entry_data dict:", entry_data.dict())

    """ update a time entry"""

    try:
        entry = update_time_entry(entry_data)
        print("Result from update_time_entry:", entry)
        
        if "error" in entry:
            print("Error found in result:", entry["error"])
            raise HTTPException(status_code=400, detail=entry["error"])
        
        return entry
        
    except Exception as e:
        print(f"Exception in endpoint: {e}")
        print(f"Exception type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/delete/{entry_id}")
async def delete_time_entry_endpoint(entry_id: int):

    """ delete a time entry """

    result = delete_time_entry(entry_id)

    if "error" in result:

        raise HTTPException(status_code=400, detail=result["error"])
    
    return result



@router.put('/update/update_facturado')
async def update_facturado(data: FacturadoUpdate):
    
    """update the time entry facturado column"""
    
    # Validate facturado value
    valid_values = ["si", "no", "parcialmente"]
    if data.facturado not in valid_values:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid facturado value. Must be one of: {', '.join(valid_values)}"
        )

    # Check if time entry exists
    check_response = supabase.table("time_entries").select("id").eq("id", data.timeEntry_id).execute()
    if not check_response.data:
        raise HTTPException(status_code=404, detail="Time entry not found")

    result = supabase.table("time_entries").update({"facturado": data.facturado}).eq("id", data.timeEntry_id).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to update time entry")
    
    return {"message": "Time entry updated successfully", "data": result.data[0]}


