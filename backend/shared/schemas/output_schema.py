"""Output schema for market analysis results."""
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Keyword(BaseModel):
    """A keyword with its relevance score."""
    keyword: str
    score: float = Field(..., ge=0.0, le=1.0)
    source: Optional[str] = None

class Topic(BaseModel):
    """A topic with its weight and keywords."""
    label: str
    weight: float = Field(..., ge=0.0, le=1.0)
    keywords: List[Keyword] = []

class Entity(BaseModel):
    """A named entity from text."""
    text: str
    type: str
    start: int
    end: int

class Embedding(BaseModel):
    """A text embedding vector."""
    model: str
    vector: List[float]
    dim: int

class NLPAnalysis(BaseModel):
    """Results of NLP analysis."""
    keywords: List[Keyword] = []
    topics: List[Topic] = []
    entities: List[Entity] = []
    embeddings: Dict[str, Embedding] = {}

class IBGEData(BaseModel):
    """Data from IBGE SIDRA."""
    table_code: str
    table_name: str
    period: str
    data: List[Dict[str, Any]] = []
    variables: List[Dict[str, Any]] = []

class GoogleTrendsData(BaseModel):
    """Data from Google Trends."""
    interest_over_time: List[Dict[str, Any]] = []
    related_queries: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

class MarketAnalysisOutput(BaseModel):
    """Complete market analysis output."""
    analysis_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "processing", "completed", "failed"]
    input: Dict[str, Any]
    nlp: NLPAnalysis
    ibge: Dict[str, IBGEData] = {}
    google_trends: Optional[GoogleTrendsData] = None
    insights: Dict[str, Any] = {}
    processing_time: Optional[float] = None
    version: str = "1.0.0"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
