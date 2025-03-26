

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.models.ModelTimeEntry import create_time_entry, delete_time_entry, get_all_time_entries, get_time_entry, update_time_entry
from app.schemas.schemas import TimeEntryCreate, TimeEntryResponse, TimeEntryUpdate, getEntries
from app.services.utils import get_current_user


router = APIRouter(prefix="/timeEntry", tags=["Time Entries"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.post("/create", response_model=TimeEntryResponse)
async def create_time_entry_endpoint(entry_data: TimeEntryCreate, user: dict = Depends(get_current_user)):

    """ register the time in a task """

    entry = create_time_entry(user["id"], entry_data)

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


@router.put("/update/{entry_id}", response_model=TimeEntryResponse)
async def update_time_entry_endpoint(entry_id: int, entry_data: TimeEntryUpdate):

    """ update a time entry"""

    entry = update_time_entry(entry_id, entry_data)

    if "error" in entry:

        raise HTTPException(status_code=400, detail=entry["error"])
    
    return entry


@router.delete("/delete/{entry_id}")
async def delete_time_entry_endpoint(entry_id: int):

    """ delete a time entry """

    result = delete_time_entry(entry_id)

    if "error" in result:

        raise HTTPException(status_code=400, detail=result["error"])
    
    return result