from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.booking import BookingStatus


class BookingCreateRequest(BaseModel):
    centre_test_id: UUID
    appointment_at: datetime


class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    centre_test_id: UUID
    appointment_at: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)