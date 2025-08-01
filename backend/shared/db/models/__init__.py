"""
Módulo de modelos do banco de dados.

Este pacote contém todos os modelos SQLAlchemy usados na aplicação.
"""
from .user import User
from .analysis import Analysis
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

# Exporta todos os modelos para facilitar as importações
__all__ = [
    'User',
    'Analysis',
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
