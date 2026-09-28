from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.user import User
from app.core.security import hash_password


def create_user(db_session, email="user@example.com"):
    user = User(
        name="Test User",
        email=email,
        password_hash=hash_password("password123"),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_catalog(db_session):
    centre = DiagnosticCentre(
        name="Test Diagnostics",
        location="Noida",
    )

    test = DiagnosticTest(
        name="Test CBC",
        description="Test blood count",
    )

    db_session.add_all([centre, test])
    db_session.flush()

    centre_test = CentreTest(
        centre_id=centre.id,
        test_id=test.id,
        price=Decimal("500.00"),
    )

    db_session.add(centre_test)
    db_session.commit()
    db_session.refresh(centre_test)

    return centre, test, centre_test


def login(client, email="user@example.com"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_create_booking(client, db_session):
    create_user(db_session)
    _, _, centre_test = create_catalog(db_session)

    token = login(client)

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["centre_test_id"] == str(centre_test.id)
    assert data["amount"] == "500.00"
    assert data["status"] == "PENDING"


def test_create_booking_without_authentication(client, db_session):
    _, _, centre_test = create_catalog(db_session)

    response = client.post(
        "/bookings",
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert response.status_code == 401


def test_create_booking_with_invalid_centre_test(client, db_session):
    create_user(db_session)

    token = login(client)

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(uuid4()),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert response.status_code == 404


def test_list_my_bookings(client, db_session):
    create_user(db_session)
    _, _, centre_test = create_catalog(db_session)

    token = login(client)

    client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["amount"] == "500.00"
    assert data[0]["status"] == "PENDING"


def test_get_booking(client, db_session):
    create_user(db_session)
    _, _, centre_test = create_catalog(db_session)

    token = login(client)

    create_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    booking_id = create_response.json()["id"]

    response = client.get(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == booking_id


def test_get_nonexistent_booking(client, db_session):
    create_user(db_session)

    token = login(client)

    response = client.get(
        f"/bookings/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

def test_user_cannot_access_another_users_booking(client, db_session):
    create_user(db_session, email="user1@example.com")
    _, _, centre_test = create_catalog(db_session)

    token_user1 = login(client, email="user1@example.com")

    create_response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token_user1}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert create_response.status_code == 201

    booking_id = create_response.json()["id"]

    # Create second user
    create_user(
        db_session,
        email="user2@example.com",
    )

    token_user2 = login(
        client,
        email="user2@example.com",
    )

    response = client.get(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {token_user2}"},
    )

    assert response.status_code == 404

def test_user_only_sees_own_bookings(client, db_session):
    create_user(db_session, email="user1@example.com")
    create_user(db_session, email="user2@example.com")

    _, _, centre_test = create_catalog(db_session)

    token_user1 = login(client, email="user1@example.com")
    token_user2 = login(client, email="user2@example.com")

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token_user1}"},
        json={
            "centre_test_id": str(centre_test.id),
            "appointment_at": "2026-10-10T10:30:00+05:30",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/bookings",
        headers={"Authorization": f"Bearer {token_user2}"},
    )

    assert response.status_code == 200
    assert response.json() == []