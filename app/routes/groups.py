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
async def get_all_groups(user_id: int):
    try:
        # 1. Get all client_ids for this user
        client_user_resp = supabase.table("client_user").select("client_id").eq("user_id", user_id).execute()
        if not client_user_resp.data:
            return []
        client_ids = [item["client_id"] for item in client_user_resp.data]

        # 2. Get all task_ids for these clients
        tasks_resp = supabase.table("tasks").select("id").in_("client_id", client_ids).execute()
        if not tasks_resp.data:
            return []
        task_ids = [item["id"] for item in tasks_resp.data]

        # 3. Get all groups for these tasks
        groups_resp = supabase.table("groups").select("*").in_("task_id", task_ids).execute()
        return groups_resp.data
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