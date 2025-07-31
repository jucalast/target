import pytest
import pandas as pd
from app.services.ibge.sidra_connector import SIDRAClient, SIDRAService, SIDRAQueryParams
from app.services.ibge.mappers import SIDRAMapper

# Fixture para o cliente (usada nos testes de baixo nível)
@pytest.fixture
def sidra_client():
    # Usar um diretório de cache específico para testes
    return SIDRAClient(cache_dir="test_cache", cache_ttl_days=1)

# Fixture para o serviço (usada nos testes de alto nível)
@pytest.fixture
def sidra_service(sidra_client):
    return SIDRAService(client=sidra_client)

# --- Testes do Mapper ---

def test_mapper_location_info():
    """Testa o mapeamento de informações de localização."""
    mapper = SIDRAMapper()
    
    # Testa a obtenção de informações para o Brasil
    info = mapper.get_location_info("brasil")
    assert info is not None
    assert info['code'] == '1'
    assert info['level'] == '1'
    
    # Testa uma sigla de UF
    info_sp = mapper.get_location_info("SP")
    assert info_sp is not None
    assert info_sp['code'] == '35'
    assert info_sp['level'] == '3'

def test_mapper_concept_mapping():
    """Testa o mapeamento de conceitos de negócio."""
    mapper = SIDRAMapper()
    
    # Supondo que você tenha um conceito 'populacao_total' no seu JSON
    # Substitua por um conceito que exista no seu arquivo sidra_mappings.json
    try:
        concept = mapper.get_concept_mapping("populacao_total")
        assert concept is not None
        assert "table_code" in concept
        assert "variables" in concept
    except ValueError as e:
        pytest.fail(f"O conceito de teste não foi encontrado no arquivo de mapeamento. Verifique se 'populacao_total' existe. Erro: {e}")

# --- Testes do Cliente (Baixo Nível) ---

def test_sidra_client_initialization(sidra_client):
    """Testa a inicialização do cliente SIDRA."""
    assert sidra_client is not None
    # Verifica se o método refatorado 'get_table' existe
    assert hasattr(sidra_client, 'get_table')

def test_get_table(sidra_client):
    """Testa a obtenção de dados de uma tabela SIDRA usando o método get_table."""
    # Tabela: 6407 - População por sexo e idade
    query = SIDRAQueryParams(
        table_code=6407,
        variables=[93],  # População
        location="Brasil", # Usar location é mais simples
        period="last 1"
    )

    # Faz a requisição
    result_df = sidra_client.get_table(query)
    
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    assert 'Valor' in result_df.columns

# --- Testes do Serviço (Alto Nível) ---

def test_get_population_by_sex_and_age(sidra_service):
    """Testa a obtenção de dados populacionais (método de alto nível)."""
    result_df = sidra_service.get_population_by_sex_and_age("Brasil")
    
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    # Verifica se as colunas esperadas estão presentes
    assert 'Sexo' in result_df.columns
    assert 'Grupo de idade' in result_df.columns

def test_get_income_distribution(sidra_service):
    """Testa a obtenção da distribuição de renda."""
    result_df = sidra_service.get_income_distribution("São Paulo")
    
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    assert 'Classes de rendimento mensal domiciliar per capita' in result_df.columns

def test_get_concept_data(sidra_service):
    """Testa a obtenção de dados por conceito de negócio."""
    # Substitua 'populacao_total' por um conceito que exista em seu arquivo
    try:
        result_df = sidra_service.get_concept_data(concept="populacao_total", location="Brasil")
        assert isinstance(result_df, pd.DataFrame)
        assert not result_df.empty
    except ValueError as e:
        pytest.fail(f"Falha ao buscar dados por conceito. Verifique o mapeamento. Erro: {e}")