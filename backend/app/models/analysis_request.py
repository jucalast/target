from sqlalchemy import Column, Integer, String
from app.db.database import Base

class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    status = Column(String)
