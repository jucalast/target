"""
Esquemas para dados de notícias.

Este módulo define os modelos Pydantic para representar notícias e fontes de notícias
no sistema, garantindo validação e documentação consistente dos dados.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator

class NewsSourceType(str, Enum):
"""Tipos de fontes de notícias suportadas."""
    NEWSPAPER = "newspaper"
    MAGAZINE = "magazine"
    NEWS_AGENCY = "news_agency"
    GOVERNMENT = "government"
    BLOG = "blog"
    OTHER = "other"

class NewsCategory(str, Enum):
"""Categorias de notícias suportadas."""
    POLITICS = "politics"
    ECONOMY = "economy"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    WORLD = "world"
    BRAZIL = "brazil"
    GENERAL = "general"

class NewsSource(BaseModel):
"""Representa uma fonte de notícias."""
    id: Optional[str] = Field(
        None,
        description="Identificador único da fonte de notícias"
    )
    name: str = Field(
        ...,
        description="Nome da fonte de notícias"
    )
    domain: str = Field(
        ...,
        description="Domínio da fonte de notícias (\
            ex: agenciabrasil.ebc.com.br)"
    )
    url: HttpUrl = Field(
        ...,
        description="URL base da fonte de notícias"
    )
    type: NewsSourceType = Field(
        default=NewsSourceType.OTHER,
        description="Tipo da fonte de notícias"
    )
    language: str = Field(
        default="pt-BR",
        description="Código de idioma da fonte (padrão: pt-BR)"
    )
    country: str = Field(
        default="BR",
        description="Código do país da fonte (padrão: BR)"
    )
    description: Optional[str] = Field(
        None,
        description="Descrição da fonte de notícias"
    )
    logo_url: Optional[HttpUrl] = Field(
        None,
        description="URL do logotipo da fonte de notícias"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais sobre a fonte"
    )

    class Config:
    schema_extra = {
    "example": {
    "id": "agenciabrasil",
    "name": "Agência Brasil",
    "domain": "agenciabrasil.ebc.com.br",
    "url": "https://agenciabrasil.ebc.com.br",
    "type": "news_agency",
    "language": "pt-BR",
    "country": "BR",
    "description": "Agência pública de notícias do Brasil",
    "logo_url": "https://agenciabrasil.ebc.com.br/static/logo-\
                    abr.png"
            }
        }

class NewsArticle(BaseModel):
"""Representa um artigo de notícia."""
    id: Optional[str] = Field(
        None,
        description="Identificador único do artigo"
    )
    title: str = Field(
        ...,
        max_length=500,
        description="Título da notícia"
    )
    content: str = Field(
        ...,
        description="Conteúdo completo da notícia"
    )
    url: HttpUrl = Field(
        ...,
        description="URL canônica da notícia"
    )
    source: NewsSource = Field(
        ...,
        description="Fonte da notícia"
    )
    published_at: datetime = Field(
        ...,
        description="Data e hora de publicação da notícia"
    )
    author: Optional[str] = Field(
        None,
        description="Autor(a) da notícia, se disponível"
    )
    category: Optional[NewsCategory] = Field(
        None,
        description="Categoria principal da notícia"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Lista de categorias/tags da notícia"
    )
    language: str = Field(
        default="pt-BR",
        description="Código de idioma da notícia (padrão: pt-BR)"
    )
    search_query: Optional[str] = Field(
        None,
        description="Termo de busca que retornou esta notícia, se aplicável"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Palavras-chave extraídas da notícia"
    )
    summary: Optional[str] = Field(
        None,
        description="Resumo gerado automaticamente do conteúdo"
    )
    sentiment_score: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Pontuação de sentimento entre -1 (negativo) e 1 (\
            positivo)"
    )
    entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Entidades nomeadas extraídas do texto (pessoas, \
            organizações, locais, etc.)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais sobre a notícia"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data e hora em que o registro foi criado no sistema"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data e hora da última atualização do registro"
    )

    class Config:
        schema_extra = {
        "example": {
        "title": "IBGE prevê safra recorde de grãos em 2023",
        "content": "O Instituto Brasileiro de Geografia e Estatística (IBGE) divulgou...",
        "url": "https://agenciabrasil.ebc.com.br/economia/noticia/2023-01/ibge-preve-safra-recorde-graos-2023",
        "source": {
        "name": "Agência Brasil",
        "domain": "agenciabrasil.ebc.com.br",
        "url": "https://agenciabrasil.ebc.com.br",
        "type": "news_agency"
                },
                "published_at": "2023-01-15T10:30:00-03:00",
                "author": "Repórter da Agência Brasil",
                "category": "economy",
                "categories": ["economy", "agriculture", "ibge"],
                "language": "pt-BR",
                "search_query": "previsão safra grãos 2023",
                "keywords": ["IBGE", "safra recorde", "grãos", "agricultura", \
                    "previsão"],
                    "sentiment_score": 0.75,
                    "metadata": {
                    "word_count": 450,
                    "extracted_at": "2023-01-15T11:05:23Z",
                    "has_image": True,
                    "image_url": "https://agenciabrasil.ebc.com.br/sites/\
                        default/files/thumbnails/image/safra_graos.jpg"
                }
            }
        }
        @validator('categories', pre=True, always=True)

    def set_categories(cls, v, values):
    """Garante que a categoria principal esteja na lista de categorias."""
        if 'category' in values and values['category'] and \
            values['category'] not in v:
            return [values['category']] + v
        return v or []

class NewsSearchResult(BaseModel):
"""Resultado de uma busca por notícias."""
        query: str = Field(
        ...,
        description="Termo de busca original"
        )
        total_results: int = Field(
        ...,
        description="Número total de resultados encontrados"
        )
        page: int = Field(
        default=1,
        description="Número da página atual"
        )
        page_size: int = Field(
        default=10,
        description="Número de itens por página"
        )
        articles: List[NewsArticle] = Field(
        default_factory=list,
        description="Lista de artigos de notícias"
        )
        facets: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Facetas para filtragem (ex: por fonte, categoria, data)"
        )

    class Config:
        schema_extra = {
        "example": {
        "query": "economia brasileira",
        "total_results": 124,
        "page": 1,
        "page_size": 10,
        "articles": [],
        "facets": {
        "source": {"Agência Brasil": 45, "IBGE": 32, \
                        "Governo Federal": 47},
                        "category": {"economy": 85, "politics": 23, "business": 16}, \
                    "published_at": {"2023-01": 45, "2022-12": 56, \
                        "2022-11": 23}
                }
            }
        }
