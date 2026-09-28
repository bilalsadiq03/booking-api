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
    # Only payment.updated events are supported.
    if payload.event_type != "payment.updated":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported event type",
        )

    # Idempotency check for an already processed event.
    existing_event = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.event_id == payload.event_id
        )
    )

    if existing_event is not None:
        return WebhookResponse(status="already_processed")

    # Find the payment using the external payment reference.
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

    booking = payment.booking

    # Prevent contradictory state transitions.
    if booking.status != BookingStatus.PENDING:
        same_terminal_state = (
            booking.status == BookingStatus.CONFIRMED
            and payload.status == PaymentStatus.SUCCESS
        ) or (
            booking.status == BookingStatus.FAILED
            and payload.status == PaymentStatus.FAILED
        )

        if same_terminal_state:
            webhook_event = WebhookEvent(
                event_id=payload.event_id,
                event_type=payload.event_type,
                processed=True,
                payload=payload.model_dump(mode="json"),
                processed_at=datetime.now(timezone.utc),
            )

            db.add(webhook_event)

            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                return WebhookResponse(
                    status="already_processed"
                )

            return WebhookResponse(
                status="already_processed"
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Webhook conflicts with current booking state",
        )

    # Create exactly one webhook event for this request.
    webhook_event = WebhookEvent(
        event_id=payload.event_id,
        event_type=payload.event_type,
        processed=False,
        payload=payload.model_dump(mode="json"),
    )

    db.add(webhook_event)

    # Apply payment status.
    payment.status = payload.status

    # Apply corresponding booking status.
    if payload.status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    # Mark webhook as successfully processed.
    webhook_event.processed = True
    webhook_event.processed_at = datetime.now(timezone.utc)

    try:
        db.commit()
    except IntegrityError:
        # Another request may have processed the same event
        # concurrently.
        db.rollback()

        existing_event = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.event_id == payload.event_id
            )
        )

        if existing_event is not None:
            return WebhookResponse(
                status="already_processed"
            )

        raise

    return WebhookResponse(status="processed")