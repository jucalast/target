# backend/app/schemas/analysis.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any

# ==============================================================================
# Schema para a Criação de uma Nova Análise (Entrada da API)
# ==============================================================================
class AnalysisCreate(BaseModel):
    """
    Schema para validar os dados de entrada para a criação de uma nova análise.
    Este é o contrato que o endpoint de análise esperará receber no corpo da requisição.
    """
    niche: str = Field(
       ...,
        min_length=3,
        max_length=100,
        title="Nicho de Mercado",
        description="O nicho de mercado do negócio ou produto a ser analisado."
    )
    description: str = Field(
       ...,
        min_length=100,
        title="Descrição Detalhada",
        description="Descrição detalhada do negócio ou produto, com no mínimo 100 caracteres para garantir uma análise de qualidade."
    )

# ==============================================================================
# Schema para Leitura de uma Análise (Saída da API)
# ==============================================================================
class AnalysisRead(BaseModel):
    """
    Schema usado para retornar os dados de uma análise processada pela API.
    Representa a estrutura de dados de saída da etapa de extração de características.
    """
    id: int
    user_id: int
    niche: str
    description: str
    normalized_text: str
    keywords: List[str]
    entities: List[Dict[str, Any]]
    embedding: List[float]
    created_at: datetime

    class Config:
        """
        Configuração do Pydantic para permitir o mapeamento direto de um
        modelo ORM (SQLAlchemy) para este schema.
        """
        from_attributes = True
