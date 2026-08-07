"""Base classes and Declarative Base for SQLAlchemy models.

This module provides the declarative base class that all database models
inherit from, along with a mixin for common timestamp fields.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models.
    
    All models should inherit from this class to ensure consistent
    configuration and behavior across the codebase.
    """
    
    pass


class BaseModel(Base):
    """Base model with common fields for all tables.
    
    Provides automatic timestamp management and a common ID primary key.
    """
    
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary representation.
        
        Returns all non-private attributes and their values.
        """
        result: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
