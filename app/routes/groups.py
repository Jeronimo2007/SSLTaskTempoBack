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
        create_group = supabase.table("groups").insert({
            "group_name": request.group_name,
            "monthly_limit_hours": request.monthly_limit_hours,
        }).execute()

        if not create_group.data:
            raise HTTPException(status_code=400, detail="Failed to create group")
        group_id = create_group.data[0]['id']

        data = [{
            "group_id": group_id,
            "task_id": id_task,
            "client_id": request.client_id,
        } for id_task in request.tasks]

        response = supabase.table("groups_tasks").insert(data).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to associate tasks with group")
        return {"message": "Group created successfully", "group_id": group_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@router.get("/get_all_groups")
async def get_all_groups():
    try:
        
        groups_response = supabase.table("groups").select("id, group_name").execute()
        if not groups_response.data:
            return []
        groups = groups_response.data

       
        group_tasks_response = supabase.table("groups_tasks").select("group_id, task_id").execute()
        if not group_tasks_response.data:
            group_tasks = []
        else:
            group_tasks = group_tasks_response.data

        
        tasks_response = supabase.table("tasks").select("id, title").execute()
        if not tasks_response.data:
            tasks = []
        else:
            tasks = tasks_response.data
        task_id_to_title = {task["id"]: task["title"] for task in tasks}

        
        from collections import defaultdict
        group_id_to_task_ids = defaultdict(list)
        for gt in group_tasks:
            group_id_to_task_ids[gt["group_id"]].append(gt["task_id"])

        
        result = []
        for group in groups:
            group_id = group["id"]
            task_titles = [task_id_to_title.get(task_id, "") for task_id in group_id_to_task_ids.get(group_id, [])]
            result.append({
                "group_name": group["group_name"],
                "tasks": task_titles
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_groups")
async def get_all_groups(user_id: int):
    try:
        
        client_user_response = supabase.table('client_user').select('client_id').eq('user_id', user_id).execute()
        if not client_user_response.data:
            return []
        client_ids = [item['client_id'] for item in client_user_response.data]

        
        tasks_response = supabase.table('tasks').select('id, title, client_id').in_('client_id', client_ids).execute()
        if not tasks_response.data:
            return []
        tasks = tasks_response.data
        task_id_to_title = {task['id']: task['title'] for task in tasks}
        valid_task_ids = set(task['id'] for task in tasks)

       
        group_tasks_response = supabase.table('groups_tasks').select('group_id, task_id').execute()
        if not group_tasks_response.data:
            return []
        group_tasks = group_tasks_response.data

        
        from collections import defaultdict
        group_id_to_task_ids = defaultdict(list)
        for gt in group_tasks:
            if gt['task_id'] in valid_task_ids:
                group_id_to_task_ids[gt['group_id']].append(gt['task_id'])

        # Get all groups
        groups_response = supabase.table('groups').select('id, group_name').execute()
        if not groups_response.data:
            return []
        groups = groups_response.data

        
        result = []
        for group in groups:
            group_id = group['id']
            task_titles = [task_id_to_title.get(task_id, "") for task_id in group_id_to_task_ids.get(group_id, [])]
            if task_titles:  
                result.append({
                    "group_name": group["group_name"],
                    "tasks": task_titles
                })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update_group_{group_id}")
async def update_group(group_id: int, request: GroupUpdate):
    try:
        # Build update data only for non-null values
        update_data = {}
        if request.group_name is not None:
            update_data["group_name"] = request.group_name

        if request.monthly_limit_hours is not None:
            update_data["monthly_limit_hours"] = request.monthly_limit_hours

        


        # Update group if there are changes
        if update_data:
            update_group = supabase.table("groups").update(update_data).eq("id", group_id).execute()
            if not update_group.data:
                raise HTTPException(status_code=400, detail="Failed to update group")

        # Update tasks only if request.tasks is not None
        if request.tasks is not None:
            # Get the current client_id from existing group_tasks
            current_group_tasks = supabase.table("groups_tasks").select("client_id").eq("group_id", group_id).limit(1).execute()
            
            if not current_group_tasks.data:
                raise HTTPException(status_code=400, detail="No existing tasks found for this group")
            
            client_id = current_group_tasks.data[0]["client_id"]
            
            # Delete existing group-task associations
            supabase.table("groups_tasks").delete().eq("group_id", group_id).execute()

            # Create new group-task associations
            data = [{
                "group_id": group_id,
                "task_id": id_task,
                "client_id": client_id,
            } for id_task in request.tasks]

            response = supabase.table("groups_tasks").insert(data).execute()
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to associate tasks with group")

        return {"message": "Group updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_group_{group_id}")
async def delete_group(group_id: int):
    try:
        # Delete group-tasks associations
        delete_tasks_response = supabase.table("groups_tasks").delete().eq("group_id", group_id).execute()
        if not delete_tasks_response:
            raise HTTPException(status_code=400, detail="Failed to delete group tasks")

        # Delete the group itself
        delete_group_response = supabase.table("groups").delete().eq("id", group_id).execute()
        if not delete_group_response:
            raise HTTPException(status_code=400, detail="Failed to delete group")

        return {"message": "Group deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))