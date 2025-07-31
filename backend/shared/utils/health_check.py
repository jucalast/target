"""
Módulo de verificação de saúde (health checks) para serviços e dependências.

Este módulo fornece funções para verificar a saúde de diferentes componentes
do sistema, como bancos de dados, APIs externas e outros serviços.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from ..db.postgres import get_postgres
from ..db.mongodb import get_mongodb

logger = logging.getLogger(__name__)

class HealthCheckResult(BaseModel):
"""Modelo para o resultado de uma verificação de saúde."""
    status: str = Field(..., description="Status da verificação (healthy, \
        degraded, unhealthy)")
    component: str = Field(..., description="Nome do componente verificado")
    details: Dict[str, Any] = Field(default_factory=dict, \
        description="Detalhes adicionais")
    timestamp: datetime = Field(default_factory=datetime.utcnow, \
        description="Data e hora da verificação")

class HealthStatus(BaseModel):
"""Modelo para o status geral de saúde da aplicação."""
    status: str = Field(..., description="Status geral da aplicação (healthy, \
        degraded, unhealthy)")
    version: str = Field(..., description="Versão da aplicação")
    timestamp: datetime = Field(default_factory=datetime.utcnow, \
        description="Data e hora da verificação")
    checks: Dict[str, HealthCheckResult] = Field(default_factory=dict, \
        description="Resultados das verificações individuais")

def check_postgres_health() -> HealthCheckResult:
"""
    Verifica a saúde da conexão com o PostgreSQL.
    Returns:
    HealthCheckResult: Resultado da verificação de saúde
    """
    try:
    postgres = get_postgres()
        is_healthy = postgres.health_check()
        if is_healthy:
        return HealthCheckResult(
            status="healthy",
            component="postgresql",
            details={"message": "Conexão com o PostgreSQL estável"}
            )
        else:
        return HealthCheckResult(
            status="unhealthy",
            component="postgresql",
            details={"error": "Falha na conexão com o PostgreSQL"}
            )
    except Exception as e:
    logger.error(f"Erro ao verificar saúde do PostgreSQL: {str(e)}", \
            exc_info=True)
        return HealthCheckResult(
            status="unhealthy",
            component="postgresql",
            details={"error": str(e)}
        )

def check_mongodb_health() -> HealthCheckResult:
"""
    Verifica a saúde da conexão com o MongoDB.
    Returns:
    HealthCheckResult: Resultado da verificação de saúde
    """
    try:
    mongodb = get_mongodb()
        is_healthy = mongodb.health_check()
        if is_healthy:
        return HealthCheckResult(
            status="healthy",
            component="mongodb",
            details={"message": "Conexão com o MongoDB estável"}
            )
        else:
        return HealthCheckResult(
            status="unhealthy",
            component="mongodb",
            details={"error": "Falha na conexão com o MongoDB"}
            )
    except Exception as e:
    logger.error(f"Erro ao verificar saúde do MongoDB: {str(e)}", \
            exc_info=True)
        return HealthCheckResult(
            status="unhealthy",
            component="mongodb",
            details={"error": str(e)}
        )

def check_disk_usage() -> HealthCheckResult:
"""
    Verifica o uso do disco.
    Returns:
    HealthCheckResult: Resultado da verificação de uso do disco
    """
    try:
    import shutil

        total, used, free = shutil.disk_usage("/")
        usage_percent = (used / total) * 100
        details = {
        "total_gb": round(total / (2**30), 2),
        "used_gb": round(used / (2**30), 2),
        "free_gb": round(free / (2**30), 2),
        "usage_percent": round(usage_percent, 2)
        }
        if usage_percent > 90:
        status = "unhealthy"
            details["warning"] = "Uso do disco acima de 90%"
        elif usage_percent > 80:
        status = "degraded"
            details["warning"] = "Uso do disco acima de 80%"
        else:
        status = "healthy"
        return HealthCheckResult(
            status=status,
            component="disk",
            details=details
        )
    except Exception as e:
    logger.error(f"Erro ao verificar uso do disco: {str(e)}", \
            exc_info=True)
        return HealthCheckResult(
            status="unhealthy",
            component="disk",
            details={"error": str(e)}
        )

def check_memory_usage() -> HealthCheckResult:
"""
    Verifica o uso de memória.
    Returns:
    HealthCheckResult: Resultado da verificação de uso de memória
    """
    try:
    import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        details = {
        "rss_mb": round(memory_info.rss / (1024 * 1024), 2),
        "vms_mb": round(memory_info.vms / (1024 * 1024), 2),
        "percent": round(memory_percent, 2)
        }
        if memory_percent > 90:
        status = "unhealthy"
            details["warning"] = "Uso de memória acima de 90%"
        elif memory_percent > 80:
        status = "degraded"
            details["warning"] = "Uso de memória acima de 80%"
        else:
        status = "healthy"
        return HealthCheckResult(
            status=status,
            component="memory",
            details=details
        )
    except Exception as e:
    logger.error(f"Erro ao verificar uso de memória: {str(e)}", \
            exc_info=True)
        return HealthCheckResult(
            status="unhealthy",
            component="memory",
            details={"error": str(e), \
                "message": "psutil não instalado ou erro na leitura"}
        )

def get_health_status(version: str = "1.0.0") -> HealthStatus:
"""
    Obtém o status de saúde geral da aplicação.
    Args:
    version: Versão da aplicação
    Returns:
    HealthStatus: Status de saúde da aplicação e seus componentes
    """

    checks = {
    "postgresql": check_postgres_health(),
    "mongodb": check_mongodb_health(),
    "disk": check_disk_usage(),
    "memory": check_memory_usage()
    }

    statuses = [check.status for check in checks.values()]
    if "unhealthy" in statuses:
    overall_status = "unhealthy"
    elif "degraded" in statuses:
    overall_status = "degraded"
    else:
    overall_status = "healthy"
    return HealthStatus(
        status=overall_status,
        version=version,
        checks={name: check for name, check in checks.items()}
    )

def health_check_dependency(version: str = "1.0.0"):
"""
    Dependência FastAPI para verificação de saúde.
    Args:
    version: Versão da aplicação
    Returns:
    HealthStatus: Status de saúde da aplicação
    Raises:
    HTTPException: Se algum componente crítico estiver com problemas
    """
    health_status = get_health_status(version)

    critical_components = ["postgresql"]

    for component in critical_components:
    if component in health_status.checks and health_status.checks[component].status != "healthy":
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
        "status": health_status.status,
        "error": f"Componente crítico {component} não está saudável",
        "details": health_status.checks[component].details
                }
            )
    return health_status
