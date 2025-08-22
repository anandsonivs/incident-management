# SQLAlchemy base class for all models
from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, Integer, DateTime, func

@as_declarative()
class Base:
    """Base class for all SQLAlchemy models."""
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # Common columns for all tables
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.
        Excludes SQLAlchemy internal attributes.
        """
        return {
            c.name: getattr(self, c.name) 
            for c in self.__table__.columns
            if not c.name.startswith('_')
        }
