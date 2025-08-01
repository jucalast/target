from enum import Enum

class AnalysisStatus(str, Enum):
    """Status possíveis para uma análise."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUEUED = "queued"
    CANCELLED = "cancelled"
