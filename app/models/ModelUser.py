from ..database.data import supabase  
from app.services.utils import hash_password


ROLE_CODES = {
    "214389": "socio",
    "132867": "senior",
    "929491": "consultor",
    "224566": "junior",
    "100435": "auxiliar"
}


def create_user(username: str, password: str, role_code: str):
    """ Creates an user with a role """

    
    response = supabase.table("users").insert({
        "username": username,
        "password": password if password else "default_password",
        "role": role_code
    }).execute()

    print("Response:", response)
    
    if response.data:
        return {"message": "Usuario creado exitosamente", "user": response.data}
    else:
        return {"error": "Error al crear el usuario", "details": "Unknown error"}

def get_user(email: str):
    """ Get all the data of a user by email, excluding those marked as 'desvinculado' """
    response = supabase.table("users").select("id,username,password,role,desvinculado,email").eq("email", email).neq("desvinculado", True).execute()
    if response.data:
        return response.data[0]
    else:
        return None


def get_all_users():
    """ Get all the users in the database, excluding those marked as 'desvinculado' """
    response = supabase.table("users").select("*").neq("desvinculado", True).execute()
    if response.data:
        return response.data
    else:
        return None

def get_all_user_with_desvinculated():
    """Get all users for the client sections including the desvicunlated"""
    response = supabase.table("users").select('*').execute()

    users = response.data
    for user in users:
        if user.get("desvinculado"):
            user["username"] += " (Desvinculado)"

            
    return users