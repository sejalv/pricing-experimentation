from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.events.models import create_tables, get_engine, get_session_factory
from src.events.logger import log_conversion, log_exposure

app = FastAPI(title="Experiment Event Logger", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine = get_engine()
_SessionFactory = get_session_factory(_engine)


@app.on_event("startup")
def on_startup():
    create_tables(_engine)


def get_db():
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


DbDep = Annotated[Session, Depends(get_db)]


class ExposureRequest(BaseModel):
    user_id: str
    variant: str
    price_shown: float
    timestamp: datetime | None = None


class ConversionRequest(BaseModel):
    user_id: str
    variant: str
    converted: bool
    revenue: float | None = None
    timestamp: datetime | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/event/exposure", status_code=201)
def record_exposure(body: ExposureRequest, db: DbDep):
    event = log_exposure(db, body.user_id, body.variant, body.price_shown, body.timestamp)
    return {"id": event.id, "recorded": True}


@app.post("/event/conversion", status_code=201)
def record_conversion(body: ConversionRequest, db: DbDep):
    event = log_conversion(db, body.user_id, body.variant, body.converted, body.revenue, body.timestamp)
    return {"id": event.id, "recorded": True}


@app.get("/events/summary")
def summary(db: DbDep):
    """Quick counts for sanity-checking — not the analysis endpoint."""
    from sqlalchemy import text
    exposure_count = db.execute(text("SELECT COUNT(*) FROM exposure_events")).scalar()
    conversion_count = db.execute(text("SELECT COUNT(*) FROM conversion_events")).scalar()
    return {"exposures": exposure_count, "conversions": conversion_count}
