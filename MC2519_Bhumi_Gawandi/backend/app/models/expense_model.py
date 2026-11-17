from datetime import datetime, timezone

from pydantic import BaseModel


class ExpenseModel(BaseModel):
    user_id: str
    title: str
    amount: float
    category: str
    payment_method: str
    date: datetime
    notes: str = ""
    receipt: str = ""

    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)