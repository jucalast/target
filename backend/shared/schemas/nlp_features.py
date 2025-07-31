"""
Esquemas para os recursos de NLP extraídos do texto.

Este módulo define os modelos Pydantic para estruturar os recursos extraídos
do processamento de linguagem natural, garantindo consistência na comunicação
entre os módulos do sistema.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class KeywordFeature(BaseModel):
    """Palavra-chave extraída do texto com seu escore."""
    keyword: str = Field(..., description="Palavra-chave extraída")
    score: float = Field(..., description="Pontuação da palavra-chave (0-1)")
    method: str = Field(..., description="Método de extração (ex: 'tfidf',\
        'lda')")

class EntityFeature(BaseModel):
    """Entidade nomeada extraída do texto."""
    text: str = Field(..., description="Texto da entidade")
    label: str = Field(..., description="Tipo da entidade (ex: 'PERSON',\
        'ORG')")
    start_char: int = Field(..., description="Posição inicial no texto")
    end_char: int = Field(..., description="Posição final no texto")

class TopicFeature(BaseModel):
    """Tópico extraído do texto com suas palavras-chave."""
    topic_id: int = Field(..., description="Identificador único do tópico")
    keywords: List[Dict[str, Any]] = Field(...,\
        description="Palavras-chave do tópico com escores")
    score: float = Field(..., description="Relevância do tópico no documento")

class EmbeddingFeature(BaseModel):
    """Embedding vetorial do texto."""
    model: str = Field(..., description="Modelo usado para gerar o embedding")
    vector: List[float] = Field(..., description="Vetor de embedding")
    dim: int = Field(..., description="Dimensão do vetor de embedding")

class NLPFeatures(BaseModel):
    """Estrutura contendo todos os recursos de NLP extraídos."""
    # Texto original e normalizado
    original_text: str = Field(...,\
        description="Texto original fornecido para análise")
    normalized_text: str = Field(..., description="Texto após normalização")
    # Recursos extraídos
    keywords: List[KeywordFeature] = Field(default_factory=list,\
        description="Palavras-chave extraídas")
    entities: List[EntityFeature] = Field(default_factory=list,\
        description="Entidades nomeadas identificadas")
    topics: List[TopicFeature] = Field(default_factory=list,\
        description="Tópicos identificados")
    embeddings: Dict[str, EmbeddingFeature] = Field(
        default_factory=dict,
        description="Dicionário de embeddings por modelo"
    )
    # Metadados
    language: str = Field("pt-BR", description="Idioma do texto analisado")
    processing_time: float = Field(...,\
        description="Tempo de processamento em segundos")

    class Config:
        schema_extra = {
            "example": {
                "original_text": "Exemplo de nicho: Mercado de tecnologia para pequenas empresas...",
                "normalized_text": "exemplo de nicho mercado de tecnologia para pequenas empresas",
                "keywords": [
                    {"keyword": "tecnologia", "score": 0.95, "method": "tfidf"},\
                    {"keyword": "pequenas empresas", "score": 0.87,\
                        "method": "tfidf"}
                ],
                "entities": [
                    {"text": "tecnologia", "label": "TECHNOLOGY",\
                        "start_char": 20, "end_char": 30}
                ],
                "topics": [
                    {
                        "topic_id": 0,
                        "keywords": [{"word": "tecnologia", "score": 0.8},\
                            {"word": "inovação", "score": 0.7}],
                        "score": 0.92
                    }
                ],
                "embeddings": {
                    "spacy": {
                        "model": "pt_core_news_lg",
                        "vector": [0.1, 0.2, 0.3, ...],
                        "dim": 300
                    },
                    "bert": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "vector": [0.4, 0.5, 0.6, ...],
                        "dim": 384
                    }
                },
                "language": "pt-BR",
                "processing_time": 1.23
            }
        }
