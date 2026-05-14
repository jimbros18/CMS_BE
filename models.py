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


class DSWD(BaseModel):
    glDate: Optional[str] = None
    ciNumber: Optional[str] = None
    processor: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None    
    notes: Optional[str] = None


class OtherCharges(BaseModel):
    item_service: Optional[str] = None
    amount: Optional[float] = None
    details: Optional[str] = None


class Payment(BaseModel):
    datePaid: Optional[str] = None
    amountPaid: Optional[float] = None
    details: Optional[str] = None


class NewClient(BaseModel):
    client: Client
    dswd: DSWD | None = None
    otherCharges: List[OtherCharges] = []
    payments: List[Payment] = []