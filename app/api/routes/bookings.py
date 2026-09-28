from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.centre_test import CentreTest
from app.models.user import User
from app.schemas.booking import BookingCreateRequest, BookingResponse


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)

# Create a new booking
@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    payload: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    centre_test = db.get(CentreTest, payload.centre_test_id)

    if centre_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre test offering not found",
        )

    booking = Booking(
        user_id=current_user.id,
        centre_test_id=centre_test.id,
        appointment_at=payload.appointment_at,
        amount=centre_test.price,
        status=BookingStatus.PENDING,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


# List all bookings for the current user
@router.get(
    "",
    response_model=list[BookingResponse],
)
def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = (
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )

    return db.scalars(statement).all()


# Get a specific booking for the current user
@router.get(
    "",
    response_model=list[BookingResponse],
)
def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = (
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )

    return db.scalars(statement).all()

# Get a specific booking for the current user
@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
)
def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, booking_id)

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return booking