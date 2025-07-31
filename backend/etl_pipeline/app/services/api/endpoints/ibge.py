"""
Endpoints para consulta de dados do IBGE.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import logging

from etl_pipeline.app.services.extractors.ibge.sidra_connector import SIDRAService
from shared.schemas.ibge import (
    IBEResult,
    IBGEQueryBase,
    IBGEDemographicQuery,
    IBGEDemographicResult
)
from shared.db.database import get_db

# Configuração de logging
logger = logging.getLogger(__name__)

# Roteador para os endpoints do IBGE
router = APIRouter()

# Inicializa o serviço SIDRA
sidra_service = SIDRAService()

@router.post(
    "/query",
    response_model=IBEResult,
    status_code=status.HTTP_200_OK,
    summary="Consulta genérica ao IBGE",
    description="""
    Realiza uma consulta genérica ao IBGE com base em um conceito pré-mapeado.

    Conceitos disponíveis:
    - jovens_adultos: Dados demográficos de jovens adultos (18-39 anos)
    - consumo_cultural: Dados de despesas com cultura e lazer
    - posse_bens: Dados sobre posse de bens duráveis
    - condicoes_vida: Dados sobre condições de vida e bem-estar
    """
)


def query_ibge(
    query: IBGEQueryBase,
    db: Session = Depends(get_db)
) -> IBEResult:
    """
    Endpoint para consulta genérica ao IBGE.
    """
    try:
        logger.info(f"Consultando IBGE para conceito: {query.concept}")

        # Obter dados do serviço SIDRA
        df = sidra_service.get_concept_data(
            concept=query.concept,
            location=query.location,
            period=query.period
        )

        # Converter DataFrame para lista de dicionários
        data = df.to_dict(orient='records')

        return IBEResult(
            concept=query.concept,
            location=query.location or "brasil",
            period=query.period,
            data=data,
            metadata={
                "source": "IBGE/SIDRA",
                "concept": query.concept,
                "row_count": len(data)
            }
        )

    except ValueError as e:
        logger.error(f"Erro na consulta ao IBGE: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro interno ao consultar IBGE: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição"
        )

@router.post(
    "/demographic",
    response_model=IBGEDemographicResult,
    status_code=status.HTTP_200_OK,
    summary="Consulta demográfica ao IBGE",
    description="""
    Realiza uma consulta demográfica ao IBGE com filtros específicos.
    """
)


def query_demographic(
    query: IBGEDemographicQuery,
    db: Session = Depends(get_db)
) -> IBGEDemographicResult:
    """
    Endpoint para consulta demográfica ao IBGE.
    """
    try:
        logger.info(f"Consultando dados demográficos: {query.dict()}")

        # Obter perfil demográfico do serviço SIDRA
        # NOTA: O método get_demographic_profile não existia. Adicionei uma
        # implementação base no arquivo sidra_connector.py (veja abaixo).
        # A chamada agora é síncrona.
        result = sidra_service.get_demographic_profile(
            age_range=query.age_range,
            education_level=query.education_level,
            location=query.location,
            period=query.period
        )

        return IBGEDemographicResult(
            concept="demographic_profile",
            location=query.location or "brasil",
            period=query.period,
            data=result.get("data", []),
            age_range=query.age_range,
            education_level=query.education_level,
            summary=result.get("summary", {}),
            metadata={
                "source": "IBGE/SIDRA",
                "query": query.dict(),
                "row_count": len(result.get("data", []))
            }
        )

    except ValueError as e:
        logger.error(f"Erro na consulta demográfica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro interno ao consultar dados demográficos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição"
        )
