from typing import Optional
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from ..database.data import supabase
from jose import JWTError, jwt
from passlib.context import CryptContext


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "_pEE_GC1P2Z-HWU0aSqmABrXyGgr5Mm1Q5JmhP1tOq4")
ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")



def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verifica el JWT y extrae el usuario."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("sub")
        id = int(id)
        if id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        response = supabase.table("users").select("id, username, role, email").eq("id", id).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return response.data[0]

    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

def hash_password(password: str) -> str:
    """
    Return the password without hashing.
    """
    return password


def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifies if a plain password matches the stored password.
    """
    return plain_password == stored_password

def create_access_token(data: dict) -> str:
    """Genera un JWT sin tiempo de expiración."""
    to_encode = data.copy()

    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Verifica y decodifica el JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
       
        return payload
    except JWTError as e:
        
        return None
    


def payload(token: str):
    """ Decodifica el token y obtiene el usuario autenticado """
    user_data = get_current_user(token)  
    if not user_data:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user_data

    

def role_required(allowed_roles: list):
    """ Dependency to restrict roles """

    def check_role(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para acceder a este recurso"
            )
        return user  
    
    return check_role


def get_user_by_email(email: str):
    """ Get user by email """
    response = supabase.table("users").select("id, username, role, email").eq("email", email).execute()
    if not response.data or len(response.data) == 0:
        return None
    return response.data[0]