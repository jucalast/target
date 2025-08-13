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
        name: User's full name
        role: User's role in the system
        avatar: URL to user's avatar image (optional)
        hashed_password: Hashed password (not plain text)
        created_at: Timestamp when the user was created
        analyses: Relationship to the Analysis model (one-to-many)
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User information
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    avatar = Column(String, nullable=True)
    
    # User authentication
    hashed_password = Column(String, nullable=False)
    
    # Timestamps
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    analyses = relationship("Analysis", back_populates="owner", cascade="all, delete-orphan")
