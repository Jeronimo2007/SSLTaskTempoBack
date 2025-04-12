from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import requests
from urllib.parse import urlencode
import os
from dotenv import load_dotenv
from app.services.utils import create_access_token,get_user_by_email  
from app.database.data import supabase


load_dotenv()

router = APIRouter(prefix="/auth", tags=["Google Auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email"

@router.get("/google")
async def google_auth():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/callback/google")
async def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    r = requests.post(token_url, data=data)
    if not r.ok:
        raise HTTPException(status_code=400, detail="Error al obtener el token de Google")

    tokens = r.json()
    google_access_token = tokens["access_token"]

    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"}
    )
    if not userinfo.ok:
        raise HTTPException(status_code=400, detail="Error al obtener la información del usuario")

    user_data = userinfo.json()
    email = user_data["email"]

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Este usuario no está autorizado a iniciar sesión.")

    
    supabase.table("users").update({"google_access_token": google_access_token}).eq("id", user["id"]).execute()

   
    jwt_token = create_access_token(data={"sub": user["id"], "role": user["role"]})

    redirect_url = (
        f"http://localhost:3000/lawspace"
        f"?access_token={jwt_token}"
        f"&user_id={user['id']}"
        f"&username={user['username']}"
        f"&email={user['email']}"
    )

    return RedirectResponse(url=redirect_url)
    