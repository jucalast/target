from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
from pathlib import Path

class Settings(BaseSettings):
    # Configurações do banco de dados
    DATABASE_URL: str = "sqlite:///./test.db"
    POSTGRESQL_URL: str = "postgresql://postgres:postgres@localhost:5432/target_db"
    
    # Configurações do pool de conexão do PostgreSQL
    POSTGRESQL_POOL_SIZE: int = 5
    POSTGRESQL_MAX_OVERFLOW: int = 10
    POSTGRESQL_POOL_TIMEOUT: int = 30  # segundos
    POSTGRESQL_POOL_RECYCLE: int = 3600  # segundos (1 hora)
    POSTGRESQL_POOL_PRE_PING: bool = True
    POSTGRESQL_ECHO: bool = False  # Log de queries SQL
    
    # Configurações de autenticação
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Configurações do IBGE/SIDRA
    IBGE_SIDRA_BASE_URL: str = "https://apisidra.ibge.gov.br/values"
    
    # Configurações de logging
    LOG_LEVEL: str = "INFO"
    
    # Configurações de ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        # Carrega variáveis de ambiente de um arquivo .env se existir
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

    def get_postgres_engine_kwargs(self) -> Dict[str, Any]:
        """Retorna os argumentos de configuração do engine do SQLAlchemy."""
        return {
            "pool_size": self.POSTGRESQL_POOL_SIZE,
            "max_overflow": self.POSTGRESQL_MAX_OVERFLOW,
            "pool_timeout": self.POSTGRESQL_POOL_TIMEOUT,
            "pool_recycle": self.POSTGRESQL_POOL_RECYCLE,
            "pool_pre_ping": self.POSTGRESQL_POOL_PRE_PING,
            "echo": self.POSTGRESQL_ECHO
        }

# Instância global das configurações
settings = Settings()

# Configurações específicas para diferentes ambientes
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
    settings.POSTGRESQL_ECHO = False
    settings.POSTGRESQL_POOL_PRE_PING = True

# Garante que as URLs de banco de dados estejam no formato correto
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)

if settings.POSTGRESQL_URL and settings.POSTGRESQL_URL.startswith("postgres://"):
    settings.POSTGRESQL_URL = settings.POSTGRESQL_URL.replace("postgres://", "postgresql://", 1)
