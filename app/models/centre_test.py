from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.diagnostic_centre import DiagnosticCentre
    from app.models.diagnostic_test import DiagnosticTest


class CentreTest(Base):
    __tablename__ = "centre_tests"

    __table_args__ = (
        UniqueConstraint(
            "centre_id",
            "test_id",
            name="uq_centre_test",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    centre_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_centres.id"),
        nullable=False,
        index=True,
    )

    test_id: Mapped[int] = mapped_column(
        ForeignKey("diagnostic_tests.id"),
        nullable=False,
        index=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    centre: Mapped["DiagnosticCentre"] = relationship(
        back_populates="centre_tests",
    )

    test: Mapped["DiagnosticTest"] = relationship(
        back_populates="centre_tests",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="centre_test",
    )