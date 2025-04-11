from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import date
import requests
from app.schemas.schemas import EventCreate, EventUpdate 
from app.services.utils import payload, supabase  

router = APIRouter(prefix='/events', tags=['events'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def crear_evento_google_calendar(access_token: str, evento: dict, creator_email: str, attendee_emails: list):
    inicio = f"{evento['event_date']}T{evento.get('start_time', '09:00:00')}"
    fin = f"{evento['event_date']}T{evento.get('end_time', '10:00:00')}"

    # Build attendees list including all emails except the creator (Google adds creator automatically)
    attendees = [{"email": email} for email in attendee_emails if email != creator_email]

    evento_google = {
        "summary": evento.get("title", "Evento sin título"),
        "description": evento.get("description", ""),
        "start": {"dateTime": inicio, "timeZone": "America/Bogota"},
        "end": {"dateTime": fin, "timeZone": "America/Bogota"},
        "attendees": attendees,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        json=evento_google
    )

    if response.ok:
        event_info = response.json()
        print(f"✅ Evento creado en el calendario de {creator_email} con ID {event_info['id']}")
        return event_info["id"]
    else:
        print(f"🔴 Error al crear evento en Google Calendar de {creator_email}: {response.text}")
        return None


def actualizar_evento_google_calendar(access_token: str, event_id_google: str, evento: dict, creator_email: str, attendee_emails: list):
    inicio = f"{evento['event_date']}T{evento.get('start_time', '09:00:00')}"
    fin = f"{evento['event_date']}T{evento.get('end_time', '10:00:00')}"

    attendees = [{"email": email} for email in attendee_emails if email != creator_email]

    evento_google = {
        "summary": evento.get("title", "Evento sin título"),
        "description": evento.get("description", ""),
        "start": {"dateTime": inicio, "timeZone": "America/Bogota"},
        "end": {"dateTime": fin, "timeZone": "America/Bogota"},
        "attendees": attendees,
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.put(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id_google}",
        headers=headers,
        json=evento_google
    )

    if not response.ok:
        print(f"🔴 Error al actualizar evento en Google Calendar de {creator_email}: {response.text}")
    else:
        print(f"✅ Evento actualizado en el calendario de {creator_email}")


def eliminar_evento_google_calendar(access_token: str, event_id_google: str, email: str):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.delete(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id_google}",
        headers=headers
    )

    if not response.ok:
        print(f"🔴 Error al eliminar evento de Google Calendar de {email}: {response.text}")
    else:
        print(f"✅ Evento eliminado del calendario de {email}")


@router.post("/create")
def create_event(event: EventCreate, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        event_data = event.dict()
        if isinstance(event_data.get("event_date"), date):
            event_data["event_date"] = event_data["event_date"].isoformat()


        if "start_time" in event_data and hasattr(event_data["start_time"], "isoformat"):
            event_data["start_time"] = event_data["start_time"].isoformat()
        if "end_time" in event_data and hasattr(event_data["end_time"], "isoformat"):
            event_data["end_time"] = event_data["end_time"].isoformat()


        

        event_data["creator_id"] = user_data["id"]

        resp = supabase.table("events").insert(event_data).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo crear el evento")

        evento_creado = resp.data[0]
        user_ids = evento_creado.get("user_ids", [])

        attendee_emails = []
        creator_email = None
        creator_access_token = None

        for uid in user_ids:
            user_resp = supabase.table("users").select("email, google_access_token").eq("id", uid).single().execute()
            user = user_resp.data

            if user and user.get("email"):
                attendee_emails.append(user["email"])

            # Identify creator's email and access token
            if uid == user_data["id"] and user.get("google_access_token"):
                creator_email = user["email"]
                creator_access_token = user["google_access_token"]

        # Create Google Calendar event only if creator has access token
        if creator_access_token:
            google_event_id = crear_evento_google_calendar(
                creator_access_token,
                evento_creado,
                creator_email,
                attendee_emails
            )
            if google_event_id:
                supabase.table("events").update({"google_event_id": google_event_id}).eq("id", evento_creado["id"]).execute()

        return {"message": "Evento creado", "data": evento_creado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear evento: {str(e)}")


@router.get("/get_all_events")
def get_all_events(user_id: int = None, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        resp = supabase.table("events").select("*").execute()
        eventos = resp.data or []

        if user_id is not None:
            eventos = [e for e in eventos if user_id in e.get("user_ids", [])]

        return eventos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener eventos: {str(e)}")


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


@router.put("/update/{event_id}")
def update_event(event_id: int, event: EventUpdate, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        event_data = event.dict()
        if isinstance(event_data.get("event_date"), date):
            event_data["event_date"] = event_data["event_date"].isoformat()

        if "start_time" in event_data and hasattr(event_data["start_time"], "isoformat"):
            event_data["start_time"] = event_data["start_time"].isoformat()
        if "end_time" in event_data and hasattr(event_data["end_time"], "isoformat"):
            event_data["end_time"] = event_data["end_time"].isoformat()

        resp_original = supabase.table("events").select("*").eq("id", event_id).single().execute()
        original_event = resp_original.data

        resp = supabase.table("events").update(event_data).eq("id", event_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo actualizar el evento")

        attendee_emails = []
        creator_email = None
        creator_access_token = None

        for uid in original_event.get("user_ids", []):
            user_resp = supabase.table("users").select("email, google_access_token").eq("id", uid).single().execute()
            user = user_resp.data

            if user and user.get("email"):
                attendee_emails.append(user["email"])

            if uid == user_data["id"] and user.get("google_access_token"):
                creator_email = user["email"]
                creator_access_token = user["google_access_token"]

        if creator_access_token and original_event.get("google_event_id"):
            actualizar_evento_google_calendar(
                creator_access_token,
                original_event["google_event_id"],
                event_data,
                creator_email,
                attendee_emails
            )

        return {"message": "Evento actualizado", "data": resp.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar evento: {str(e)}")


@router.delete("/delete/{event_id}")
def delete_event(event_id: int, token: str = Depends(oauth2_scheme)):
    try:
        user_data = payload(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        resp_event = supabase.table("events").select("*").eq("id", event_id).single().execute()
        evento = resp_event.data

        creator_access_token = None
        creator_email = None

        for uid in evento.get("user_ids", []):
            user_resp = supabase.table("users").select("email, google_access_token").eq("id", uid).single().execute()
            user = user_resp.data

            if uid == user_data["id"] and user.get("google_access_token"):
                creator_access_token = user["google_access_token"]
                creator_email = user["email"]

        if creator_access_token and evento.get("google_event_id"):
            eliminar_evento_google_calendar(creator_access_token, evento["google_event_id"], creator_email)

        resp = supabase.table("events").delete().eq("id", event_id).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail="No se pudo eliminar el evento")

        return {"message": "Evento eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar evento: {str(e)}")
