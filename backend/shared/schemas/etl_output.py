"""
Esquemas para a saída do pipeline ETL.

Este módulo define os modelos Pydantic para estruturar os dados de saída
do pipeline ETL, garantindo consistência na comunicação com outros módulos.
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class DataSource(str, Enum):
    """Fontes de dados suportadas pelo pipeline ETL."""
    IBGE_SIDRA = "ibge_sidra"
    GOOGLE_TRENDS = "google_trends"
    NEWS_SCRAPING = "news_scraping"
    NLP_PROCESSING = "nlp_processing"

class DataQualityLevel(str, Enum):
    """Níveis de qualidade dos dados."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class DataPoint(BaseModel):
    """Ponto de dado genérico com metadados."""
    value: Any = Field(..., description="Valor do dado")
    source: DataSource = Field(..., description="Fonte dos dados")
    timestamp: datetime = Field(..., description="Data/hora da coleta")
    confidence: float = Field(1.0, description="Nível de confiança (0-1)")
    quality: DataQualityLevel = Field(DataQualityLevel.UNKNOWN,\
        description="Qualidade do dado")
    meta_info: Dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",  # Mantém compatibilidade com o JSON
        description="Metadados adicionais"
    )

    class Config:
        # Permite usar tanto 'meta_info' no código quanto 'metadata' no JSON
        populate_by_name = True

class MarketMetric(BaseModel):
    """Métrica de mercado com histórico e metadados."""
    name: str = Field(..., description="Nome da métrica")
    description: str = Field("", description="Descrição detalhada da métrica")
    unit: str = Field("", description="Unidade de medida (ex: R$, %, pessoas)")
    current_value: DataPoint = Field(..., description="Valor atual da métrica")
    historical_values: List[DataPoint] = Field(
        default_factory=list,
        description="Valores históricos da métrica"
    )
    trend: Optional[float] = Field(
        None,
        description="Tendência da métrica (\
            variação percentual em relação ao período anterior)"
    )

class MarketSegment(BaseModel):
    """Segmento de mercado com suas métricas."""
    name: str = Field(..., description="Nome do segmento")
    description: str = Field("", description="Descrição do segmento")
    metrics: Dict[str, MarketMetric] = Field(
        default_factory=dict,
        description="Métricas do segmento"
    )

class NewsArticle(BaseModel):
    """Notícia coletada de fontes setoriais."""
    title: str = Field(..., description="Título da notícia")
    source: str = Field(..., description="Fonte da notícia")
    url: Optional[HttpUrl] = Field(None, description="URL da notícia")
    published_at: datetime = Field(..., description="Data de publicação")
    summary: str = Field("", description="Resumo do conteúdo")
    sentiment: Optional[float] = Field(
        None,
        description="Análise de sentimento (-1 a 1,\
            onde -1 é negativo e 1 é positivo)"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Palavras-chave extraídas da notícia"
    )

class SearchTrend(BaseModel):
    """Tendência de busca do Google Trends."""
    keyword: str = Field(..., description="Termo de busca")
    values: List[Dict[datetime, float]] = Field(
        ...,
        description="Série temporal de interesse ao longo do tempo"
    )
    related_queries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Consultas relacionadas"
    )
    interest_by_region: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Interesse por região"
    )

class ETLOutput(BaseModel):
    """
    Estrutura de saída do pipeline ETL.
    Este modelo define o formato padronizado dos dados processados que serão
    consumidos pelo próximo módulo de análise.
    """
    # Metadados
    request_id: str = Field(..., description="ID da requisição original")
    timestamp: datetime = Field(..., description="Data/hora da geração")
    processing_time: float = Field(...,\
        description="Tempo de processamento em segundos")
    # Dados estruturados
    market_segments: Dict[str, MarketSegment] = Field(
        default_factory=dict,
        description="Segmentos de mercado identificados"
    )
    # Dados de tendências
    search_trends: Dict[str, SearchTrend] = Field(
        default_factory=dict,
        description="Tendências de busca por termo"
    )
    # Notícias e conteúdo
    news_articles: List[NewsArticle] = Field(
        default_factory=list,
        description="Notícias relevantes coletadas"
    )
    # Dados brutos processados (opcional)
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dados brutos processados (para referência)"
    )
    # Estatísticas de processamento
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Estatísticas sobre o processamento"
    )

    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_123456",
                "timestamp": "2023-10-01T12:30:45Z",
                "processing_time": 45.2,
                "market_segments": {
                    "pequenas_empresas": {
                        "name": "Pequenas Empresas",
                        "description": "Segmento de pequenas empresas",
                        "metrics": {
                            "faturamento_medio": {
                                "name": "Faturamento Médio",
                                "unit": "R$",
                                "current_value": {
                                    "value": 25000.50,
                                    "source": "ibge_sidra",
                                    "timestamp": "2023-09-01T00:00:00Z",
                                    "confidence": 0.95,
                                    "quality": "high"
                                },
                                "historical_values": [
                                    # Valores históricos...
                                ],
                                "trend": 2.5
                            }
                        }
                    }
                },
                "search_trends": {
                    "tecnologia pequenas empresas": {
                        "keyword": "tecnologia pequenas empresas",
                        "values": [
                            {"date": "2023-01-01T00:00:00Z", "value": 45},
                            # Mais valores...
                        ],
                        "related_queries": [
                            # Consultas relacionadas...
                        ]
                    }
                },
                "news_articles": [
                    {
                        "title": "Tecnologia impulsiona crescimento de pequenas empresas",
                        "source": "Portal de Notícias",
                        "url": "https://exemplo.com/noticia",
                        "published_at": "2023-09-28T10:30:00Z",
                        "summary": "Pequenas empresas que adotam tecnologia...",\
                        "sentiment": 0.8,
                        "keywords": ["tecnologia", "pequenas empresas",\
                            "crescimento"]
                    }
                ],
                "stats": {
                    "total_metrics": 15,
                    "total_news": 12,
                    "data_sources": ["ibge_sidra", "google_trends"],
                    "processing_notes": []
                }
            }
        }
