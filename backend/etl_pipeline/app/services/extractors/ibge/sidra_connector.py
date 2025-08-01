"""
Conector para a API SIDRA do IBGE.

Este módulo fornece uma interface de alto nível para acessar os dados do IBGE
através da API SIDRA, com suporte a cache, novas tentativas automáticas e uma
camada de serviço para consultas semânticas (ex: por conceito de negócio).
"""

from pydantic import ValidationError
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast
from urllib3.exceptions import HTTPError
from requests.exceptions import RequestException, ConnectionError, Timeout

import pandas as pd
import requests
import sidrapy
from pydantic import BaseModel, Field, validator
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    retry_any,
    retry_if_exception
)

from .exceptions import (
    SidraApiError,
    SidraTableNotFoundError,
    SidraVariableNotFoundError,
    SidraClassificationNotFoundError,
    SidraCategoryNotFoundError,
    SidraLocationNotFoundError,
    SidraApiValidationError,
    SidraApiRateLimitError
)
from .mappers import SIDRAMapper

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constantes e Modelos ---
DEFAULT_CACHE_DIR = Path(".cache/sidra")
DEFAULT_CACHE_TTL_DAYS = 7

# Cache TTL inteligente baseado no tipo de dados (em dias)
INTELLIGENT_CACHE_TTL = {
    'demographic': 30,      # dados demográficos: 30 dias
    'economic': 7,          # dados econômicos: 7 dias  
    'survey': 90,           # dados de pesquisa: 90 dias
    'census': 365,          # dados do censo: 1 ano
    'metadata': 1,          # metadados: 1 dia
    'default': 7            # padrão: 7 dias
}

# Limites oficiais da API SIDRA
MAX_VALUES_PER_REQUEST = 100_000
MAX_DIMENSIONS = 9

# Tabelas que requerem parâmetros específicos
SPECIAL_TABLE_CONFIGS = {
    '6401': {'territorial_level': '1', 'note': 'PNAD Contínua - Brasil apenas'},
    '6402': {'territorial_level': '1', 'note': 'PNAD Contínua - Brasil apenas'},
    '6403': {'territorial_level': '1', 'note': 'PNAD Contínua - Brasil apenas'},
    '5918': {'territorial_level': '3', 'note': 'Municípios - requer nível N3 ou superior'}
}

class IBGEDataSource(str, Enum):
    """Fontes de dados do IBGE que possuem tabelas mapeadas."""
    POF = "POF"        # Pesquisa de Orçamentos Familiares
    PNAD = "PNAD"      # Pesquisa Nacional por Amostra de Domicílios Contínua
    CENSO = "CENSO"    # Censo Demográfico

# Dicionário com exemplos de tabelas SIDRA relevantes para cada fonte de dados
SIDRA_TABLES = {
    IBGEDataSource.POF: {
        "despesas_alimentacao": 7482,
    },
    IBGEDataSource.PNAD: {
        "populacao_idade_sexo": 6407,
        "rendimento_todas_fontes": 5437,
        "educacao_pessoas": 3564,
    },
    IBGEDataSource.CENSO: {
        "populacao_residente": 9514,
    },
}

class SIDRAQueryParams(BaseModel):
    """Modelo para validar e estruturar os parâmetros de uma consulta à API SIDRA.

    A localização pode ser especificada de duas formas (a primeira é recomendada):
    1. Pelo nome: `location='São Paulo'`
    2. Pelo código e nível: `territorial_level='3'`, `ibge_territorial_code='35'`
    """
    table_code: Union[str, int] = Field(..., description="Código da tabela SIDRA a ser consultada.")
    variables: List[Union[str, int]] = Field(..., description="Lista de códigos das variáveis a serem retornadas.")
    classifications: Optional[Dict[str, Union[List[Union[str, int]], str]]] = Field(
        None, 
        description="Filtros de classificação. Ex: {'C2': [3, 4]} para filtrar sexo ou {'C1': 'all'} para todas as categorias."
    )
    location: Optional[str] = Field(
        None,
        description="Nome da localidade (ex: 'Brasil', 'Região Sul', 'SP', 'Belo Horizonte'). Se fornecido, sobrepõe os parâmetros de nível e código territorial."
    )
    territorial_level: Optional[str] = Field(
        None,
        description="Nível territorial (ex: '1' para Brasil). Ignorado se 'location' for especificado."
    )
    ibge_territorial_code: Optional[Union[str, List[str]]] = Field(
        None,
        description="Código(s) do território (ex: '35' para SP). Ignorado se 'location' for especificado."
    )
    period: Union[str, List[str]] = Field(
        "last",
        description="Período dos dados (ex: 'last', '2022', '202201-202212'). Pode ser uma string ou lista de strings."
    )
    
    class Config:
        """Configurações do modelo Pydantic."""
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
    
    @validator('table_code')
    def validate_table_code(cls, v):
        """Valida o código da tabela."""
        if not str(v).isdigit():
            raise ValueError(f"Código de tabela inválido: {v}. Deve ser um número.")
        return str(v)
    
    @validator('variables', each_item=True)
    def validate_variables(cls, v):
        """Valida os códigos das variáveis."""
        if not str(v).isdigit():
            raise ValueError(f"Código de variável inválido: {v}. Deve ser um número.")
        return str(v)
    
    @validator('classifications')
    def validate_classifications(cls, v):
        """Valida os códigos de classificação e categorias.
        
        Mantém as chaves originais (incluindo o prefixo 'C' se presente) e apenas
        valida os valores, convertendo-os para o formato adequado.
        """
        if v is None:
            return None
            
        result = {}
        for key, value in v.items():
            # Converte a chave para string mantendo o formato original
            str_key = str(key)
            
            # Verifica se a chave começa com 'C' ou 'c' seguido de dígitos
            # ou se é apenas dígitos
            if not (str_key[0].lower() == 'c' and str_key[1:].isdigit()) and not str_key.isdigit():
                raise ValueError(
                    f"Código de classificação inválido: {key}. "
                    f"Deve ser um número ou começar com 'C' seguido de números."
                )
                
            if isinstance(value, str):
                # Se for string, deve ser 'all' (case insensitive)
                if value.lower() != 'all':
                    raise ValueError(
                        f"Valor de classificação inválido: {value}. "
                        f"Deve ser 'all' ou uma lista de códigos."
                    )
                result[str_key] = value.lower()
            elif isinstance(value, (list, tuple)):
                # Valida cada código de categoria
                validated_categories = []
                for item in value:
                    str_item = str(item)
                    if not str_item.isdigit():
                        raise ValueError(
                            f"Código de categoria inválido: {item}. "
                            f"Deve ser um número."
                        )
                    validated_categories.append(str_item)
                result[str_key] = validated_categories
            else:
                raise ValueError(
                    f"Tipo de valor de classificação inválido: {type(value)}. "
                    f"Deve ser 'all' ou uma lista de códigos."
                )
                
        return result

    class Config:
        """Configurações do modelo Pydantic."""
        schema_extra = {
            "example": {
                "table_code": 6407,
                "variables": [93],
                "classifications": {"C2": [3, 4]},
                "location": "São Paulo",
                "period": "last",
            }
        }

class SIDRAClient:
    """
    Cliente para a API SIDRA do IBGE com cache, novas tentativas e mapeamento dinâmico.
    
    Esta classe fornece uma interface robusta para acessar os dados da API SIDRA do IBGE,
    com suporte a cache, novas tentativas automáticas e mapeamento dinâmico de códigos.
    """
    # Constantes para configuração de novas tentativas
    MAX_RETRIES = 3
    RETRY_WAIT_MIN = 1  # segundos
    RETRY_WAIT_MAX = 10  # segundos
    
    # Constantes para cache
    CACHE_VERSION = "1.0"
    METADATA_CACHE_TTL = 86400  # 24 horas em segundos
    
    def __init__(
        self, 
        cache_enabled: bool = True, 
        cache_dir: Optional[Union[str, Path]] = None,
        cache_ttl_days: int = DEFAULT_CACHE_TTL_DAYS,
        max_retries: Optional[int] = None,
        retry_wait_min: Optional[int] = None,
        retry_wait_max: Optional[int] = None,
        enable_intelligent_cache: bool = True
    ):
        """
        Inicializa o cliente SIDRA com melhores práticas.

        Args:
            cache_enabled: Se True, ativa o cache de respostas em arquivos Parquet.
            cache_dir: Diretório para armazenar o cache.
            cache_ttl_days: Tempo de vida (TTL) do cache em dias.
            max_retries: Número máximo de tentativas para requisições à API.
            retry_wait_min: Tempo mínimo de espera entre tentativas (em segundos).
            retry_wait_max: Tempo máximo de espera entre tentativas (em segundos).
            enable_intelligent_cache: Se True, usa TTL inteligente baseado no tipo de dados.
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = timedelta(days=cache_ttl_days)
        self.enable_intelligent_cache = enable_intelligent_cache
        self.mapper = SIDRAMapper()
        
        # Configuração de novas tentativas
        self.max_retries = max_retries or self.MAX_RETRIES
        self.retry_wait_min = retry_wait_min or self.RETRY_WAIT_MIN
        self.retry_wait_max = retry_wait_max or self.RETRY_WAIT_MAX

        # Configuração do cache
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.metadata_cache = {}
        self.last_metadata_update = 0
        
        # Métricas de performance
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_data_points = 0
        
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache SIDRA ativado em: {self.cache_dir.resolve()}")
            
            # Cria subdiretórios para cache de metadados
            self.metadata_cache_dir = self.cache_dir / "metadata"
            self.metadata_cache_dir.mkdir(exist_ok=True)

    def _get_intelligent_cache_ttl(self, table_code: str) -> timedelta:
        """
        Determina o TTL do cache baseado no tipo de dados da tabela.
        
        Args:
            table_code: Código da tabela SIDRA
            
        Returns:
            TTL apropriado para o tipo de dados
        """
        if not self.enable_intelligent_cache:
            return self.cache_ttl
        
        # Mapeamento de tabelas para tipos de dados
        table_types = {
            # Dados demográficos (PNAD, Censo)
            'demographic': ['6407', '6408', '6409', '9514', '3175'],
            # Dados econômicos (PIB, Inflação, Emprego)
            'economic': ['5932', '1612', '6381', '6468'],
            # Dados de pesquisa (POF, PME)
            'survey': ['7482', '7483', '7484'],
            # Dados do censo (menos frequentes)
            'census': ['9514', '3175', '200']
        }
        
        # Determina o tipo baseado no código da tabela
        data_type = 'default'
        for type_name, table_list in table_types.items():
            if table_code in table_list:
                data_type = type_name
                break
        
        ttl_days = INTELLIGENT_CACHE_TTL.get(data_type, INTELLIGENT_CACHE_TTL['default'])
        return timedelta(days=ttl_days)
    
    def _estimate_request_size(self, query: SIDRAQueryParams) -> int:
        """
        Estima o número de valores que serão retornados pela consulta.
        
        Args:
            query: Parâmetros da consulta
            
        Returns:
            Estimativa do número de valores
        """
        try:
            # Valores base
            variables_count = len(query.variables) if query.variables else 1
            periods_count = 1  # Simplificado - pode ser expandido
            
            # Estimativa de territórios
            if query.location:
                territories_count = 1
            elif query.ibge_territorial_code == "all":
                # Estimativas baseadas no nível territorial
                level_estimates = {'1': 1, '2': 5, '3': 27, '6': 5570}
                territories_count = level_estimates.get(query.territorial_level or '1', 1)
            else:
                territories_count = 1
            
            # Estimativa de classificações
            classifications_count = 1
            if query.classifications:
                for value in query.classifications.values():
                    if isinstance(value, list):
                        classifications_count *= len(value)
                    elif value == 'all':
                        classifications_count *= 10  # Estimativa conservadora
            
            estimated_size = variables_count * periods_count * territories_count * classifications_count
            
            # Log warning se estimativa exceder o limite
            if estimated_size > MAX_VALUES_PER_REQUEST:
                logger.warning(
                    f"Consulta pode exceder limite de {MAX_VALUES_PER_REQUEST:,} valores. "
                    f"Estimativa: {estimated_size:,} valores"
                )
            
            return estimated_size
            
        except Exception as e:
            logger.warning(f"Erro ao estimar tamanho da consulta: {e}")
            return 1000  # Estimativa conservadora
    
    def _validate_table_constraints(self, query: SIDRAQueryParams) -> SIDRAQueryParams:
        """
        Valida e ajusta parâmetros baseado em restrições específicas das tabelas.
        
        Args:
            query: Parâmetros da consulta original
            
        Returns:
            Parâmetros ajustados conforme as restrições
        """
        table_code = str(query.table_code)
        
        # Verifica se a tabela tem configurações especiais
        if table_code in SPECIAL_TABLE_CONFIGS:
            config = SPECIAL_TABLE_CONFIGS[table_code]
            
            # Força nível territorial específico se necessário
            if 'territorial_level' in config:
                required_level = config['territorial_level']
                if query.territorial_level and query.territorial_level != required_level:
                    logger.warning(
                        f"Tabela {table_code} requer nível territorial {required_level}. "
                        f"Ajustando de {query.territorial_level} para {required_level}. "
                        f"Nota: {config.get('note', '')}"
                    )
                
                # Cria nova query com parâmetros ajustados
                query_dict = query.model_dump()
                query_dict['territorial_level'] = required_level
                if required_level == '1':  # Brasil apenas
                    query_dict['ibge_territorial_code'] = '1'
                    query_dict['location'] = 'Brasil'
                
                query = SIDRAQueryParams(**query_dict)
        
        return query
        """Gera uma chave de cache única e determinística para uma consulta."""
        # Usa model_dump() com json.dumps para compatibilidade com Pydantic v2
        query_dict = query.model_dump()
        query_str = json.dumps(query_dict, sort_keys=True)
        return hashlib.md5(query_str.encode('utf-8')).hexdigest()

    def _get_from_cache(self, key: str, table_id: str = None) -> Optional[pd.DataFrame]:
        """
        Carrega um DataFrame do cache se o arquivo existir e for válido, usando TTL inteligente.

        Args:
            key: Chave de cache gerada por _get_cache_key.
            table_id: ID da tabela para calcular TTL inteligente.

        Returns:
            DataFrame com os dados em cache ou None se não existir ou ser inválido.

        Raises:
            SidraApiError: Se ocorrer um erro ao carregar os dados do cache.
        """
        if not self.cache_enabled:
            self.cache_metrics['cache_disabled_calls'] += 1
            return None

        cache_file = self.cache_dir / f"{key}.parquet"

        try:
            if not cache_file.exists():
                logger.debug(f"Arquivo de cache não encontrado: {cache_file}")
                self.cache_metrics['cache_misses'] += 1
                return None

            # Calcula TTL inteligente baseado no tipo de dados da tabela
            intelligent_ttl = self._get_intelligent_cache_ttl(table_id) if table_id else self.cache_ttl
            
            # Verifica se o cache está expirado usando TTL inteligente
            file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            cache_age = datetime.now() - file_mtime
            
            if cache_age > intelligent_ttl:
                logger.debug(f"Cache expirado para a chave: {key} (idade: {cache_age}, TTL: {intelligent_ttl})")
                self.cache_metrics['cache_expired'] += 1
                # Remove arquivo expirado
                try:
                    cache_file.unlink()
                except OSError:
                    pass
                return None

            # Carrega os dados do arquivo Parquet
            df = pd.read_parquet(cache_file)
            
            # Verifica se o DataFrame está vazio
            if df.empty:
                logger.warning(f"Arquivo de cache vazio: {cache_file}")
                self.cache_metrics['cache_empty'] += 1
                return None
                
            # Cache hit bem-sucedido
            self.cache_metrics['cache_hits'] += 1
            self.cache_metrics['total_data_from_cache'] += len(df)
            
            cache_age_hours = cache_age.total_seconds() / 3600
            logger.info(f"Cache HIT: {key} (idade: {cache_age_hours:.1f}h, {len(df)} linhas)")
            return df

        except Exception as e:
            error_msg = f"Erro ao carregar dados do cache {cache_file}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.cache_metrics['cache_errors'] += 1
            raise SidraApiError(
                message=error_msg,
                original_error=e
            ) from e

    def _save_to_cache(self, key: str, df: pd.DataFrame) -> None:
        """
        Salva um DataFrame no cache como um arquivo Parquet.

        Args:
            key: Chave de cache gerada por _get_cache_key.
            df: DataFrame a ser salvo no cache.

        Raises:
            SidraApiError: Se ocorrer um erro ao salvar os dados no cache.
        """
        if not self.cache_enabled:
            self.cache_metrics['cache_disabled_calls'] += 1
            return
            
        if df is None or df.empty:
            logger.warning("Tentativa de salvar DataFrame vazio ou nulo no cache")
            self.cache_metrics['cache_empty_saves'] += 1
            return

        cache_file = self.cache_dir / f"{key}.parquet"
        
        try:
            # Cria o diretório de cache se não existir
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Salva o DataFrame em formato Parquet
            df.to_parquet(cache_file, index=False)
            
            # Adiciona metadados ao arquivo para rastreamento
            metadata = {
                'version': self.CACHE_VERSION,
                'created_at': datetime.now().isoformat(),
                'num_rows': len(df),
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            # Salva metadados em um arquivo JSON separado
            metadata_file = cache_file.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Atualiza métricas de cache
            self.cache_metrics['cache_saves'] += 1
            self.cache_metrics['total_data_cached'] += len(df)
            
            logger.info(
                f"Cache SAVE: {key} "
                f"({len(df)} linhas, {len(df.columns)} colunas, {cache_file.stat().st_size / 1024:.1f}KB)"
            )
            
        except Exception as e:
            error_msg = f"Erro ao salvar dados no cache {cache_file}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.cache_metrics['cache_errors'] += 1
            
            # Não interrompe o fluxo principal em caso de falha no cache
            try:
                # Tenta remover arquivos parciais em caso de erro
                if cache_file.exists():
                    cache_file.unlink()
                metadata_file = cache_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
            except Exception as cleanup_error:
                logger.error(f"Erro ao limpar cache após falha: {cleanup_error}")
                
            raise SidraApiError(
                message=error_msg,
                original_error=e
            ) from e
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RequestException, HTTPError, Timeout, ConnectionError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def get_table(self, query: SIDRAQueryParams) -> pd.DataFrame:
        """
        Obtém dados da API SIDRA com base nos parâmetros fornecidos.
        
        Este método implementa um padrão de resiliência com cache inteligente, novas tentativas
        e tratamento de erros robusto. Os dados são armazenados em cache local com TTL
        baseado no tipo de dados para melhor desempenho em consultas repetidas.
        
        Args:
            query: Parâmetros da consulta SIDRA.
            
        Returns:
            DataFrame com os dados da tabela solicitada.
            
        Raises:
            SidraApiError: Se ocorrer um erro ao acessar a API SIDRA ou processar os dados.
            ValueError: Se os parâmetros de consulta forem inválidos.
        """
        # Valida os parâmetros da consulta
        try:
            query = SIDRAQueryParams(**query.model_dump())
        except ValidationError as e:
            error_msg = f"Parâmetros de consulta inválidos: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        
        # Valida restrições da tabela
        query = self._validate_table_constraints(query)
        
        # Estima tamanho da requisição
        estimated_size = self._estimate_request_size(query)
        if estimated_size > self.MAX_REQUEST_SIZE:
            raise SidraApiError(
                message=f"Requisição muito grande: {estimated_size} > {self.MAX_REQUEST_SIZE}",
                error_code="REQUEST_TOO_LARGE"
            )
        
        # Gera chave de cache e verifica se os dados estão em cache
        cache_key = self._get_cache_key(query)
        try:
            cached_df = self._get_from_cache(cache_key, str(query.table_code))
            if cached_df is not None:
                logger.info(f"Dados recuperados do cache para a tabela {query.table_code}")
                return cached_df
        except SidraApiError as e:
            logger.warning(f"Erro ao acessar cache, continuando sem cache: {e}")
            # Continua sem cache em caso de erro
            # Obtém informações da tabela
            table_info = self.mapper.get_table_info(query.table_code)
            if not table_info:
                raise SidraApiError(
                    message=f"Tabela {query.table_code} não encontrada no mapeamento",
                    error_code="TABLE_NOT_FOUND"
                )
            
            # Prepara e executa a requisição
            params = self._prepare_sidra_params(query)
            logger.info(f"Fazendo requisição para a API SIDRA - Tabela {query.table_code}")
            
            # Usa get_table do sidrapy com parâmetros corretos
            raw_data = sidrapy.get_table(
                table_code=str(query.table_code),
                territorial_level=params['territorial_level'],
                ibge_territorial_code=params['ibge_territorial_code'],
                variable=params.get('variable'),
                classifications=params.get('classifications'),
                period=params.get('period', 'last'),
                header='y',
                format='list'
            )
            
            # Processa e valida a resposta
            df = self._process_sidra_response(raw_data, str(query.table_code))
            if df is None or df.empty:
                raise SidraApiError(
                    message=f"Nenhum dado retornado para a tabela {query.table_code}",
                    error_code="NO_DATA_RETURNED"
                )
            
            # Tenta salvar no cache (não falha se não conseguir)
            try:
                self._save_to_cache(cache_key, df)
            except SidraApiError as e:
                logger.warning(f"Falha ao salvar no cache: {e}")
            
            return df
            
        except (RequestException, HTTPError, Timeout, ConnectionError):
            # Re-raise network errors for retry decorator
            raise
            
        except SidraApiError:
            # Re-raise application errors without retry
            raise
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Erro inesperado ao acessar a tabela {query.table_code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SidraApiError(
                message=error_msg,
                original_error=e,
                error_code="UNEXPECTED_ERROR"
            ) from e
    def _prepare_sidra_params(self, query: SIDRAQueryParams) -> Dict[str, Any]:
        """
        Prepara os parâmetros para a requisição à API SIDRA.
        
        Args:
            query: Parâmetros da consulta.
            
        Returns:
            Dicionário com os parâmetros formatados para a API.
            
        Raises:
            SidraApiError: Se os parâmetros forem inválidos ou incompatíveis.
        """
        try:
            # Tabelas que só suportam nível nacional (N1)
            national_only_tables = ["6401", "6402", "6403"]  # PNAD Contínua e similares
            
            # Resolve a localização se fornecida
            if query.location:
                location_info = self.mapper.get_location_info(query.location)
                if not location_info:
                    raise SidraApiError(
                        message=f"Localização não encontrada: '{query.location}'",
                        error_code="LOCATION_NOT_FOUND"
                    )
                # Força nível nacional para tabelas específicas
                if str(query.table_code) in national_only_tables:
                    territorial_level = "1"  # Sempre nível nacional
                    ibge_territorial_code = "1"  # Brasil
                    logger.warning(f"Tabela {query.table_code} só suporta nível nacional. Forçando N1/Brasil.")
                else:
                    territorial_level = location_info['level']
                    ibge_territorial_code = location_info['code']
            else:
                territorial_level = query.territorial_level or "1"
                ibge_territorial_code = query.ibge_territorial_code or "all"
            
            # Prepara as variáveis
            variables = []
            if query.variables and len(query.variables) > 0:
                for var in query.variables:
                    if isinstance(var, (int, str)) and str(var).strip():
                        variables.append(str(var))
                    else:
                        raise SidraApiError(
                            message=f"Tipo de variável inválido: {type(var).__name__}",
                            error_code="INVALID_VARIABLE_TYPE"
                        )
            
            # Prepara as classificações
            classifications = {}
            if query.classifications:
                for key, value in query.classifications.items():
                    # Remove o prefixo 'C' ou 'c' se existir
                    clean_key = key.lstrip('Cc')
                    
                    # Formata os valores da classificação
                    if isinstance(value, (list, tuple)):
                        classifications[clean_key] = ','.join(map(str, value))
                    else:
                        classifications[clean_key] = str(value)
            
            # Constrói o dicionário de parâmetros
            params = {
                'table_code': str(query.table_code),
                'territorial_level': territorial_level,
                'ibge_territorial_code': ibge_territorial_code,
                'period': query.period or 'last',
                'header': 'y',
            }
            
            # Adiciona variáveis se fornecidas
            if variables and len(variables) > 0:
                params['variable'] = ','.join(variables)
            
            # Adiciona as classificações se fornecidas
            if classifications:
                params['classifications'] = classifications
            
            return params
            
        except SidraApiError:
            raise
        except Exception as e:
            error_msg = f"Erro ao preparar parâmetros para a tabela {query.table_code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SidraApiError(
                message=error_msg,
                original_error=e,
                error_code="PARAM_PREP_ERROR"
            ) from e

    def _process_sidra_response(self, raw_data: List[Dict], table_code: str) -> pd.DataFrame:
        """
        Processa a resposta da API SIDRA e converte para DataFrame.
        
        Args:
            raw_data: Dados brutos retornados pela API SIDRA.
            table_code: Código da tabela para fins de log.
            
        Returns:
            DataFrame com os dados processados.
            
        Raises:
            SidraApiError: Se os dados não puderem ser processados.
        """
        try:
            # Verifica se a resposta está vazia ou inválida
            if not raw_data or not isinstance(raw_data, list) or len(raw_data) < 2:
                logger.warning(f"Resposta vazia ou inválida da API SIDRA para a tabela {table_code}")
                return pd.DataFrame()
            
            # O primeiro item é o cabeçalho, os demais são os dados
            headers = raw_data[0]
            data = raw_data[1:]
            
            # Cria o DataFrame com os dados e os cabeçalhos
            df = pd.DataFrame(data, columns=headers.keys())
            
            # Remove linhas vazias ou inválidas
            df = df.dropna(how='all')
            
            # Converte a coluna de valor para numérico, se existir
            if 'V' in df.columns:
                # Remove pontos de milhar e converte vírgula para ponto decimal
                df['V'] = df['V'].astype(str).str.replace('.', '').str.replace(',', '.')
                df['V'] = pd.to_numeric(df['V'], errors='coerce')
                df = df.rename(columns={'V': 'Valor'})
            
            # Renomeia colunas comuns para nomes mais legíveis
            column_mapping = {
                'D1N': 'Localidade',
                'D2N': 'Sexo',
                'D3N': 'Idade',
                'D4N': 'Cor_Raca',
                'D5N': 'Escolaridade'
            }
            
            df = df.rename(columns={
                k: v for k, v in column_mapping.items() 
                if k in df.columns
            })
            
            # Adiciona metadados úteis
            df['Tabela'] = table_code
            
            logger.info(f"Dados processados - Tabela {table_code}: {len(df)} registros")
            return df
            
        except Exception as e:
            error_msg = f"Erro ao processar resposta da tabela {table_code}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise SidraApiError(
                message=error_msg,
                original_error=e,
                error_code="DATA_PROCESSING_ERROR"
            ) from e

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas detalhadas do sistema de cache.
        
        Returns:
            Dicionário com estatísticas de performance do cache.
        """
        total_requests = (self.cache_metrics['cache_hits'] + 
                         self.cache_metrics['cache_misses'] + 
                         self.cache_metrics['cache_expired'])
        
        hit_rate = (self.cache_metrics['cache_hits'] / total_requests * 100 
                   if total_requests > 0 else 0)
        
        cache_efficiency = {
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'cache_hits': self.cache_metrics['cache_hits'],
            'cache_misses': self.cache_metrics['cache_misses'],
            'cache_expired': self.cache_metrics['cache_expired'],
            'cache_errors': self.cache_metrics['cache_errors'],
            'cache_saves': self.cache_metrics['cache_saves'],
            'cache_empty_saves': self.cache_metrics['cache_empty_saves'],
            'cache_disabled_calls': self.cache_metrics['cache_disabled_calls'],
            'total_data_cached': self.cache_metrics['total_data_cached'],
            'total_data_from_cache': self.cache_metrics['total_data_from_cache'],
            'cache_enabled': self.cache_enabled,
            'cache_dir': str(self.cache_dir),
            'default_ttl_hours': self.cache_ttl.total_seconds() / 3600
        }
        
        # Adiciona informações sobre TTL inteligente
        cache_efficiency['intelligent_ttl_mapping'] = {
            data_type: ttl.total_seconds() / 3600 
            for data_type, ttl in self.INTELLIGENT_CACHE_TTL.items()
        }
        
        return cache_efficiency


class SIDRAService:
    """
    Serviço de alto nível que utiliza o SIDRAClient para fornecer acesso
    semântico aos dados do IBGE, abstraindo códigos de tabelas e variáveis.
    """
    def __init__(self, client: Optional[SIDRAClient] = None):
        """
        Inicializa o serviço SIDRA.

        Args:
            client: Uma instância de SIDRAClient. Se não for fornecida, uma nova será criada.
        """
        self.client = client or SIDRAClient()

    def get_table(
        self,
        table_code: str,
        variables: List[str] = None,
        classifications: Dict[str, Union[str, List[str]]] = None,
        location: str = "Brasil",
        period: str = "last"
    ) -> Dict[str, Any]:
        """
        Método de conveniência para obter dados de uma tabela SIDRA.
        
        Args:
            table_code: Código da tabela SIDRA
            variables: Lista de códigos de variáveis
            classifications: Dicionário de classificações
            location: Localização (padrão: "Brasil")
            period: Período (padrão: "last")
            
        Returns:
            Dicionário com os dados da tabela
        """
        try:
            logger.info(f"Obtendo dados da tabela SIDRA {table_code} para {location}")
            
            # Cria query para o SIDRAClient
            query = SIDRAQueryParams(
                table_code=table_code,
                variables=variables or [],  # Lista vazia em vez de ["all"]
                classifications=classifications or {},
                location=location,
                period=period
            )
            
            # Obtem os dados do client
            df = self.client.get_table(query)
            
            if df is not None and not df.empty:
                # Converte para formato dicionário
                result = {
                    'value': df.to_dict(orient='records'),
                    'metadata': {
                        'table_code': table_code,
                        'location': location,
                        'period': period,
                        'records_count': len(df)
                    }
                }
                logger.info(f"Dados obtidos com sucesso: {len(df)} registros")
                return result
            else:
                logger.warning(f"Nenhum dado retornado para tabela {table_code}")
                return {'value': [], 'metadata': {'table_code': table_code, 'records_count': 0}}
                
        except Exception as e:
            logger.error(f"Erro ao obter dados da tabela {table_code}: {str(e)}", exc_info=True)
            # Retorna estrutura vazia em caso de erro
            return {'value': [], 'metadata': {'table_code': table_code, 'error': str(e)}}

    def get_population_by_sex_and_age(
        self, 
        location: str, 
        period: str = "last"
    ) -> pd.DataFrame:
        """
        Obtém a população total por sexo e grupos de idade para uma dada localidade.

        Args:
            location: Nome da localidade (ex: 'Brasil', 'RS', 'Curitiba').
            period: Período desejado (padrão: 'last').

        Returns:
            DataFrame com os dados populacionais.
        """
        logger.info(f"Buscando perfil populacional para '{location}'...")
        query = SIDRAQueryParams(
            table_code=SIDRA_TABLES[IBGEDataSource.PNAD]['populacao_idade_sexo'],
            variables=[93], # Variável: População
            classifications={
                'C2': 'all',  # Sexo
                'C1': 'all'   # Grupo de Idade
            },
            location=location,
            period=period
        )
        return self.client.get_table(query)

    def get_income_distribution(
        self, 
        location: str,
        period: str = "last"
    ) -> pd.DataFrame:
        """
        Obtém a distribuição de rendimento médio mensal para uma localidade.

        Args:
            location: Nome da localidade.
            period: Período desejado.

        Returns:
            DataFrame com dados de rendimento.
        """
        logger.info(f"Buscando distribuição de renda para '{location}'...")
        query = SIDRAQueryParams(
            table_code=SIDRA_TABLES[IBGEDataSource.PNAD]['rendimento_todas_fontes'],
            variables=[4099], # Rendimento médio mensal real
            classifications={'C544': 'all'}, # Classes de rendimento
            location=location,
            period=period
        )
        return self.client.get_table(query)

    def get_concept_data(
        self,
        concept: str,
        location: str = "Brasil",
        period: str = "last"
    ) -> pd.DataFrame:
        """
        Obtém dados para um conceito de negócio pré-mapeado.

        Args:
            concept: Nome do conceito (definido no arquivo de mapeamento).
            location: Nome da localidade.
            period: Período desejado.

        Returns:
            DataFrame com os dados do conceito.
        """
        logger.info(f"Buscando dados para o conceito '{concept}' em '{location}'...")
        
        # Obtém o mapeamento completo do conceito
        mapping = self.client.mapper.get_concept_mapping(concept)
        
        # Cria a consulta a partir do mapeamento
        query = SIDRAQueryParams(
            table_code=mapping['table_code'],
            variables=mapping['variables'],
            classifications=mapping.get('classifications'),
            location=location,
            period=period
        )
        return self.client.get_table(query)

    def get_demographic_profile(
        self,
        location: str,
        age_range: Optional[Tuple[int, int]] = None,
        education_level: Optional[str] = None,
        period: str = "last"
    ) -> Dict[str, Any]:
        """
        Obtém um perfil demográfico simplificado.

        NOTA: Esta é uma implementação de exemplo. A filtragem por faixa etária
        e nível de educação requer uma lógica mais complexa de processamento
        de strings e/ou junção de dados de múltiplas tabelas.

        Args:
            location: Nome da localidade.
            age_range: Faixa etária (atualmente não implementado o filtro).
            education_level: Nível de educação (atualmente não implementado o filtro).
            period: Período desejado.

        Returns:
            Um dicionário com os dados e um resumo.
        """
        logger.info(f"Buscando perfil demográfico para '{location}'...")
        if age_range:
            logger.warning(f"A filtragem por faixa etária ({age_range}) não está implementada nesta versão.")
        if education_level:
            logger.warning(f"A filtragem por nível de educação ('{education_level}') não está implementada.")

        # A base para o perfil demográfico é a população por sexo e idade.
        df = self.get_population_by_sex_and_age(location=location, period=period)

        # Calcula um resumo simples
        total_population = df['Valor'].sum()
        summary = {
            "total_population": int(total_population) if not pd.isna(total_population) else 0,
            "description": f"População total estimada para '{location}'."
        }

        return {"data": df.to_dict(orient='records'), "summary": summary}

# --- Exemplo de Uso ---
if __name__ == '__main__':
    # Inicializa o serviço
    service = SIDRAService()

    try:
        # Exemplo 1: Buscar perfil populacional do estado de Santa Catarina
        pop_sc_df = service.get_population_by_sex_and_age(location="Santa Catarina")
        print("\n--- População de Santa Catarina por Sexo e Idade ---")
        print(pop_sc_df.head())

        # Exemplo 2: Buscar distribuição de renda para a Região Nordeste
        income_ne_df = service.get_income_distribution(location="Região Nordeste", period="2023")
        print("\n--- Distribuição de Renda na Região Nordeste (2023) ---")
        print(income_ne_df.head())
        
        # Exemplo 3: Usar um conceito pré-mapeado (supondo que 'pib_per_capita' exista no seu JSON)
        # Para este exemplo funcionar, seu sidra_mappings.json precisa ter a entrada 'pib_per_capita'
        # try:
        #     pib_df = service.get_concept_data(concept="pib_per_capita", location="Brasil")
        #     print("\n--- Conceito: PIB per capita do Brasil ---")
        #     print(pib_df.head())
        # except ValueError as e:
        #     print(f"\nNão foi possível buscar o conceito: {e}")

    except Exception as e:
        logger.error(f"Ocorreu um erro durante a execução do exemplo: {e}")