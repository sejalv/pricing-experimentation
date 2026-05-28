from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://experiment:experiment@localhost:5432/events")


class Base(DeclarativeBase):
    pass


class ExposureEvent(Base):
    __tablename__ = "exposure_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    variant = Column(String, nullable=False)
    price_shown = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class ConversionEvent(Base):
    __tablename__ = "conversion_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    variant = Column(String, nullable=False)
    converted = Column(Boolean, nullable=False)
    revenue = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


def get_engine():
    return create_engine(DATABASE_URL)


def get_session_factory(engine=None):
    engine = engine or get_engine()
    return sessionmaker(bind=engine)


def create_tables(engine=None):
    engine = engine or get_engine()
    Base.metadata.create_all(engine)
