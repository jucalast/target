"""
Módulo de modelos do banco de dados.

Este pacote contém todos os modelos SQLAlchemy usados na aplicação.
"""

from .analysis import Analysis
from .analysis_request import AnalysisRequest
from .etl_models import (
    ETLResultModel,
    MarketSegmentModel,
    MarketMetricModel,
    DataPointModel,
    SearchTrendModel,
    NewsArticleModel,
    ETLRunLogModel,
    DataSource,
    DataQualityLevel
)
from .user import User

__all__ = [
    'User',
    'Analysis',
    'AnalysisRequest',
    'ETLResultModel',
    'MarketSegmentModel',
    'MarketMetricModel',
    'DataPointModel',
    'SearchTrendModel',
    'NewsArticleModel',
    'ETLRunLogModel',
    'DataSource',
    'DataQualityLevel'
]
