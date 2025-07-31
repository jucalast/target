"""
Esquemas Pydantic para a API de integração com o IBGE.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class IBGEQueryBase(BaseModel):
    """Base para consultas ao IBGE"""
    concept: str = Field(..., description="Conceito a ser consultado (ex: 'jovens_adultos', 'consumo_cultural')")
    location: Optional[str] = Field(
        None, 
        description="Localização (sigla do estado ou 'brasil' para dados nacionais)"
    )
    period: str = Field(
        "last", 
        description="Período de referência no formato AAAATT ou 'last' para o mais recente"
    )

class IBEResult(BaseModel):
    """Resultado de uma consulta ao IBGE"""
    concept: str
    location: str
    period: str
    data: List[Dict[str, Any]] = Field(..., description="Dados retornados pela consulta")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais sobre a consulta"
    )

class IBGEDemographicQuery(IBGEQueryBase):
    """Consulta para dados demográficos"""
    age_range: Optional[tuple[int, int]] = Field(
        None,
        description="Faixa etária (mínimo, máximo)",
        example=[18, 39]
    )
    education_level: Optional[str] = Field(
        None,
        description="Nível de instrução (ex: 'superior_completo')"
    )

class IBGEDemographicResult(IBEResult):
    """Resultado de uma consulta demográfica"""
    age_range: Optional[tuple[int, int]] = None
    education_level: Optional[str] = None
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resumo estatístico dos dados"
    )
