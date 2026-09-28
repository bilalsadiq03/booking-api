from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.schemas.catalog import (
    CentreTestDetailResponse,
    DiagnosticCentreResponse,
    DiagnosticTestResponse,
)


router = APIRouter(
    tags=["Catalogue"],
)


# List all Diagnostic Centres
@router.get(
    "/centres",
    response_model=list[DiagnosticCentreResponse],
)
def list_centres(
    db: Session = Depends(get_db),
):
    statement = (
        select(DiagnosticCentre)
        .order_by(DiagnosticCentre.name)
    )

    return db.scalars(statement).all()

@router.get(
    "/centres/{centre_id}",
    response_model=DiagnosticCentreResponse,
)
def get_centre(
    centre_id: UUID,
    db: Session = Depends(get_db),
):
    centre = db.get(DiagnosticCentre, centre_id)

    if centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    return centre


# List all Diagnostic Tests
@router.get(
    "/tests",
    response_model=list[DiagnosticTestResponse],
)
def list_tests(
    db: Session = Depends(get_db),
):
    statement = (
        select(DiagnosticTest)
        .order_by(DiagnosticTest.name)
    )

    return db.scalars(statement).all()


# Get Diagnostic Test by ID
@router.get(
    "/tests/{test_id}",
    response_model=DiagnosticTestResponse,
)
def get_test(
    test_id: UUID,
    db: Session = Depends(get_db),
):
    test = db.get(DiagnosticTest, test_id)

    if test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic test not found",
        )

    return test


# List all Diagnostic Tests by Diagnostic Centre
@router.get(
    "/centres/{centre_id}/tests",
    response_model=list[CentreTestDetailResponse],
)
def list_centre_tests(
    centre_id: UUID,
    db: Session = Depends(get_db),
):
    centre = db.get(DiagnosticCentre, centre_id)

    if centre is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnostic centre not found",
        )

    statement = (
        select(CentreTest)
        .where(CentreTest.centre_id == centre_id)
        .options(selectinload(CentreTest.test))
        .order_by(CentreTest.price)
    )

    return db.scalars(statement).all()