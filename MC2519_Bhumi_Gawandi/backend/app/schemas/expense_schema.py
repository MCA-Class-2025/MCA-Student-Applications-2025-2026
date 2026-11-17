from datetime import datetime

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str
    payment_method: str
    date: datetime
    notes: str = ""


class ExpenseUpdate(BaseModel):
    title: str
    amount: float
    category: str
    payment_method: str
    date: datetime
    notes: str = ""