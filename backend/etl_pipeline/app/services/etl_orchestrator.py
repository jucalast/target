"""
ETL Orchestrator

Este módulo implementa o orquestrador do pipeline ETL, coordenando a extração,
transformação e carregamento de dados de múltiplas fontes, com foco na integração
com o módulo de PLN e preparação dos dados para o próximo módulo.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from shared.schemas.nlp_features import NLPFeatures
from shared.schemas.etl_parameters import ETLParameters, IBGETableQuery, GoogleTrendsQuery
from shared.schemas.etl_output import ETLOutput, MarketSegment, SearchTrend, NewsArticle

from ..extractors.ibge.sidra_connector import SIDRAClient, SIDRAService
from ..extractors.google_trends_service import GoogleTrendsService
from ..repositories.etl_repository import ETLRepository
from .transformers.ibge_transformer import IBGETransformer
from .transformers.trends_transformer import TrendsTransformer

logger = logging.getLogger(__name__)

class ETLError(Exception):
    """Exceção personalizada para erros no pipeline ETL."""
    pass

class ETLCoordinator:
    """
    Coordenador do pipeline ETL.
    
    Esta classe coordena a execução do pipeline completo de ETL, incluindo:
    - Extração de dados de múltiplas fontes (IBGE, Google Trends, etc.)
    - Transformação dos dados em um formato padronizado
    - Carga dos dados processados para o próximo módulo
    """
    
    def __init__(self, db: Session, max_workers: int = 3):
        """
        Inicializa o coordenador ETL.
        
        Args:
            db: Sessão do banco de dados SQLAlchemy
            max_workers: Número máximo de workers para processamento paralelo
        """
        self.db = db
        self.max_workers = max_workers
        
        # Inicializa os serviços de extração
        self.sidra_client = SIDRAClient()
        self.sidra_service = SIDRAService(self.sidra_client)
        self.google_trends = GoogleTrendsService()
        
        # Inicializa os transformadores
        self.ibge_transformer = IBGETransformer()
        self.trends_transformer = TrendsTransformer()
        
        # Cache para dados processados
        self.cache = {}
    
    def process_etl_request(self, etl_params: ETLParameters) -> ETLOutput:
        """
        Processa uma requisição ETL completa.
        
        Args:
            etl_params: Parâmetros de entrada para o pipeline ETL
            
        Returns:
            ETLOutput com os dados processados e estruturados
            
        Raises:
            ETLError: Em caso de falha no processamento
        """
        start_time = time.time()
        logger.info(f"Iniciando processamento ETL para requisição: {etl_params.request_id}")
        
        try:
            # 1. Extrair dados das fontes
            self._extract_data(etl_params)
            
            # 2. Transformar dados
            transformed_data = self._transform_data(etl_params)
            
                # 3. Preparar saída
            etl_output = self._prepare_output(etl_params, transformed_data)
            
            # 4. Persistir resultados
            self._persist_results(etl_output)
            
            # 5. Calcular tempo de processamento
            processing_time = time.time() - start_time
            etl_output.processing_time = processing_time
            
            logger.info(f"Processamento ETL concluído em {processing_time:.2f} segundos")
            return etl_output
            
        except Exception as e:
            logger.error(f"Erro no processamento ETL: {str(e)}", exc_info=True)
            raise ETLError(f"Falha no processamento ETL: {str(e)}")
    
    def _extract_data(self, etl_params: ETLParameters) -> None:
        """
        Extrai dados das fontes configuradas.
        
        Args:
            etl_params: Parâmetros de entrada para o pipeline ETL
        """
        logger.info("Iniciando extração de dados")
        
        # Inicializa o dicionário de cache
        self.cache = {
            'request_id': etl_params.request_id,
            'timestamp': etl_params.timestamp,
            'user_input': etl_params.user_input,
            'nlp_features': etl_params.nlp_features.dict(),
            'ibge_data': {},
            'google_trends_data': {},
            'news_data': []
        }
        
        # Lista de tarefas de extração a serem executadas em paralelo
        extraction_tasks = []
        
        # Adiciona tarefas de extração do IBGE, se houver consultas
        if etl_params.ibge_queries:
            extraction_tasks.append((self._extract_ibge_data, etl_params.ibge_queries))
        
        # Adiciona tarefas de extração do Google Trends, se houver consultas
        if etl_params.google_trends_queries:
            extraction_tasks.append((self._extract_google_trends, etl_params.google_trends_queries))
        
        # Adiciona tarefas de scraping de notícias, se configurado
        if etl_params.news_queries:
            extraction_tasks.append((self._extract_news, etl_params.news_queries))
        
        # Executa as tarefas de extração em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(task_func, params)
                for task_func, params in extraction_tasks
            ]
            
            # Aguarda a conclusão de todas as tarefas
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Erro na tarefa de extração: {str(e)}", exc_info=True)
        
        logger.info("Extração de dados concluída")
    
    def _extract_ibge_data(self, queries: List[IBGETableQuery]) -> None:
        """
        Extrai dados do IBGE SIDRA com base nas consultas fornecidas.
        
        Args:
            queries: Lista de consultas ao IBGE SIDRA
        """
        logger.info(f"Extraindo dados do IBGE para {len(queries)} consultas")
        
        for query in queries:
            try:
                # Extrai os dados usando o SIDRAService
                data = self.sidra_service.get_table(
                    table_code=query.table_code,
                    variables=query.variables,
                    classifications=query.classifications,
                    location=query.location,
                    period=query.period
                )
                
                # Armazena os dados brutos no cache
                cache_key = f"ibge_{query.table_code}_{query.location}"
                self.cache['ibge_data'][cache_key] = data
                
                logger.debug(f"Dados do IBGE extraídos para tabela {query.table_code}")
                
            except Exception as e:
                logger.error(f"Erro ao extrair dados do IBGE: {str(e)}", exc_info=True)
                self.cache['ibge_data'][f"error_{query.table_code}"] = {
                    'error': str(e),
                    'query': query.dict()
                }
    
    def _extract_google_trends(self, queries: List[GoogleTrendsQuery]) -> None:
        """
        Extrai dados do Google Trends com base nas consultas fornecidas.
        
        Args:
            queries: Lista de consultas ao Google Trends
        """
        logger.info(f"Extraindo dados do Google Trends para {len(queries)} consultas")
        
        for query in queries:
            try:
                # Extrai os dados de interesse ao longo do tempo
                interest_data = self.google_trends.get_interest_over_time(
                    keywords=query.keywords,
                    timeframe=query.timeframe,
                    geo=query.geo,
                    gprop=query.gprop
                )
                
                # Extrai consultas relacionadas para cada termo
                related_queries = {}
                for keyword in query.keywords:
                    related = self.google_trends.get_related_queries(
                        keywords=[keyword],
                        timeframe=query.timeframe,
                        geo=query.geo
                    )
                    related_queries[keyword] = related
                
                # Armazena os dados brutos no cache
                cache_key = f"trends_{'_'.join(query.keywords)}_{query.geo}"
                self.cache['google_trends_data'][cache_key] = {
                    'interest': interest_data,
                    'related_queries': related_queries
                }
                
                logger.debug(f"Dados do Google Trends extraídos para termos: {', '.join(query.keywords)}")
                
            except Exception as e:
                logger.error(f"Erro ao extrair dados do Google Trends: {str(e)}", exc_info=True)
                self.cache['google_trends_data'][f"error_{'_'.join(query.keywords)}"] = {
                    'error': str(e),
                    'query': query.dict()
                }
    
    def _extract_news(self, query) -> None:
        """
        Extrai notícias de fontes setoriais.
        
        Args:
            query: Parâmetros para a coleta de notícias
        """
        logger.info("Extraindo notícias setoriais")
        # TODO: Implementar coleta de notícias de fontes abertas
        self.cache['news_data'] = []
    
    def _transform_data(self, etl_params: ETLParameters) -> Dict[str, Any]:
        """
        Transforma os dados extraídos em um formato padronizado.
        
        Args:
            etl_params: Parâmetros de entrada para o pipeline ETL
            
        Returns:
            Dicionário com os dados transformados
        """
        logger.info("Iniciando transformação de dados")
        
        transformed = {
            'market_segments': {},
            'search_trends': {},
            'news_articles': []
        }
        
        # 1. Transforma dados do IBGE
        if self.cache.get('ibge_data'):
            for cache_key, ibge_data in self.cache['ibge_data'].items():
                if not isinstance(ibge_data, dict) or 'error' in ibge_data:
                    logger.warning(f"Dados do IBGE inválidos para {cache_key}")
                    continue
                    
                try:
                    # Aplica o transformador do IBGE
                    segments = self.ibge_transformer.transform(ibge_data)
                    
                    # Adiciona os segmentos transformados ao resultado
                    for segment_name, segment in segments.items():
                        if segment_name in transformed['market_segments']:
                            # Se o segmento já existe, atualiza as métricas
                            transformed['market_segments'][segment_name].metrics.update(segment.metrics)
                        else:
                            transformed['market_segments'][segment_name] = segment
                    
                except Exception as e:
                    logger.error(f"Erro ao transformar dados do IBGE ({cache_key}): {str(e)}", exc_info=True)
        
        # 2. Transforma dados do Google Trends
        if self.cache.get('google_trends_data'):
            for cache_key, trends_data in self.cache['google_trends_data'].items():
                if not isinstance(trends_data, dict) or 'error' in trends_data:
                    logger.warning(f"Dados do Google Trends inválidos para {cache_key}")
                    continue
                try:
                    trend = self.trends_transformer.transform(trends_data)
                    if trend:
                        transformed['search_trends'][trend.keyword] = trend
                except Exception as e:
                    logger.error(f"Erro ao transformar dados do Google Trends ({cache_key}): {str(e)}", exc_info=True)

def _extract_news(self, query) -> None:
    """
    Extrai notícias de fontes setoriais.
    
    Args:
        query: Parâmetros para a coleta de notícias
    """
    logger.info("Extraindo notícias setoriais")
    # TODO: Implementar coleta de notícias de fontes abertas
    self.cache['news_data'] = []

def _transform_data(self, etl_params: ETLParameters) -> Dict[str, Any]:
    """
    Transforma os dados extraídos em um formato padronizado.
    
    Args:
        etl_params: Parâmetros de entrada para o pipeline ETL
        
    Returns:
        Dicionário com os dados transformados
    """
    logger.info("Iniciando transformação de dados")
    
    transformed = {
        'market_segments': {},
        'search_trends': {},
        'news_articles': []
    }
    
    # 1. Processa dados do IBGE (se houver)
    if self.cache.get('ibge_data'):
        logger.info("Processando dados do IBGE")
        for table_id, data in self.cache['ibge_data'].items():
            try:
                segment_data = self.ibge_transformer.transform(data)
                if segment_data:
                    transformed['market_segments'].update(segment_data)
            except Exception as e:
                logger.error(f"Erro ao transformar dados do IBGE (Tabela {table_id}): {str(e)}", exc_info=True)
    
    # 2. Processa tendências de busca (se houver)
    if self.cache.get('google_trends_data'):
        logger.info("Processando dados do Google Trends")
        for keyword, trend_data in self.cache['google_trends_data'].items():
            try:
                trend = self.trends_transformer.transform(trend_data)
                if trend:
                    transformed['search_trends'][keyword] = trend
            except Exception as e:
                logger.error(f"Erro ao transformar dados do Google Trends (Termo: {keyword}): {str(e)}", exc_info=True)
    
    # 3. Processa notícias (se houver)
    if self.cache.get('news_data'):
        # TODO: Implementar transformação de notícias
        pass
        
    logger.info("Transformação de dados concluída")
    return transformed

def _persist_results(self, etl_output: ETLOutput) -> None:
    """
    Persiste os resultados do ETL no banco de dados.
    
    Args:
        etl_output: Dados processados a serem persistidos
        
    Raises:
        ETLError: Em caso de falha na persistência
    """
    try:
        # Inicializa o repositório
        etl_repo = ETLRepository(self.db)
            
        # Registra o início do processamento
        etl_repo.log_etl_run(
            request_id=etl_output.request_id,
            status='started',
            message='Iniciando processamento ETL',
            details={
                'market_segments_count': len(etl_output.market_segments),
                'search_trends_count': len(etl_output.search_trends),
                'news_articles_count': len(etl_output.news_articles)
            }
        )
            
        # Persiste os resultados
        etl_repo.create_etl_result(etl_output)
            
        logger.info(f"Resultados do ETL persistidos com sucesso para a requisição {etl_output.request_id}")
            
    except Exception as e:
        logger.error(f"Erro ao persistir resultados do ETL: {str(e)}", exc_info=True)
            
        # Registra a falha no log
        try:
            etl_repo = ETLRepository(self.db)
            etl_repo.log_etl_run(
                request_id=etl_output.request_id,
                status='failed',
                message=f'Falha ao persistir resultados: {str(e)}',
                details={
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
        except Exception as log_error:
            logger.error(f"Erro ao registrar falha no log: {str(log_error)}", exc_info=True)
            
        raise ETLError(f"Falha ao persistir resultados do ETL: {str(e)}") from e