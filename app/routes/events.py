from fastapi import APIRouter, HTTPException, Depends
from datetime import date

from fastapi.security import OAuth2PasswordBearer
from app.database.data import supabase
from app.schemas.schemas import EventCreate, EventUpdate
from app.services.utils import payload  # Asegúrate de importar la función payload

router = APIRouter(prefix='/events', tags=['events'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Crear evento
@router.post("/create")
def create_event(event: EventCreate, token: str = Depends(oauth2_scheme)):
    try:
        print("🔹 Endpoint /create llamado")  # Depuración
        user_data = payload(token)
        print("🔹 Datos del usuario autenticado:", user_data)  # Depuración
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        # Convertir event_date a formato ISO
        event_data = event.dict()
        if isinstance(event_data.get("event_date"), date):
            event_data["event_date"] = event_data["event_date"].isoformat()

        # Intentar insertar el evento
        print("🔹 Datos enviados a Supabase:", event_data)  # Depuración
        resp = supabase.table("events").insert(event_data).execute()
        print("🔹 Respuesta de Supabase:", resp)  # Depuración

        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo crear el evento")

        return {"message": "Evento creado", "data": resp.data}
    except Exception as e:
        print("🔴 Error al crear evento:", str(e))  # Depuración
        raise HTTPException(status_code=500, detail=f"Error al crear evento: {str(e)}")


# Obtener todos los eventos (opcionalmente por usuario)
@router.get("/get_all_events")
def get_all_events(user_id: int = None, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        resp = supabase.table("events").select("*").execute()
        eventos = resp.data or []

        if user_id is not None:
            eventos = [e for e in eventos if user_id in e["user_ids"]]

        return eventos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")


# Obtener un solo evento por ID
@router.get("/events/{event_id}")
def get_event(event_id: int, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        resp = supabase.table("events").select("*").eq("id", event_id).single().execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        return resp.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener evento: {str(e)}")


# Actualizar evento
@router.put("/update/{event_id}")
def update_event(event_id: int, event: EventUpdate, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        # Convertir event_date a formato ISO si está presente
        event_data = event.dict()
        if isinstance(event_data.get("event_date"), date):
            event_data["event_date"] = event_data["event_date"].isoformat()

        resp = supabase.table("events").update(event_data).eq("id", event_id).execute()
        print("🔹 Respuesta de Supabase:", resp)  # Depuración

        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo actualizar el evento")

        return {"message": "Evento actualizado", "data": resp.data}
    except Exception as e:
        print("🔴 Error al actualizar evento:", str(e))  # Depuración
        raise HTTPException(status_code=500, detail=f"Error al actualizar evento: {str(e)}")


# Eliminar evento
@router.delete("/delete/{event_id}")
def delete_event(event_id: int, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        resp = supabase.table("events").delete().eq("id", event_id).execute()
        print("🔹 Respuesta de Supabase:", resp)  # Depuración

        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo eliminar el evento")

        return {"message": "Evento eliminado"}
    except Exception as e:
        print("🔴 Error al eliminar evento:", str(e))  # Depuración
        raise HTTPException(status_code=500, detail=f"Error al eliminar evento: {str(e)}")
