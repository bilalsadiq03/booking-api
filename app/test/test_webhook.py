from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.test.test_booking import create_catalog, create_user, login


def create_pending_booking(client, db_session, email):
    create_user(
        db_session,
        email=email,
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email=email,
    )

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-20T10:30:00+05:30",
        },
    )

    assert response.status_code == 201

    return response.json()["id"], token


def create_payment(client, db_session, booking_id, token, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.SUCCESS,
    )

    response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert response.status_code == 201

    return response.json()["payment_reference"]


def test_success_webhook_confirms_booking(
    client,
    db_session,
    monkeypatch,
):
    booking_id, token = create_pending_booking(
        client,
        db_session,
        "webhook-success@example.com",
    )

    payment_reference = create_payment(
        client,
        db_session,
        booking_id,
        token,
        monkeypatch,
    )

    # Payment initially succeeded and booking is confirmed.
    # Reset them to simulate a provider webhook arriving later.
    booking = db_session.get(Booking, booking_id)
    booking.status = BookingStatus.PENDING

    payment = db_session.query(Payment).filter(
        Payment.payment_reference == payment_reference
    ).one()
    payment.status = PaymentStatus.FAILED

    db_session.commit()

    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt-success-001",
            "event_type": "payment.updated",
            "payment_reference": payment_reference,
            "status": "SUCCESS",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    db_session.refresh(payment)
    db_session.refresh(booking)

    assert payment.status == PaymentStatus.SUCCESS
    assert booking.status == BookingStatus.CONFIRMED


def test_failed_webhook_fails_booking(
    client,
    db_session,
    monkeypatch,
):
    booking_id, token = create_pending_booking(
        client,
        db_session,
        "webhook-failed@example.com",
    )

    payment_reference = create_payment(
        client,
        db_session,
        booking_id,
        token,
        monkeypatch,
    )

    booking = db_session.get(Booking, booking_id)
    booking.status = BookingStatus.PENDING

    payment = db_session.query(Payment).filter(
        Payment.payment_reference == payment_reference
    ).one()
    payment.status = PaymentStatus.SUCCESS

    db_session.commit()

    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt-failed-001",
            "event_type": "payment.updated",
            "payment_reference": payment_reference,
            "status": "FAILED",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    db_session.refresh(payment)
    db_session.refresh(booking)

    assert payment.status == PaymentStatus.FAILED
    assert booking.status == BookingStatus.FAILED


def test_duplicate_webhook_is_idempotent(
    client,
    db_session,
    monkeypatch,
):
    booking_id, token = create_pending_booking(
        client,
        db_session,
        "webhook-duplicate@example.com",
    )

    payment_reference = create_payment(
        client,
        db_session,
        booking_id,
        token,
        monkeypatch,
    )

    # Reset state so the webhook performs the first transition.
    booking = db_session.get(Booking, booking_id)
    booking.status = BookingStatus.PENDING

    payment = (
        db_session.query(Payment)
        .filter(
            Payment.payment_reference == payment_reference
        )
        .one()
    )
    payment.status = PaymentStatus.FAILED

    db_session.commit()

    payload = {
        "event_id": "evt-duplicate-001",
        "event_type": "payment.updated",
        "payment_reference": payment_reference,
        "status": "SUCCESS",
    }

    # First delivery should process the event.
    first_response = client.post(
        "/payments/webhook/",
        json=payload,
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "processed"

    # Second delivery of the exact same event should be idempotent.
    second_response = client.post(
        "/payments/webhook/",
        json=payload,
    )

    assert second_response.status_code == 200
    assert second_response.json()["status"] == "already_processed"


def test_webhook_payment_not_found(client):
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt-missing-payment",
            "event_type": "payment.updated",
            "payment_reference": "PAY-DOES-NOT-EXIST",
            "status": "SUCCESS",
        },
    )

    assert response.status_code == 404


def test_webhook_unsupported_event_type(
    client,
):
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt-unsupported-001",
            "event_type": "unknown.event",
            "payment_reference": "PAY-DOES-NOT-EXIST",
            "status": "SUCCESS",
        },
    )

    assert response.status_code == 400

def test_webhook_rejects_conflicting_terminal_state(
    client,
    db_session,
    monkeypatch,
):
    booking_id, token = create_pending_booking(
        client,
        db_session,
        "webhook-conflict@example.com",
    )

    payment_reference = create_payment(
        client,
        db_session,
        booking_id,
        token,
        monkeypatch,
    )

    # Put the booking into a terminal SUCCESS state.
    booking = db_session.get(Booking, booking_id)
    payment = (
        db_session.query(Payment)
        .filter(
            Payment.payment_reference == payment_reference
        )
        .one()
    )

    booking.status = BookingStatus.CONFIRMED
    payment.status = PaymentStatus.SUCCESS
    db_session.commit()

    # A FAILED event now conflicts with the current terminal state.
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt-conflicting-state-001",
            "event_type": "payment.updated",
            "payment_reference": payment_reference,
            "status": "FAILED",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Webhook conflicts with current booking state"
    )

    # Verify the original state was not changed.
    db_session.refresh(booking)
    db_session.refresh(payment)

    assert booking.status == BookingStatus.CONFIRMED
    assert payment.status == PaymentStatus.SUCCESS