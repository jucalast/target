"""Analysis model for the database.

This module defines the Analysis model that represents an analysis in the database.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey,\
    JSON, func
from sqlalchemy.orm import relationship

from shared.db.postgres import Base


class Analysis(Base):
    """Analysis model representing an analysis in the database.
    Attributes:
        id: Primary key
        user_id: Foreign key to the user who created the analysis
        niche: The niche being analyzed
        description: Description of the analysis
        normalized_text: Normalized text for NLP processing
        keywords: Extracted keywords as JSON
        entities: Extracted named entities as JSON
        embedding: Vector embedding of the analysis text
        created_at: Timestamp when the analysis was created
        owner: Relationship to the User model
    """
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,\
        index=True)
    niche = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=False)
    entities = Column(JSON, nullable=False)
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="analyses")
