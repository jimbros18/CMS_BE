from pydantic import BaseModel
from typing import List, Optional

class Client(BaseModel):
    dateServiced: str
    deceasedFirst: str
    deceasedMiddle: Optional[str] = None
    deceasedLast: str
    province: str
    city: str
    barangay: str
    purok: Optional[str] = None
    cellNumber: Optional[str] = None
    facebook: Optional[str] = None
    plan: Optional[str] = None
    coffin: Optional[str] = None
    coffinAmount: Optional[float] = None
    notes: Optional[str] = None

class Inclusions(BaseModel):
    items: Optional[List[str]] = None

class OtherCharges(BaseModel):
    item_service: Optional[str] = None
    amount: Optional[float] = None
    details: Optional[str] = None

class Assistance(BaseModel):
    provider: Optional[str] = None
    gl_date: Optional[str] = None
    ci_number: Optional[str] = None
    processor: Optional[str] = None
    amount: Optional[float] = None

class Payment(BaseModel):
    date_paid: Optional[str] = None
    amount_paid: Optional[float] = None
    details: Optional[str] = None

class Staff(BaseModel):
    embalmer: Optional[str] = None
    driver: Optional[str] = None
    helper: Optional[str] = None
    plate_num: Optional[str] = None

class NewClient(BaseModel):
    client: Client
    inclusions: List[str] = []
    assistance: List[Assistance] = []
    otherCharges: List[OtherCharges] = []
    payments: List[Payment] = []
    lights: List[int] = []  
    staff: List[Staff] = []
    returned: List[int] = []

class LoginPayload(BaseModel):
    email: str
    password: str