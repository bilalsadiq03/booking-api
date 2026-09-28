from pydantic import BaseModel

from app.models.payment import PaymentStatus


class PaymentWebhookRequest(BaseModel):
    event_id: str
    event_type: str
    payment_reference: str
    status: PaymentStatus


class WebhookResponse(BaseModel):
    status: str