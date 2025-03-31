from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.database.data import supabase
from app.models.ModelClients import create_client, get_relation_client_user, read_client_user, read_clients, remove_client, update_client
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
    

    response = create_client(client_data)

    if not response:
        raise HTTPException(status_code=500, detail='cannot create client')
    

    return 'creado exitosamente'


@router.get('/get_client_user')
async def get_client_user(token: str = Depends(oauth2_scheme)):
    
    """ Get the users that are assigned to a client """

    user_data = payload(token)


    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    

    response = read_client_user()

    return response



@router.get('/get_clients_admin')
async def get_clients_admin( token: str = Depends(oauth2_scheme)):

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


    response = update_client(update_data)


    return response



@router.delete('/delete_client')
async def delete_client(delete_data: clientDelete, user: dict = Depends(role_required(['socio', 'senior'])), token: str = Depends(oauth2_scheme)):
    
    """ delete a client with their assigments """

    user_data = payload(token)


    if not user_data:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    

    response = remove_client(delete_data.id)


    return response

@router.get("/get_relation")
async def get_relation(user_id: int):
    """Get the relation between clients and users"""


    response = get_relation_client_user(user_id)

    return response




@router.get("/summary")
def get_client_summary():
    """Get the summary of the clients"""
    try:
        # Realiza la consulta a la tabla "client_monthly_summary"
        response = supabase.table("client_monthly_summary").select("*").execute()

        # Verifica si hay un error en la respuesta
        if not response or "error" in response:
            error_message = response.get("error", {}).get("message", "Error desconocido")
            raise HTTPException(status_code=500, detail=f"Error al obtener el resumen de clientes: {error_message}")

        # Verifica si los datos están vacíos
        if not response.data:
            raise HTTPException(status_code=404, detail="No se encontraron datos en el resumen de clientes")

        # Devuelve los datos si todo está correcto
        return response.data

    except HTTPException as e:
        # Re-lanza excepciones HTTP conocidas
        raise e
    except Exception as e:
        # Manejo genérico de errores
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.get("/get_clients_name")
def get_clients_name():
    """Get the name of the clients"""
    response = supabase.table("clients").select('id',"name").execute()
    return response.data



