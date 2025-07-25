from app.models.analysis_request import AnalysisRequest
from app.schemas.analysis_request import AnalysisRequestCreate
from app.db.database import SessionLocal

def create_analysis_request(db: SessionLocal, request: AnalysisRequestCreate):
    db_request = AnalysisRequest(description=request.description, status=request.status)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request
