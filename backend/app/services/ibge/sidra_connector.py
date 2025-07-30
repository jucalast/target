"""
Conector para a API SIDRA do IBGE.

Este módulo fornece uma interface de alto nível para acessar os dados do IBGE
através da API SIDRA, com suporte a cache, novas tentativas automáticas e uma
camada de serviço para consultas semânticas (ex: por conceito de negócio).
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import pandas as pd
import sidrapy
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Importa o SIDRAMapper do módulo de mapeamento
# (Ajuste o caminho conforme a estrutura do seu projeto)
# from .mappers import SIDRAMapper 
# Para fins de exemplo, vamos supor que SIDRAMapper está no mesmo diretório
from .mappers import SIDRAMapper

# --- Configuração Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constantes e Modelos ---
DEFAULT_CACHE_DIR = Path(".cache/sidra")
DEFAULT_CACHE_TTL_DAYS = 7

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
    """
    Modelo para validar e estruturar os parâmetros de uma consulta à API SIDRA.

    A localização pode ser especificada de duas formas (a primeira é recomendada):
    1. Pelo nome: `location='São Paulo'`
    2. Pelo código e nível: `territorial_level='3'`, `ibge_territorial_code='35'`
    """
    table_code: int = Field(..., description="Código da tabela SIDRA a ser consultada.")
    variables: List[int] = Field(..., description="Lista de códigos das variáveis a serem retornadas.")
    classifications: Optional[Dict[str, Union[List[int], str]]] = Field(
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
    period: str = Field(
        "last",
        description="Período dos dados (ex: 'last', '2022', '202201-202212')."
    )

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
    Cliente para a API SIDRA do IBGE com cache, novas tentativas e mapeamento.
    """
    def __init__(
        self, 
        cache_enabled: bool = True, 
        cache_dir: Optional[Union[str, Path]] = None,
        cache_ttl_days: int = DEFAULT_CACHE_TTL_DAYS
    ):
        """
        Inicializa o cliente SIDRA.

        Args:
            cache_enabled: Se True, ativa o cache de respostas em arquivos Parquet.
            cache_dir: Diretório para armazenar o cache.
            cache_ttl_days: Tempo de vida (TTL) do cache em dias.
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = timedelta(days=cache_ttl_days)
        self.mapper = SIDRAMapper()

        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache SIDRA ativado em: {self.cache_dir.resolve()}")

    def _get_cache_key(self, query: SIDRAQueryParams) -> str:
        """Gera uma chave de cache única e determinística para uma consulta."""
        # Usa model_dump() com json.dumps para compatibilidade com Pydantic v2
        query_dict = query.model_dump()
        query_str = json.dumps(query_dict, sort_keys=True)
        return hashlib.md5(query_str.encode('utf-8')).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[pd.DataFrame]:
        """Carrega um DataFrame do cache se o arquivo existir e for válido."""
        if not self.cache_enabled:
            return None
        
        cache_file = self.cache_dir / f"{key}.parquet"
        if not cache_file.exists():
            return None
        
        file_mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - file_mod_time > self.cache_ttl:
            logger.info(f"Cache expirado para a chave {key}. Buscando novos dados.")
            return None
        
        try:
            logger.info(f"Carregando dados do cache para a chave: {key}")
            return pd.read_parquet(cache_file)
        except Exception as e:
            logger.warning(f"Não foi possível ler o arquivo de cache {cache_file}: {e}")
            return None

    def _save_to_cache(self, key: str, df: pd.DataFrame) -> None:
        """Salva um DataFrame no cache como um arquivo Parquet."""
        if not self.cache_enabled or df.empty:
            return
            
        cache_file = self.cache_dir / f"{key}.parquet"
        try:
            df.to_parquet(cache_file, index=False)
            logger.info(f"Dados salvos no cache: {cache_file}")
        except Exception as e:
            logger.error(f"Falha ao salvar dados no cache {cache_file}: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception), # Tenta novamente para qualquer exceção da API
        reraise=True
    )
    def get_table(self, query: SIDRAQueryParams) -> pd.DataFrame:
        """
        Busca dados da API SIDRA usando sidrapy.get para maior controle sobre a formatação da URL.
        
        Args:
            query: Parâmetros da consulta à API SIDRA.
            
        Returns:
            DataFrame com os dados solicitados.
            
        Raises:
            ValueError: Se os parâmetros forem inválidos ou a resposta estiver vazia.
            Exception: Para erros de rede ou da API.
        """
        # Gera uma chave única para o cache baseada nos parâmetros da consulta
        cache_key = self._get_cache_key(query)
        
        # Tenta obter os dados do cache primeiro
        cached_df = self._get_from_cache(cache_key)
        if cached_df is not None:
            logger.info(f"Retornando dados em cache para a tabela {query.table_code}")
            return cached_df

        logger.info(f"Buscando dados da API SIDRA para a tabela {query.table_code}...")

        # 1. Resolve a localização
        if query.location:
            location_info = self.mapper.get_location_info(query.location)
            if not location_info:
                raise ValueError(f"Localização não encontrada: '{query.location}'")
            territorial_level = location_info['level']
            ibge_territorial_code = location_info['code']
        else:
            territorial_level = query.territorial_level or "1"
            ibge_territorial_code = query.ibge_territorial_code or "all"
        
        # 2. Converte o dicionário de classificações para o formato esperado pelo sidrapy
        sidra_classifications = None
        if query.classifications:
            sidra_classifications = {}
            for key, value in query.classifications.items():
                # A API SIDRA, via sidrapy, espera que a chave da classificação seja apenas o número.
                # Ex: 'C1' -> '1', 'C544' -> '544'
                clean_key = key.lstrip('Cc')
                if isinstance(value, (list, tuple)):
                    sidra_classifications[clean_key] = ','.join(map(str, value))
                else:
                    sidra_classifications[clean_key] = str(value)

        try:
            # 3. Chama a função sidrapy.get_table
            # A função get() foi usada em versões mais antigas ou em implementações customizadas.
            # A função padrão e atual é get_table().
            raw_data = sidrapy.get_table(
                table_code=str(query.table_code),
                territorial_level=territorial_level,
                ibge_territorial_code=ibge_territorial_code,
                variable=','.join(map(str, query.variables)),
                period=query.period,
                classifications=sidra_classifications,
                header="y"
            )

            # 4. Verifica e converte manualmente para DataFrame
            if not raw_data or len(raw_data) < 2:
                raise ValueError(f"A API SIDRA retornou uma resposta vazia para a tabela {query.table_code}.")
            
            # A primeira linha contém os cabeçalhos, as demais contêm os dados
            header = raw_data[0]
            data_rows = raw_data[1:]
            
            # Cria o DataFrame manualmente
            df = pd.DataFrame(data_rows, columns=header.values())
            
            # Tenta converter a coluna 'Valor' para numérico para facilitar análises
            if 'Valor' in df.columns:
                # 'coerce' transforma valores não numéricos em NaN (Not a Number)
                df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

            # Salva no cache e retorna
            self._save_to_cache(cache_key, df)
            return df.copy()
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados da tabela {query.table_code}: {e}")
            raise

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