"""
Testes para o módulo SIDRAClient.

Este módulo contém testes para a classe SIDRAClient, que é responsável por
fazer requisições à API SIDRA do IBGE.
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import pytest
import pandas as pd
import pandas.testing as pdt
from etl_pipeline.app.services.ibge.sidra_connector import SIDRAClient, SIDRAQueryParams, SidraApiError
from etl_pipeline.app.services.ibge.mappers import SIDRAMapper

# Constantes para testes
TEST_CACHE_DIR = "./test_cache"
TEST_TABLE_CODE = "6401"  # PNAD Contínua - Tabela de exemplo

# Mock para o SIDRAMapper
@pytest.fixture


def mock_mapper():
    """Retorna um mock do SIDRAMapper com dados de teste."""
    mapper = MagicMock(spec=SIDRAMapper)

    # Configura o mock para retornar informações de tabela simuladas
    mapper.get_table_info.return_value = {
        'code': '6401',
        'name': 'PNAD Contínua',
        'variables': [
            {'code': '93', 'name': 'População'},
        ],
        'classifications': [
            {'id': 'C2', 'name': 'Sexo', 'categories': [
                {'code': '1', 'name': 'Homens'},
                {'code': '2', 'name': 'Mulheres'}
            ]}
        ]
    }

    return mapper

# Fixture para o cliente SIDRA com cache em diretório temporário
@pytest.fixture


def sidra_client(mock_mapper):
    """Retorna uma instância de SIDRAClient configurada para testes."""
    # Cria um diretório temporário para cache
    cache_dir = Path(TEST_CACHE_DIR)
    cache_dir.mkdir(exist_ok=True)

    # Configura o cliente com cache ativado e TTL curto para testes
    client = SIDRAClient(
        cache_enabled=True,
        cache_dir=cache_dir,
        cache_ttl_days=1/24,  # 1 hora de TTL
        max_retries=2,
        retry_wait_min=0.1,
        retry_wait_max=0.5
    )

    # Substitui o mapper por um mock
    client.mapper = mock_mapper

    yield client

    # Limpa o cache após os testes
    for f in cache_dir.glob("*"):
        try:
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                f.rmdir()
        except Exception:
            pass

    try:
        cache_dir.rmdir()
    except Exception:
        pass

# Fixture para dados de resposta simulados
@pytest.fixture


def mock_sidra_response():
    """Retorna uma resposta simulada da API SIDRA."""
    return [
        {"Coluna1": "Cabeçalho1", "Coluna2": "Cabeçalho2", "Valor": "Valor"},
        {"Coluna1": "Dado1", "Coluna2": "Dado2", "Valor": "100,50"},
        {"Coluna1": "Dado3", "Coluna2": "Dado4", "Valor": "200,75"}
    ]

# Fixture para parâmetros de consulta de teste
@pytest.fixture


def test_query_params():
    """Retorna parâmetros de consulta para testes."""
    return SIDRAQueryParams(
        table_code=TEST_TABLE_CODE,
        variables=[93],  # População
        classifications={"C2": [1, 2]},  # Sexo: 1=Masculino, 2=Feminino
        period="2023",
        location="Brasil"
    )

# Testes para SIDRAClient


class TestSIDRAClient:
    """Testes para a classe SIDRAClient."""


    def test_get_cache_key_consistente(self, sidra_client, test_query_params):
        """Testa se a geração da chave de cache é consistente."""
        key1 = sidra_client._get_cache_key(test_query_params)
        key2 = sidra_client._get_cache_key(test_query_params)
        assert key1 == key2

        # Modifica um parâmetro e verifica se a chave muda
        modified_params = test_query_params.copy()
        modified_params.period = "2022"
        key3 = sidra_client._get_cache_key(modified_params)
        assert key1 != key3


    def test_save_and_retrieve_from_cache(self, sidra_client, test_query_params, tmp_path):
        """Testa o salvamento e recuperação de dados do cache."""
        # Dados de teste
        test_data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        cache_key = "test_cache_key"

        # Salva no cache
        sidra_client._save_to_cache(cache_key, test_data)

        # Verifica se o arquivo foi criado
        cache_file = Path(sidra_client.cache_dir) / f"{cache_key}.parquet"
        assert cache_file.exists()

        # Recupera do cache
        cached_data = sidra_client._get_from_cache(cache_key)

        # Verifica se os dados são iguais
        pdt.assert_frame_equal(test_data, cached_data)

    @patch('app.services.ibge.sidra_connector.sidrapy.get_table')


    def test_get_table_success(self, mock_get_table, sidra_client, test_query_params):
        """Testa uma requisição bem-sucedida à API SIDRA."""
        # Configura o mock para retornar dados no formato esperado pelo _process_sidra_response
        mock_response = [
            {"Coluna1": "Cabeçalho1", "Coluna2": "Cabeçalho2", "V": "Valor"},
            {"Coluna1": "Dado1", "Coluna2": "Dado2", "V": "100,50"},
            {"Coluna1": "Dado3", "Coluna2": "Dado4", "V": "200,75"}
        ]
        mock_get_table.return_value = mock_response

        # Faz a requisição
        result = sidra_client.get_table(test_query_params)

        # Verifica se a função foi chamada com os parâmetros corretos
        mock_get_table.assert_called_once()

        # Verifica o resultado
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # 2 linhas de dados
        assert "Valor" in result.columns  # A coluna V deve ser renomeada para Valor

        # Verifica se os valores numéricos foram convertidos corretamente
        assert result["Valor"].dtype == float
        assert result["Valor"].iloc[0] == 100.5  # 100,50 convertido para float

    @patch('app.services.ibge.sidra_connector.sidrapy.get_table')


    def test_get_table_with_retry(self, mock_get_table, sidra_client, test_query_params):
        """Testa o mecanismo de retry em caso de falha na requisição."""
        # Formato esperado pela _process_sidra_response:
        # - Primeiro item: dicionário com cabeçalhos
        # - Itens seguintes: dicionários com os dados
        success_response = [
            {"D1C": "D1C", "D2C": "D2C", "V": "V", "D1N": "D1N", "D2N": "D2N"},  # Cabeçalho
            {"D1C": "1", "D2C": "1", "V": "100,50", "D1N": "Brasil", "D2N": "Teste"}  # Dados
        ]

        # Configura o mock para levantar exceção duas vezes e depois retornar sucesso
        from requests.exceptions import ConnectionError as RequestsConnectionError
        mock_get_table.side_effect = [
            RequestsConnectionError("Erro de conexão"),
            RequestsConnectionError("Erro de conexão"),
            success_response
        ]

        # A requisição deve ser bem-sucedida após duas tentativas
        result = sidra_client.get_table(test_query_params)

        # Verifica se foram feitas 3 chamadas (2 falhas + 1 sucesso)
        assert mock_get_table.call_count == 3

        # Verifica o resultado
        assert not result.empty
        assert "Valor" in result.columns
        assert result["Valor"].iloc[0] == 100.5  # Verifica a conversão de "100,50" para float

    @patch('app.services.ibge.sidra_connector.sidrapy.get_table')


    def test_get_table_empty_response(self, mock_get_table, sidra_client, test_query_params):
        """Testa o tratamento de resposta vazia da API."""
        # Configura o mock para retornar uma resposta vazia
        mock_get_table.return_value = []

        # Deve lançar uma exceção específica
        with pytest.raises(SidraApiError) as exc_info:
            sidra_client.get_table(test_query_params)

        # Verifica se a exceção foi lançada com o código de erro correto
        assert exc_info.value.error_code == "NO_DATA_RETURNED"

        # Verifica se a mensagem de erro contém o código da tabela
        assert str(test_query_params.table_code) in str(exc_info.value)

    @patch('app.services.ibge.sidra_connector.sidrapy.get_table')


    def test_get_table_caching(self, mock_get_table, sidra_client, test_query_params, mock_sidra_response):
        """Testa se o cache está funcionando corretamente."""
        # Configura o mock para retornar dados simulados
        mock_get_table.return_value = mock_sidra_response

        # Primeira chamada - deve chamar a API
        result1 = sidra_client.get_table(test_query_params)
        assert mock_get_table.call_count == 1

        # Segunda chamada - deve usar o cache
        result2 = sidra_client.get_table(test_query_params)
        assert mock_get_table.call_count == 1  # Ainda 1 chamada à API

        # Verifica se os resultados são iguais
        pdt.assert_frame_equal(result1, result2)

        # Verifica se os dados estão no cache
        cache_key = sidra_client._get_cache_key(test_query_params)
        cached_data = sidra_client._get_from_cache(cache_key)
        assert cached_data is not None
        pdt.assert_frame_equal(result1, cached_data)

# Testes para SIDRAQueryParams


class TestSIDRAQueryParams:
    """Testes para a classe SIDRAQueryParams."""


    def test_valid_query_params(self):
        """Testa a criação de parâmetros válidos."""
        params = SIDRAQueryParams(
            table_code=6401,
            variables=[93],
            classifications={"C2": [1, 2]},
            period="2023",
            location="Brasil"
        )

        # Verifica os valores convertidos
        assert params.table_code == "6401"
        assert params.variables == ["93"]

        # Verifica as classificações (a chave deve ser convertida para maiúsculas)
        assert "C2" in params.classifications
        assert params.classifications["C2"] == ["1", "2"]

        # Verifica os outros parâmetros
        assert params.period == "2023"
        assert params.location == "Brasil"

        # Testa a conversão para dicionário
        params_dict = params.dict()
        assert params_dict["table_code"] == "6401"
        assert params_dict["variables"] == ["93"]
        assert params_dict["classifications"] == {"C2": ["1", "2"]}


    def test_invalid_table_code(self):
        """Testa a validação de código de tabela inválido."""
        with pytest.raises(ValueError):
            SIDRAQueryParams(
                table_code="abc",  # Código inválido
                variables=[93],
                period="2023"
            )


    def test_missing_required_fields(self):
        """Testa a validação de campos obrigatórios."""
        with pytest.raises(ValueError):
            # Faltando variáveis
            SIDRAQueryParams(
                table_code=6401,
                period="2023"
            )

# Teste de integração (pode ser marcado como lento)
@pytest.mark.integration


class TestSIDRAClientIntegration:
    """Testes de integração com a API SIDRA real."""

    @patch('app.services.ibge.sidra_connector.sidrapy.get_table')


    def test_real_api_request(self, mock_get_table):
        """Testa uma requisição à API SIDRA com dados simulados."""
        # Configura o cliente com cache desativado
        client = SIDRAClient(cache_enabled=False)

        # Dados simulados que correspondem ao formato esperado
        mock_data = [
            {"D1C": "1", "D2C": "1", "V": 100.0, "D1N": "Brasil", "D2N": "Masculino"},
            {"D1C": "1", "D2C": "2", "V": 100.0, "D1N": "Brasil", "D2N": "Feminino"}
        ]
        mock_get_table.return_value = mock_data

        # Consulta simulada à PNAD Contínua (população por sexo)
        query = SIDRAQueryParams(
            table_code=6401,  # PNAD Contínua
            variables=[93],   # População
            classifications={"C2": [1, 2]},  # Sexo: 1=Masculino, 2=Feminino
            period="2023",  # Ano de 2023
            location="Brasil"
        )

        result = client.get_table(query)

        # Verificações básicas
        assert not result.empty
        assert "Valor" in result.columns
        assert "Sexo" in result.columns
        assert isinstance(result, pd.DataFrame)
# Executa os testes se o arquivo for executado diretamente
if __name__ == "__main__":
    pytest.main(["-v", "test_sidra_client.py"])
