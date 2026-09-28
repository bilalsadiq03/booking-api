from decimal import Decimal

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest


def seed_catalog():
    db = SessionLocal()

    try:
        existing_test = db.scalar(
            select(DiagnosticTest).limit(1)
        )

        if existing_test:
            print("Catalog already contains data.")
            return

        centre_1 = DiagnosticCentre(
            name="EVE Diagnostics",
            location="Greater Noida",
        )

        centre_2 = DiagnosticCentre(
            name="City Health Labs",
            location="Noida",
        )

        test_1 = DiagnosticTest(
            name="Complete Blood Count",
            description="Measures different components of blood.",
        )

        test_2 = DiagnosticTest(
            name="Lipid Profile",
            description="Measures cholesterol and triglyceride levels.",
        )

        test_3 = DiagnosticTest(
            name="HbA1c",
            description="Measures average blood glucose over the previous few months.",
        )

        db.add_all([
            centre_1,
            centre_2,
            test_1,
            test_2,
            test_3,
        ])

        db.flush()

        db.add_all([
            CentreTest(
                centre_id=centre_1.id,
                test_id=test_1.id,
                price=Decimal("500.00"),
            ),
            CentreTest(
                centre_id=centre_1.id,
                test_id=test_2.id,
                price=Decimal("700.00"),
            ),
            CentreTest(
                centre_id=centre_2.id,
                test_id=test_1.id,
                price=Decimal("450.00"),
            ),
            CentreTest(
                centre_id=centre_2.id,
                test_id=test_3.id,
                price=Decimal("600.00"),
            ),
        ])

        db.commit()

        print("Catalog seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_catalog()