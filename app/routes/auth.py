from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.ModelUser import create_user, get_all_user_with_desvinculated, get_all_users, get_user, ROLE_CODES
from app.services.utils import create_access_token, get_current_user, verify_password
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["usuarios"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

class UserCreate(BaseModel):
    username: str
    password: str
    role_code: str  

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a user with a role based in a code"""

    role = ROLE_CODES.get(user_data.role_code)
    if not role:
        raise HTTPException(status_code=400, detail="Código de rol inválido.")

    user = create_user(user_data.username, user_data.password, role)
    if not user:
        raise HTTPException(status_code=400, detail="No se pudo crear el usuario")

    return {"message": "Usuario creado exitosamente", "role": role}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Verify credentials and returns the acces token"""

    


    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    
    access_token = create_access_token(
        data={"sub": user["id"], "role": user["role"]}
    )

    return {"access_token": access_token, "token_type": "bearer", "role": user["role"],"user_id": user['id'], "username": user['username']}

@router.get("/me", status_code=status.HTTP_200_OK)
async def read_current_user(user: dict = Depends(get_current_user)):
    """returns user info using the token"""
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.get("/get_all_users")
async def read_all_users(user: dict = Depends(get_current_user)):
    """Get all the users in the database
    """
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    response = get_all_users()

    return response


@router.get('/get_users_B')
def get_users_including_desvinculated(user: dict = Depends(get_current_user)):

    if not user:
        raise HTTPException(status_code= 404, detail= "usuario no encontrado")
    
    response = get_all_user_with_desvinculated()

    return response
