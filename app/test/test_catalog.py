from decimal import Decimal

from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest


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

    return centre, test, centre_test


def test_list_centres(client, db_session):
    centre, _, _ = create_catalog(db_session)

    response = client.get("/centres")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(centre.id)
    assert data[0]["name"] == "Test Diagnostics"


def test_get_centre(client, db_session):
    centre, _, _ = create_catalog(db_session)

    response = client.get(f"/centres/{centre.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(centre.id)
    assert data["location"] == "Noida"


def test_get_nonexistent_centre(client):
    import uuid

    response = client.get(
        f"/centres/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_list_tests(client, db_session):
    _, test, _ = create_catalog(db_session)

    response = client.get("/tests")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == str(test.id)
    assert data[0]["name"] == "Test CBC"


def test_get_test(client, db_session):
    _, test, _ = create_catalog(db_session)

    response = client.get(f"/tests/{test.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(test.id)
    assert data["name"] == "Test CBC"


def test_get_nonexistent_test(client):
    import uuid

    response = client.get(
        f"/tests/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_list_centre_tests(client, db_session):
    centre, test, centre_test = create_catalog(db_session)

    response = client.get(
        f"/centres/{centre.id}/tests"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["id"] == str(centre_test.id)
    assert data[0]["test"]["id"] == str(test.id)
    assert data[0]["test"]["name"] == "Test CBC"
    assert Decimal(data[0]["price"]) == Decimal("500.00")


def test_list_tests_for_nonexistent_centre(client):
    import uuid

    response = client.get(
        f"/centres/{uuid.uuid4()}/tests"
    )

    assert response.status_code == 404