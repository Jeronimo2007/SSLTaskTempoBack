from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.database.data import supabase
from app.schemas.schemas import GroupCreate, GroupUpdate
from typing import List

router = APIRouter(prefix="/groups", tags=["groups"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

@router.post("/create_group")
async def create_group(request: GroupCreate):
    try:
        if not request.group_name or not request.area:
            raise HTTPException(status_code=400, detail="Missing required fields: group_name and area")

        creation = supabase.table("groups").insert(request.dict()).execute()
        
        if "error" in creation:
            raise HTTPException(status_code=400, detail=creation["error"])
            
        return creation.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_groups")
async def get_all_groups(task_id: int):
    try:

        if not task_id:
            raise HTTPException(status_code=400, detail="task_id is required")


        response = supabase.table("groups").select("*").eq("task_id",task_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_{group_id}")
async def get_group(group_id: int):
    try:
        response = supabase.table("groups").select("*").eq("id", group_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update_group_{group_id}")
async def update_group(group_id: int, request: GroupUpdate):
    try:
        if not request.dict(exclude_unset=True):
            raise HTTPException(status_code=400, detail="No update data provided")

        response = supabase.table("groups").update(request.dict(exclude_unset=True)).eq("id", group_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_group_{group_id}")
async def delete_group(group_id: int):
    try:
        response = supabase.table("groups").delete().eq("id", group_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        return {"message": "Group deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))