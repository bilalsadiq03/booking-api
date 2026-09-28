from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.booking import BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook import PaymentWebhookRequest, WebhookResponse


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/webhook/",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
)
def payment_webhook(
    payload: PaymentWebhookRequest,
    db: Session = Depends(get_db),
):

    # Only support payment.updated events.
    if payload.event_type != "payment.updated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported event type",
        )
        
    # Check whether this event has already been processed.
    existing_event = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.event_id == payload.event_id
        )
    )

    if existing_event is not None:
        return WebhookResponse(status="already_processed")

    # Find the payment referenced by the external provider.
    payment = db.scalar(
        select(Payment).where(
            Payment.payment_reference == payload.payment_reference
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    webhook_event = WebhookEvent(
        event_id=payload.event_id,
        event_type=payload.event_type,
        processed=False,
        payload=payload.model_dump(mode="json"),
    )

    db.add(webhook_event)

    # Update payment.
    payment.status = payload.status

    # Update associated booking.
    booking = payment.booking

    if payload.status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    webhook_event.processed = True
    webhook_event.processed_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        # Another concurrent request may have inserted the same event.
        db.rollback()

        existing_event = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == payload.event_id
            )
        )

        if existing_event is not None:
            return WebhookResponse(status="already_processed")

        raise

    return WebhookResponse(status="processed")