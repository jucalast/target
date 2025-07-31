"""
Módulo de modelos do banco de dados.

Este pacote contém todos os modelos SQLAlchemy usados na aplicação.
"""


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
