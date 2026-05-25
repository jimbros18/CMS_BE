from pydantic import BaseModel
from typing import List, Optional

class Client(BaseModel):
    dateServiced: str
    deceasedFirst: str
    deceasedMiddle: Optional[str] = None
    deceasedLast: str
    address: str
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

class DSWD(BaseModel):
    gl_date: Optional[str] = None
    ci_number: Optional[str] = None
    processor: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None    
    notes: Optional[str] = None

class Payment(BaseModel):
    date_paid: Optional[str] = None
    amount_paid: Optional[float] = None
    details: Optional[str] = None

class NewClient(BaseModel):
    client: Client
    inclusions: List[str] = []
    dswd: DSWD | None = None
    otherCharges: List[OtherCharges] = []
    payments: List[Payment] = []