from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.payment import PaymentStatus


class PaymentCreateRequest(BaseModel):
    booking_id: UUID
    model_config = ConfigDict(extra="forbid")


class PaymentResponse(BaseModel):
    id: UUID
    booking_id: UUID
    payment_reference: str
    amount: Decimal
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)