from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import date, datetime, time


class clientCreate(BaseModel):
    name: str
    permanent: bool
    lawyers: list[int]
    nit: str
    phone: str
    city: str
    address: str
    email: str
    international : bool
    type: Literal['natural','juridica'] = 'natural'  # Default to 'natural'


class clientUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    lawyers: Optional[list[int]] = None 
    permanent: Optional[bool] = None
    nit: str
    phone: str
    city: str
    address: str
    email: str
    international: Optional[bool] = None
    type: Optional[Literal['natural', 'juridica']] = None  # Default to 'natural' if not provided




class clientDelete(BaseModel):
    id: int



class TaskCreate(BaseModel):
    client_id: int
    title: str
    billing_type: str
    status: str
    area: Optional[str] = "Sin área"
    note: Optional[str] = None
    total_value: Optional[float] = Field(default=None, description="Requerido si billing_type es 'percentage'")
    due_date: Optional[datetime] = None
    permanent: bool = False
    monthly_limit_hours_tasks: int = 0
    facturado: str = 'no'
    asesoria_tarif: Optional[float] = None

class TaskUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    area: Optional[str] = None
    billing_type: Optional[str] = None
    note: Optional[str] = None
    total_value: Optional[float] = None
    monthly_limit_hours_tasks: Optional[int] = None
    facturado: Optional[Literal["si", "no", "parcialmente"]] = None
    asesoria_tarif: Optional[float] = None


class TaskResponse(BaseModel):
    id: int
    client_id: int
    title: str
    description: Optional[str]
    assigned_to_id: int
    status: str
    assignment_date: datetime
    due_date: Optional[datetime]
    total_time: float
    billing_type: Literal["hourly", "percentage"]
    note: Optional[str]
    total_value: Optional[float]
    area: Optional[str]

class TimeEntryCreateByTime(BaseModel):
    user_id: int
    task_id: int
    start_time: datetime
    description: str
    duration: float
    


class TimeEntryCreate(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime
    description: str
    


class TimeEntryUpdate(BaseModel):
    id: int
    description: Optional[str] = None

class FacturadoUpdate(BaseModel):
    timeEntry_id: int
    facturado: Literal["si", "no", "parcialmente"]


class TimeEntryResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    duration: float

class getEntries(BaseModel):
    start_date: datetime
    end_date: datetime


class ReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime



class ClientReportRequest(BaseModel):
    client_id: int
    start_date: datetime
    end_date: datetime


class ClientReportRequestTimeEntries(BaseModel):
    start_date: datetime
    end_date: datetime



class TaskReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    task_id: int

class GroupReportRequest(BaseModel):
    value_per_set_hours: float
    start_date: datetime
    end_date: datetime
    task_id: int

class InvoiceByHoursRequest(BaseModel):
    client_id: int
    task_id: int
    currency: str  # 'COP' o 'USD'
    exchange_rate: float | None = None
    include_tax: bool = True

    
class InvoiceByPercentageRequest(BaseModel):
    client_id: int
    task_id: int
    percentage: float
    currency: str  # 'COP' o 'USD'
    exchange_rate: float | None = None
    payment_type: str  # anticipo, fracción, final

class InvoiceFilterRequest(BaseModel):
    client_id: int
    start_date: str  
    end_date: str


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    start_time: time
    end_time: time
    user_ids: List[int]

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    user_ids: Optional[List[int]] = None


class ContractCreate(BaseModel):
    client_id: int
    description: Optional[str] = None
    total_value: float
    start_date: date
    end_date: Optional[date] = None

class ContractUpdate(BaseModel):
    description: Optional[str] = None
    total_value: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    active: Optional[bool] = None



class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str
    salary: float
    cost: float
    weekly_hours: float
    cost_per_hour_client: float 
    desvinculado: bool = False



class UserUpdate(BaseModel):
    id: int
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    salary: Optional[float] = None
    cost: Optional[float] = None
    weekly_hours: Optional[float] = None
    cost_per_hour_client: Optional[float] = None 
    desvinculado: Optional[bool] = None

class TaskTimeEntriesRequest(BaseModel):
    task_id: int
    start_date: datetime
    end_date: datetime
    facturado: Optional[Literal["si", "no", "parcialmente"]] = None
    hour_package: Optional[float] = None



class GroupCreate(BaseModel):
    group_name: str
    tasks: List[int]
    client_id: int
    monthly_limit_hours: int
    

class GroupUpdate(BaseModel):
    group_name: Optional[str] = None
    tasks: Optional[List[int]] = None
    monthly_limit_hours: Optional[int] = None
    


class PendienteCreate(BaseModel):
    task_id: int
    description: str
    status: str
    nota: str


class PendienteUpdate(BaseModel):
    id: int
    description: Optional[str] = None
    status: Optional[str] = None
    nota: Optional[str] = None
