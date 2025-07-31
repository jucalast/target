"""
Rotas para verificação de saúde da aplicação.

Este módulo fornece endpoints para monitorar a saúde dos serviços e dependências
que compõem a aplicação.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from shared.utils.health_check import HealthStatus, health_check_dependency
from shared.utils.config import settings

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Serviço indisponível ou degradado"
        }
    },
)

@router.get(
    "",
    response_model=HealthStatus,
    summary="Verifica a saúde da aplicação",
    description="""
    Retorna o status de saúde da aplicação e suas dependências.

    - **Status possíveis**:
      - `healthy`: Tudo funcionando corretamente
      - `degraded`: Algum componente não essencial está com problemas
      - `unhealthy`: Algum componente crítico está com problemas
    """,
    response_description="Status de saúde da aplicação"
)
async def health_check():
    """
    Endpoint de verificação de saúde da aplicação.

    Retorna o status de saúde de todos os componentes monitorados,
    incluindo bancos de dados e recursos do sistema.
    """
    return health_check_dependency(settings.APP_VERSION)

@router.get(
    "/ready",
    summary="Verifica se a aplicação está pronta para receber requisições",
    description="""
    Verifica se todos os componentes críticos da aplicação estão prontos
    para receber requisições.

    Este endpoint é útil para verificações de readiness em orquestradores
    como Kubernetes.
    """,
    responses={
        status.HTTP_200_OK: {
            "description": "Aplicação pronta para receber requisições",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def readiness_check():
    """
    Endpoint de verificação de readiness.

    Retorna 200 apenas se todos os componentes críticos estiverem saudáveis.
    Caso contrário, retorna 503 Service Unavailable.
    """
    # A função health_check_dependency já levanta HTTPException se algum
    # componente crítico não estiver saudável
    health_status = health_check_dependency(settings.APP_VERSION)
    return {"status": "ok", "version": settings.APP_VERSION}

@router.get(
    "/live",
    summary="Verifica se a aplicação está em execução",
    description="""
    Verifica se a aplicação está em execução.

    Este endpoint não verifica dependências externas, apenas se o serviço
    está respondendo a requisições HTTP. Útil para verificações de liveness
    em orquestradores como Kubernetes.
    """,
    responses={
        status.HTTP_200_OK: {
            "description": "Aplicação em execução",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def liveness_check():
    """
    Endpoint de verificação de liveness.

    Retorna 200 se a aplicação estiver respondendo a requisições HTTP.
    """
    return {"status": "ok", "version": settings.APP_VERSION}
