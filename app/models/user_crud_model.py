from app.schemas.schemas import UserCreate, UserUpdate
from app.database.data import supabase
from fastapi import HTTPException




def user_create(data: UserCreate):
    """
    Create a user and save it in database
    """
    try:
        # Convert model to dict and ensure fields match the table
        user_data = data.dict()
        response = supabase.table('users').insert(user_data).execute()

        # Check if response contains an error
        if not response.data:
            raise HTTPException(status_code=400, detail="Supabase error: No data returned")

        # Verify if any record was actually inserted
        if hasattr(response, 'data') and response.data:
            return response.data  # Return the inserted data
        else:
            raise HTTPException(status_code=500, detail="No user was inserted in the database.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error creating user: {str(e)}')
    

def get_all():
    try:
        response = supabase.table('users').select('*').execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Supabase error: No data returned")

        if hasattr(response, 'data') and response.data:
            return response.data
        else:
            raise HTTPException(status_code=404, detail="No users found in the database.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Cannot get users: {str(e)}')
    

def update_user(data: UserUpdate):
    """
    Update a user and save it in database
    Only non-None fields will be updated.
    """
    try:
        # Filter out None values
        update_data = {k: v for k, v in data.dict().items() if v is not None and k != "id"}
        if not update_data:
            raise HTTPException(status_code=400, detail='No fields to update')

        response = supabase.table('users').update(update_data).eq('id', data.id).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Supabase error: No data returned")

        if hasattr(response, 'data') and response.data:
            return response.data
        else:
            raise HTTPException(status_code=404, detail="No user was updated in the database.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Cannot update user: {str(e)}')


def delete_user(user_id: int):
    """
    Delete a user and save it in database
    """
    try:
        response = supabase.table('users').delete().eq('id', user_id).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Supabase error: No data returned")

        if hasattr(response, 'data') and response.data:
            return response.data
        else:
            raise HTTPException(status_code=404, detail="No user was deleted from the database.")

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Cannot delete user: {str(e)}')
