

from app.schemas.schemas import ContractCreate, ContractUpdate
from ..database.data import supabase
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(prefix="/contracts", tags=["contratos"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


@router.get("/client/{client_id}")
def get_contracts_by_client(client_id: int):
    response = supabase.table("contracts")\
        .select("*")\
        .eq("client_id", client_id)\
        .order("created_at", desc=True)\
        .execute()
    return response.data


@router.get('/contracts')
def get_contracts():
    response = supabase.table("contracts").select("*").execute()
    return response.data


@router.post("/create")
def create_contract(data: ContractCreate):
    response = supabase.table("contracts").insert({
        "client_id": data.client_id,
        "description": data.description,
        "total_value": data.total_value,
        "start_date": str(data.start_date),
        "end_date": str(data.end_date) if data.end_date else None
    }).execute()
    return response.data

# 🔹 ACTUALIZAR CONTRATO EXISTENTE
@router.put("/update/{contract_id}")
def update_contract(contract_id: int, data: ContractUpdate):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    if "end_date" in update_data:
        update_data["end_date"] = str(update_data["end_date"])
    if "start_date" in update_data:
        update_data["start_date"] = str(update_data["start_date"])

    response = supabase.table("contracts").update(update_data).eq("id", contract_id).execute()
    return response.data

# 🔹 ELIMINAR CONTRATO
@router.delete("/delete/{contract_id}")
def delete_contract(contract_id: int):
    response = supabase.table("contracts").delete().eq("id", contract_id).execute()
    return {"message": "Contrato eliminado"}
