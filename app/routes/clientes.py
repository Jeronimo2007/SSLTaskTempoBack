from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.models.ModelClients import create_client, read_clients, remove_client, update_client
from app.schemas.schemas import clientCreate, clientDelete, clientUpdate
from app.services.utils import payload, role_required


router = APIRouter(prefix="/clients", tags=["clients"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")




@router.post('/create')
async def addClient(client_data: clientCreate, user: dict = Depends(role_required(['socio', 'senior'])), token: str = Depends(oauth2_scheme)):
    
    """ Create a client and save it in database"""
    
    user_data = payload(token)
        

    if not user_data or "id" not in user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    

    response = create_client(client_data.name,client_data.color)

    if not response:
        raise HTTPException(status_code=500, detail='cannot create client')
    

    return 'creado exitosamente'



@router.get('/get_clients_admin')
async def get_clients_admin(user: dict = Depends(role_required(['socio', 'senior'])), token: str = Depends(oauth2_scheme)):

    """ Get all the clients in the database """


    user_data = payload(token)


    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    response = read_clients()

    return response


@router.put('/update_client')
async def client_update(update_data: clientUpdate, user: dict = Depends(role_required(['socio', 'senior'])), token: str = Depends(oauth2_scheme)):


    """update the clients info"""


    user_data = payload(token)


    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")


    response = update_client(update_data.id ,update_data.name, update_data.color)


    return response



@router.delete('/delete_client')
async def delete_client(delete_data: clientDelete, user: dict = Depends(role_required(['socio', 'senior'])), token: str = Depends(oauth2_scheme)):
    
    """ delete a client with their assigments """

    user_data = payload(token)


    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    

    response = remove_client(delete_data.id)


    return response





