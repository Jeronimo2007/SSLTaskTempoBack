import os
from dotenv import load_dotenv
from supabase import create_client


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las credenciales de Supabase. Revisa tu archivo .env")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)