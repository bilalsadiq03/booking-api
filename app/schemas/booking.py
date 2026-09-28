from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.booking import BookingStatus


class BookingCreateRequest(BaseModel):
    centre_test_id: UUID
    appointment_at: datetime

    @field_validator("appointment_at")
    @classmethod
    def validate_appointment_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "appointment_at must include timezone information"
            )

        if value <= datetime.now(timezone.utc):
            raise ValueError(
                "appointment_at must be in the future"
            )

        return value


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