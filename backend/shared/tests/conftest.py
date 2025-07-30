"""
Configuração para testes de integração com o IBGE.
"""
import os
import pytest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api_gateway.app.main import app
from shared.db.postgres import Base
from shared.db.database import get_db

# Configuração do banco de dados de teste
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar o banco de dados de teste
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Sobrescreve a dependência do banco de dados para testes."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def test_app():
    """
    Configura o aplicativo FastAPI para testes.
    """
    # Sobrescrever a dependência do banco de dados
    app.dependency_overrides[get_db] = override_get_db
    
    # Configurar diretório de cache para testes
    test_cache_dir = Path("./test_cache")
    os.environ["SIDRA_CACHE_DIR"] = str(test_cache_dir.absolute())
    
    # Garantir que o diretório de cache existe
    test_cache_dir.mkdir(exist_ok=True)
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpar após os testes
    if test_cache_dir.exists():
        for file in test_cache_dir.glob("*"):
            file.unlink()
        test_cache_dir.rmdir()
    
    # Limpar sobrescritas
    app.dependency_overrides = {}

@pytest.fixture(scope="module")
def ibge_client():
    """
    Cliente para testes de integração com a API do IBGE.
    """
    from app.services.ibge.sidra_connector import SIDRAClient
    
    # Usar um diretório de cache temporário para testes
    test_cache_dir = Path("./test_cache_sidra")
    
    # Garantir que o diretório existe
    test_cache_dir.mkdir(exist_ok=True)
    
    client = SIDRAClient(
        cache_enabled=True,
        cache_dir=test_cache_dir,
        cache_ttl_days=1
    )
    
    yield client
    
    # Limpar após os testes
    if test_cache_dir.exists():
        for file in test_cache_dir.glob("*"):
            file.unlink()
        test_cache_dir.rmdir()
