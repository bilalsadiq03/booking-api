from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.payments import router as payments_router
from app.api.routes.webhooks import router as webhooks_router
from app.core.config import settings    
from app.database.session import get_db


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(bookings_router)
app.include_router(payments_router)
app.include_router(webhooks_router)


@app.get("/")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": settings.app_name,
        "database": "connected",
    }