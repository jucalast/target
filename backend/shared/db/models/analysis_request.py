"""AnalysisRequest model for the database.

This module defines the AnalysisRequest model that represents an analysis request in the database.
"""
from sqlalchemy import Column, Integer, String

from shared.db.postgres import Base


class AnalysisRequest(Base):
    """AnalysisRequest model representing an analysis request in the database.
    Attributes:
        id: Primary key
        description: Description of the analysis request
        status: Current status of the request
    """
    __tablename__ = "analysis_requests"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    status = Column(String)
