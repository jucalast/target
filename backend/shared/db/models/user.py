"""User model for the database.

This module defines the User model that represents a user in the database.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from shared.db.postgres import Base

class User(Base):
    """User model representing a user in the database.
    
    Attributes:
        id: Primary key
        email: User's email (unique, indexed)
        hashed_password: Hashed password (not plain text)
        created_at: Timestamp when the user was created
        analyses: Relationship to the Analysis model (one-to-many)
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User authentication
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analyses = relationship("Analysis", back_populates="owner", cascade="all, delete-orphan")
