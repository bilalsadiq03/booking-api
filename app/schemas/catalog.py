from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticCentreResponse(BaseModel):
    id: UUID
    name: str
    location: str

    model_config = ConfigDict(from_attributes=True)


class DiagnosticTestResponse(BaseModel):
    id: UUID
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class CentreTestResponse(BaseModel):
    id: UUID
    test_id: UUID
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class CentreTestDetailResponse(BaseModel):
    id: UUID
    test: DiagnosticTestResponse
    price: Decimal

    model_config = ConfigDict(from_attributes=True)