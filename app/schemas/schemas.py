from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import date, datetime, time


class clientCreate(BaseModel):
    name: str
    permanent: bool
    monthly_limit_hours: Optional[float] = 0
    lawyers: list[int]
    nit: str
    phone: str
    city: str
    address: str
    email: str


class clientUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    lawyers: Optional[list[int]] = None 
    permanent: Optional[bool] = None
    monthly_limit_hours: Optional[float] = None 
    nit: str
    phone: str
    city: str
    address: str
    email: str




class clientDelete(BaseModel):
    id: int



class TaskCreate(BaseModel):
    client_id: int
    title: str
    billing_type: Literal["hourly", "percentage"]
    status: str
    area: Optional[str] = "Sin área"
    note: Optional[str] = None
    total_value: Optional[float] = Field(default=None, description="Requerido si billing_type es 'percentage'")
    due_date: Optional[datetime] = None
    permanent: bool = False

class TaskUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    area: Optional[str] = None
    billing_type: Optional[Literal["hourly", "percentage"]] = None
    note: Optional[str] = None
    total_value: Optional[float] = None

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
