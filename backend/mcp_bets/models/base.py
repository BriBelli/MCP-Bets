"""
SQLAlchemy Base Models

All ORM models inherit from this base class.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
