from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.models.user_crud_model import delete_user, get_all, update_user, user_create
from app.services.utils import payload
from app.schemas.schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/user_crud", tags=["CRUD DE USUARIOS"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.post('/create')
def create_user(data: UserCreate, token: str = Depends(oauth2_scheme)):
    """ Create a user and save it in database"""
    print(f"[CREATE] Received data: {data}")
    user_data = payload(token)
    print(f"[CREATE] Decoded user from token: {user_data}")

    if not user_data or "id" not in user_data:
        print("[CREATE] User not authenticated or missing id in token payload.")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    response = user_create(data)
    print(f"[CREATE] Response from user_create: {response}")

    if not response:
        print("[CREATE] Cannot create user, response is empty or None.")
        raise HTTPException(status_code=500, detail='cannot create user')

    return 'creado exitosamente'


@router.get('/get_all')
def get_all_users_with_desvinculated(token: str = Depends(oauth2_scheme)):
    """ Get all users with desvinculated """
    user_data = payload(token)
    print(f"[GET_ALL] Decoded user from token: {user_data}")

    if not user_data:
        print("[GET_ALL] User not authenticated.")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    response = get_all()
    print(f"[GET_ALL] Response from get_all: {response}")

    if not response:
        print("[GET_ALL] Cannot get users, response is empty or None.")
        raise HTTPException(status_code=500, detail='cannot get users')

    return response


@router.put('/update')
def user_update(data: UserUpdate, token: str = Depends(oauth2_scheme)):
    """ Update a user and save it in database """
    print(f"[UPDATE] Received update request with data: {data}")
    user_data = payload(token)
    print(f"[UPDATE] Decoded user from token: {user_data}")

    if not user_data or "id" not in user_data:
        print("[UPDATE] User not authenticated or missing id in token payload.")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    try:
        response = update_user(data)
        print(f"[UPDATE] Response from update_user: {response}")
    except Exception as e:
        print(f"[UPDATE] Exception during user update: {e}")
        raise

    if not response:
        print("[UPDATE] Cannot update user, response is empty or None.")
        raise HTTPException(status_code=500, detail='cannot update user')

    return 'actualizado exitosamente'


@router.delete('/delete')
def user_delete(user_id: int, token: str = Depends(oauth2_scheme)):
    """ Delete a user and save it in database """
    print(f"[DELETE] Received delete request for user_id: {user_id}")
    user_data = payload(token)
    print(f"[DELETE] Decoded user from token: {user_data}")

    if not user_data or "id" not in user_data:
        print("[DELETE] User not authenticated or missing id in token payload.")
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    response = delete_user(user_id)
    print(f"[DELETE] Response from delete_user: {response}")

    if not response:
        print("[DELETE] Cannot delete user, response is empty or None.")
        raise HTTPException(status_code=500, detail='cannot delete user')

    return 'eliminado exitosamente'
