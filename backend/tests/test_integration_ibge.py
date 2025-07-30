"""
Testes de integração para o conector IBGE.
"""
import pytest
from pathlib import Path
from typing import Dict, Any
import json

from app.services.ibge.sidra_connector import SIDRAClient, SIDRAService, SIDRAMapper

# Constantes para testes
TEST_CACHE_DIR = Path("./test_cache_integration")
TEST_MAPPING_FILE = Path("test_mappings.json")

# Dados de teste para o mapeamento
test_mapping_data = {
    "concepts": {
        "test_concept": {
            "table": "5918",
            "variables": ["5932"],
            "classifications": {
                "1": ["1"],
                "2": ["1", "2"]
            },
            "description": "Exemplo de conceito para testes"
        }
    },
    "territories": {
        "test_location": "1"
    },
    "metadata": {
        "test": "Dados de teste"
    }
}

@pytest.fixture(scope="module")
def test_mapping_file():
    """Cria um arquivo de mapeamento temporário para testes."""
    # Criar diretório de teste se não existir
    TEST_MAPPING_FILE.parent.mkdir(exist_ok=True, parents=True)
    
    # Salvar dados de teste no arquivo
    with open(TEST_MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_mapping_data, f, ensure_ascii=False, indent=2)
    
    yield TEST_MAPPING_FILE
    
    # Limpar após o teste
    if TEST_MAPPING_FILE.exists():
        TEST_MAPPING_FILE.unlink()

@pytest.fixture(scope="module")
def sidra_client():
    """Cliente SIDRA para testes."""
    # Garantir que o diretório de cache existe
    TEST_CACHE_DIR.mkdir(exist_ok=True)
    
    client = SIDRAClient(
        cache_enabled=True,
        cache_dir=TEST_CACHE_DIR,
        cache_ttl_days=1
    )
    
    yield client
    
    # Limpar após o teste
    if TEST_CACHE_DIR.exists():
        for file in TEST_CACHE_DIR.glob("*"):
            file.unlink()
        TEST_CACHE_DIR.rmdir()

def test_sidra_mapper_initialization(test_mapping_file):
    """Testa a inicialização do SIDRAMapper."""
    mapper = SIDRAMapper(mapping_file=str(test_mapping_file))
    assert mapper is not None
    assert isinstance(mapper.mappings, dict)
    assert "concepts" in mapper.mappings
    assert "territories" in mapper.mappings

def test_get_territory_code(test_mapping_file):
    """Testa a obtenção de códigos territoriais."""
    mapper = SIDRAMapper(mapping_file=str(test_mapping_file))
    
    # Testar com localização existente
    assert mapper.get_territory_code("test_location") == "1"
    
    # Testar com localização inexistente (deve retornar o padrão "1" para Brasil)
    assert mapper.get_territory_code("nonexistent_location") == "1"

def test_get_concept_mapping(test_mapping_file):
    """Testa a obtenção de mapeamento de conceitos."""
    mapper = SIDRAMapper(mapping_file=str(test_mapping_file))
    
    # Testar com conceito existente
    concept = mapper.get_concept_mapping("test_concept")
    assert concept is not None
    assert concept["table"] == "5918"
    assert "variables" in concept
    assert "classifications" in concept
    
    # Testar com conceito inexistente
    assert mapper.get_concept_mapping("nonexistent_concept") == {}

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sidra_client_get_table(sidra_client):
    """
    Testa a obtenção de dados de uma tabela SIDRA.
    
    Este é um teste de integração real com a API do IBGE.
    """
    # Dados de teste para a PNAD Contínua (tabela 5918 - Rendimento de todas as fontes)
    table_code = "5918"
    variables = ["5932"]  # Rendimento médio real habitual do trabalho principal
    classifications = {
        "1": ["1"],        # 1=1.0 - Pessoas de 14 anos ou mais de idade
        "2": ["1", "2"]    # 1=Homem, 2=Mulher
    }
    
    # Fazer a requisição
    df = await sidra_client.get_table(
        table_code=table_code,
        variables=variables,
        classifications=classifications,
        territory_code="1",  # Brasil
        period="last"       # Último período disponível
    )
    
    # Verificar resultados
    assert df is not None
    assert not df.empty
    assert len(df) > 0
    
    # Verificar se as colunas esperadas estão presentes
    expected_columns = ["D1C", "D2C", "D3C", "V"]
    for col in expected_columns:
        assert col in df.columns

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sidra_service_get_concept_data(test_mapping_file):
    """
    Testa a obtenção de dados por conceito usando o SIDRAService.
    
    Este é um teste de integração real com a API do IBGE.
    """
    # Criar um cliente com o arquivo de mapeamento de teste
    client = SIDRAClient(cache_enabled=False)
    client.mapper = SIDRAMapper(mapping_file=str(test_mapping_file))
    
    service = SIDRAService(client=client)
    
    # Testar com um conceito existente
    df = await service.get_concept_data(
        concept="test_concept",
        location="test_location",
        period="last"
    )
    
    # Verificar resultados
    assert df is not None
    assert not df.empty
    assert len(df) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sidra_service_get_demographic_profile():
    """
    Testa a obtenção de perfil demográfico.
    
    Este é um teste de integração real com a API do IBGE.
    """
    service = SIDRAService()
    
    # Testar com parâmetros básicos
    result = await service.get_demographic_profile(
        age_range=(18, 39),
        location="brasil",
        period="last"
    )
    
    # Verificar resultados
    assert result is not None
    assert isinstance(result, dict)
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0

# Executar os testes com: pytest tests/test_integration_ibge.py -v --log-cli-level=INFO
