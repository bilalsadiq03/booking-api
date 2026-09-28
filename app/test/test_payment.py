from app.models.booking import Booking, BookingStatus
from app.models.payment import PaymentStatus
from app.test.test_booking import create_catalog, create_user, login


def test_successful_payment(client, db_session, monkeypatch):
    # Arrange
    create_user(
        db_session,
        email="payment@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email="payment@example.com",
    )

    # Create booking
    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    # Force payment gateway to return SUCCESS
    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.SUCCESS,
    )

    # Act
    payment_response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    # Assert payment
    assert payment_response.status_code == 201

    data = payment_response.json()

    assert data["booking_id"] == booking_id
    assert data["amount"] == "500.00"
    assert data["status"] == "SUCCESS"
    assert data["payment_reference"].startswith("PAY-")

    # Assert booking was confirmed
    booking = db_session.get(
        Booking,
        booking_id,
    )

    assert booking is not None
    assert booking.status == BookingStatus.CONFIRMED

def test_failed_payment(client, db_session, monkeypatch):
    # Arrange
    create_user(
        db_session,
        email="failed-payment@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email="failed-payment@example.com",
    )

    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-11T10:30:00+05:30",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    # Force payment gateway to return FAILED
    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.FAILED,
    )

    # Act
    payment_response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    # Assert payment
    assert payment_response.status_code == 201

    data = payment_response.json()

    assert data["booking_id"] == booking_id
    assert data["amount"] == "500.00"
    assert data["status"] == "FAILED"

    # Assert booking was failed
    booking = db_session.get(
        Booking,
        booking_id,
    )

    assert booking is not None
    assert booking.status == BookingStatus.FAILED

def test_duplicate_payment_rejected(client, db_session, monkeypatch):
    create_user(
        db_session,
        email="duplicate@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email="duplicate@example.com",
    )

    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-12T10:30:00+05:30",
        },
    )

    booking_id = booking_response.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.SUCCESS,
    )

    first_payment = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking_id},
    )

    assert first_payment.status_code == 201

    second_payment = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking_id},
    )

    assert second_payment.status_code == 409

def test_user_cannot_pay_another_users_booking(
    client,
    db_session,
    monkeypatch,
):
    create_user(
        db_session,
        email="owner@example.com",
    )
    create_user(
        db_session,
        email="attacker@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    owner_token = login(
        client,
        email="owner@example.com",
    )

    attacker_token = login(
        client,
        email="attacker@example.com",
    )

    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-13T10:30:00+05:30",
        },
    )

    booking_id = booking_response.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.SUCCESS,
    )

    payment_response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {attacker_token}"},
        json={"booking_id": booking_id},
    )

    assert payment_response.status_code == 404

def test_payment_not_allowed_for_confirmed_booking(
    client,
    db_session,
    monkeypatch,
):
    create_user(
        db_session,
        email="confirmed@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email="confirmed@example.com",
    )

    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-14T10:30:00+05:30",
        },
    )

    booking_id = booking_response.json()["id"]

    monkeypatch.setattr(
        "app.api.routes.payments.random.choice",
        lambda choices: PaymentStatus.SUCCESS,
    )

    first_payment = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking_id},
    )

    assert first_payment.status_code == 201

    second_payment = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"booking_id": booking_id},
    )

    assert second_payment.status_code == 409

def test_payment_requires_authentication(client, db_session):
    response = client.post(
        "/payments",
        json={
            "booking_id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert response.status_code == 401

def test_payment_rejects_client_supplied_amount(
    client,
    db_session,
    monkeypatch,
):
    create_user(
        db_session,
        email="amount@example.com",
    )

    _, _, centre_test = create_catalog(db_session)

    token = login(
        client,
        email="amount@example.com",
    )

    booking_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2027-01-10T10:30:00+05:30",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
            "amount": 1,
        },
    )

    assert response.status_code == 422