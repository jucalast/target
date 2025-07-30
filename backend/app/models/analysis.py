# backend/app/models/analysis.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    niche = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)

    keywords = Column(JSON, nullable=False)
    entities = Column(JSON, nullable=False)
    embedding = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="analyses")
