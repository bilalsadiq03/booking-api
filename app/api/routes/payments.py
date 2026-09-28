import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreateRequest, PaymentResponse


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, payload.booking_id)

    # Booking does not exist
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Booking belongs to another user
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Booking must be pending
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Booking is not eligible for payment",
        )

    # Prevent duplicate payment
    if booking.payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already exists for this booking",
        )

    # Simulate payment gateway
    payment_status = random.choice(
        [PaymentStatus.SUCCESS, PaymentStatus.FAILED]
    )

    payment = Payment(
        booking_id=booking.id,
        payment_reference=f"PAY-{uuid.uuid4().hex[:12].upper()}",
        amount=booking.amount,
        status=payment_status,
    )

    # Update booking according to payment result
    if payment_status == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
    else:
        booking.status = BookingStatus.FAILED

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment