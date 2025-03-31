from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import date, datetime


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
    status: str
    due_date: datetime
    area: str

class TaskUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    area: Optional[str] = None

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


class TimeEntryCreate(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime
    description: str


class TimeEntryUpdate(BaseModel):
    start_time: Optional[datetime] 
    end_time: Optional[datetime] 


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


class InvoiceByHoursRequest(BaseModel):
    client_id: int
    currency: Literal["COP", "USD"]
    exchange_rate: Optional[float] = None 
    include_tax: bool = True 

    
class InvoiceByPercentageRequest(BaseModel):
    client_id: int
    contract_id: int  
    percentage: float  
    payment_type: Literal["anticipo", "fracción", "final"]
    currency: Literal["COP", "USD"]
    exchange_rate: Optional[float] = None
    include_tax: bool = True  

class InvoiceFilterRequest(BaseModel):
    client_id: int
    start_date: str  
    end_date: str


class EventCreate(BaseModel):
    title: str
    event_date: date
    user_ids: List[int]

class EventUpdate(BaseModel):
    title: str
    event_date: date
    user_ids: List[int]



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
