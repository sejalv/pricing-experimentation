from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.events.models import ConversionEvent, ExposureEvent


def log_exposure(
    session: Session,
    user_id: str,
    variant: str,
    price_shown: float,
    timestamp: datetime | None = None,
) -> ExposureEvent:
    event = ExposureEvent(
        user_id=user_id,
        variant=variant,
        price_shown=price_shown,
        timestamp=timestamp or datetime.utcnow(),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def log_conversion(
    session: Session,
    user_id: str,
    variant: str,
    converted: bool,
    revenue: float | None = None,
    timestamp: datetime | None = None,
) -> ConversionEvent:
    event = ConversionEvent(
        user_id=user_id,
        variant=variant,
        converted=converted,
        revenue=revenue if converted else None,
        timestamp=timestamp or datetime.utcnow(),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event
