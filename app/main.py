from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "service": settings.app_name,
        "database": "connected",
    }