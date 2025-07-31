"""
Esquemas para os parâmetros de entrada do ETL.

Este módulo define os modelos Pydantic para estruturar os parâmetros de entrada
do pipeline ETL, garantindo consistência na comunicação entre os módulos.
"""
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .nlp_features import NLPFeatures

class IBGETableQuery(BaseModel):
    """Parâmetros para consulta a uma tabela específica do IBGE SIDRA."""
    table_code: str = Field(..., description="Código da tabela SIDRA")
    variables: List[str] = Field(..., description="Lista de códigos de variáveis")
    classifications: Dict[str, Union[str, List[str]]] = Field(
        default_factory=dict,
        description="Classificações para filtrar os dados"
    )
    location: str = Field("Brasil", description="Localidade para os dados")
    period: str = Field("last", description="Período dos dados (ex: 'last', '2022')")

class GoogleTrendsQuery(BaseModel):
    """Parâmetros para consulta ao Google Trends."""
    keywords: List[str] = Field(..., description="Termos de busca")
    timeframe: str = Field("today 12-m", description="Período de tempo para a análise")
    geo: str = Field("BR", description="Localização geográfica")
    gprop: str = Field("web", description="Fonte dos dados (web, news, images, youtube)")

class NewsScrapingQuery(BaseModel):
    """Parâmetros para coleta de notícias."""
    keywords: List[str] = Field(..., description="Termos de busca para as notícias")
    sources: Optional[List[str]] = Field(
        None,
        description="Fontes de notícias específicas (opcional)"
    )
    max_articles: int = Field(20, description="Número máximo de artigos para coletar")
    timeframe_days: int = Field(30, description="Número máximo de dias para trás")

class ETLParameters(BaseModel):
    """
    Parâmetros para execução do pipeline ETL.
    
    Esta estrutura define os parâmetros que serão passados do módulo de NLP
    para o módulo ETL, contendo todas as informações necessárias para a coleta
    e processamento de dados de mercado.
    """
    # Identificação e metadados
    request_id: str = Field(..., description="ID único da requisição")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Data/hora da requisição")
    
    # Dados de entrada do usuário
    user_input: Dict[str, Any] = Field(
        ...,
        description="Entrada original do usuário (nichos, descrições, etc.)"
    )
    
    # Recursos de NLP extraídos
    nlp_features: NLPFeatures = Field(..., description="Recursos de NLP extraídos do texto")
    
    # Parâmetros para coleta de dados
    ibge_queries: List[IBGETableQuery] = Field(
        default_factory=list,
        description="Lista de consultas a tabelas do IBGE SIDRA"
    )
    google_trends_queries: List[GoogleTrendsQuery] = Field(
        default_factory=list,
        description="Lista de consultas ao Google Trends"
    )
    news_queries: Optional[NewsScrapingQuery] = Field(
        None,
        description="Parâmetros para coleta de notícias setoriais"
    )
    
    # Configurações de processamento
    cache_enabled: bool = Field(True, description="Habilita o uso de cache")
    max_retries: int = Field(3, description="Número máximo de tentativas para cada requisição")
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_123456",
                "timestamp": "2023-10-01T12:00:00Z",
                "user_input": {
                    "niche": "Tecnologia para pequenas empresas",
                    "description": "Soluções de automação para pequenos negócios..."
                },
                "nlp_features": {
                    # Estrutura definida em nlp_features.NLPFeatures
                },
                "ibge_queries": [
                    {
                        "table_code": "6401",
                        "variables": ["2979", "2980"],
                        "classifications": {"200": "1933"},
                        "location": "Brasil",
                        "period": "last"
                    }
                ],
                "google_trends_queries": [
                    {
                        "keywords": ["tecnologia pequenas empresas", "automação comércio"],
                        "timeframe": "today 12-m",
                        "geo": "BR",
                        "gprop": "web"
                    }
                ],
                "news_queries": {
                    "keywords": ["tecnologia", "pequenas empresas"],
                    "sources": ["g1", "valor"],
                    "max_articles": 20,
                    "timeframe_days": 30
                },
                "cache_enabled": True,
                "max_retries": 3
            }
        }
