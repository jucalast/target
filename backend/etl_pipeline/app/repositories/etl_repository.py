"""
Repositório para gerenciamento de resultados do ETL no PostgreSQL.

Este módulo fornece uma interface para persistir e recuperar resultados
de execuções do pipeline ETL no banco de dados PostgreSQL.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid
import logging

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from shared.db.models.etl_models import (
    ETLResultModel, 
    MarketSegmentModel, 
    MarketMetricModel, 
    DataPointModel,
    SearchTrendModel,
    NewsArticleModel,
    ETLRunLogModel,
    etl_result_news
)
from shared.db.repositories.postgres_repository import BasePostgresRepository
from shared.schemas.etl_output import ETLOutput, MarketSegment, MarketMetric, DataPoint, SearchTrend, NewsArticle
from shared.schemas.etl_parameters import ETLParameters
from shared.schemas.nlp_features import NLPFeatures
from shared.utils.exceptions import DatabaseError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ETLRepository(BasePostgresRepository):
    """
    Repositório para operações com resultados de ETL.

    Esta classe estende o repositório base PostgreSQL para fornecer
    operações específicas para o domínio de ETL.
    """


    def __init__(self, db: Session):
        """
        Inicializa o repositório ETL.

        Args:
            db: Sessão do SQLAlchemy
        """
        super().__init__(ETLResultModel, db)


    def create_etl_result(self, etl_output: ETLOutput) -> ETLResultModel:
        """
        Cria um novo resultado de ETL no banco de dados.

        Args:
            etl_output: Objeto ETLOutput com os dados processados

        Returns:
            ETLResultModel: O registro criado

        Raises:
            DatabaseError: Em caso de erro no banco de dados
            ValidationError: Em caso de erro de validação
        """
        try:
            # Inicia uma transação
            with self.db.begin_nested():
                # Cria o registro principal do resultado ETL
                etl_result = ETLResultModel(
                    request_id=etl_output.request_id,
                    timestamp=etl_output.timestamp,
                    processing_time=etl_output.processing_time,
                    user_input=etl_output.raw_data.get('user_input', {}),
                    nlp_features=etl_output.raw_data.get('nlp_features', {}),
                    raw_data=etl_output.raw_data,
                    stats=etl_output.stats
                )

                self.db.add(etl_result)
                self.db.flush()  # Obtém o ID do resultado ETL

                # Processa os segmentos de mercado
                self._process_market_segments(etl_result.id, etl_output.market_segments)

                # Processa as tendências de busca
                self._process_search_trends(etl_result.id, etl_output.search_trends)

                # Processa as notícias
                self._process_news_articles(etl_result.id, etl_output.news_articles)

                # Registra o log de conclusão
                self.log_etl_run(
                    request_id=etl_output.request_id,
                    status='completed',
                    message='ETL processado com sucesso',
                    details={
                        'market_segments_count': len(etl_output.market_segments),
                        'search_trends_count': len(etl_output.search_trends),
                        'news_articles_count': len(etl_output.news_articles)
                    }
                )

                return etl_result

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Erro de integridade ao criar resultado ETL: {str(e)}")
            raise ValidationError("Dados inválidos para criação de resultado ETL") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar resultado ETL: {str(e)}")
            raise DatabaseError("Falha ao criar resultado ETL") from e


    def _process_market_segments(self, etl_result_id: uuid.UUID, segments: Dict[str, MarketSegment]) -> None:
        """
        Processa e salva os segmentos de mercado no banco de dados.

        Args:
            etl_result_id: ID do resultado ETL
            segments: Dicionário de segmentos de mercado
        """
        for segment_name, segment in segments.items():
            # Cria o segmento
            segment_model = MarketSegmentModel(
                name=segment.name,
                description=segment.description,
                etl_result_id=etl_result_id
            )
            self.db.add(segment_model)
            self.db.flush()  # Obtém o ID do segmento

            # Processa as métricas do segmento
            self._process_market_metrics(segment_model.id, segment.metrics)


    def _process_market_metrics(self, segment_id: uuid.UUID, metrics: Dict[str, MarketMetric]) -> None:
        """
        Processa e salva as métricas de mercado no banco de dados.

        Args:
            segment_id: ID do segmento de mercado
            metrics: Dicionário de métricas de mercado
        """
        for metric_name, metric in metrics.items():
            # Cria o valor atual da métrica
            current_value = DataPointModel(
                value=metric.current_value.value,
                source=metric.current_value.source,
                timestamp=metric.current_value.timestamp,
                confidence=metric.current_value.confidence,
                quality=metric.current_value.quality,
                meta_info=metric.current_value.metadata  # Usando meta_info em vez de metadata
            )
            self.db.add(current_value)
            self.db.flush()  # Obtém o ID do data point

            # Cria a métrica
            metric_model = MarketMetricModel(
                name=metric.name,
                description=metric.description,
                unit=metric.unit,
                trend=metric.trend,
                segment_id=segment_id,
                current_value_id=current_value.id
            )
            self.db.add(metric_model)
            self.db.flush()  # Obtém o ID da métrica

            # Atualiza a referência no data point
            current_value.metric_id = metric_model.id

            # Processa os valores históricos
            for hist_value in metric.historical_values:
                hist_point = DataPointModel(
                    value=hist_value.value,
                    source=hist_value.source,
                    timestamp=hist_value.timestamp,
                    confidence=hist_value.confidence,
                    quality=hist_value.quality,
                    meta_info=hist_value.metadata,  # Usando meta_info em vez de metadata
                    metric_id=metric_model.id
                )
                self.db.add(hist_point)


    def _process_search_trends(self, etl_result_id: uuid.UUID, trends: Dict[str, SearchTrend]) -> None:
        """
        Processa e salva as tendências de busca no banco de dados.

        Args:
            etl_result_id: ID do resultado ETL
            trends: Dicionário de tendências de busca
        """
        for keyword, trend in trends.items():
            trend_model = SearchTrendModel(
                keyword=trend.keyword,
                values=[v.dict() for v in trend.values],
                related_queries=trend.related_queries,
                interest_by_region=trend.interest_by_region,
                etl_result_id=etl_result_id
            )
            self.db.add(trend_model)


    def _process_news_articles(self, etl_result_id: uuid.UUID, articles: List[NewsArticle]) -> None:
        """
        Processa e salva os artigos de notícias no banco de dados.

        Args:
            etl_result_id: ID do resultado ETL
            articles: Lista de artigos de notícias
        """
        for article in articles:
            # Verifica se o artigo já existe (pela URL ou título + data)
            existing_article = self.db.query(NewsArticleModel).filter(
                NewsArticleModel.url == str(article.url) if article.url else False,
                NewsArticleModel.title == article.title,
                NewsArticleModel.published_at == article.published_at
            ).first()

            if existing_article:
                # Se o artigo já existe, apenas adiciona a associação
                self.db.execute(
                    etl_result_news.insert().values(
                        etl_result_id=etl_result_id,
                        news_article_id=existing_article.id
                    )
                )
            else:
                # Cria um novo artigo
                article_model = NewsArticleModel(
                    title=article.title,
                    source=article.source,
                    url=str(article.url) if article.url else None,
                    published_at=article.published_at,
                    summary=article.summary,
                    sentiment=article.sentiment,
                    keywords=article.keywords
                )
                self.db.add(article_model)
                self.db.flush()  # Obtém o ID do artigo

                # Cria a associação com o resultado ETL
                self.db.execute(
                    etl_result_news.insert().values(
                        etl_result_id=etl_result_id,
                        news_article_id=article_model.id
                    )
                )


    def get_etl_result(self, request_id: str) -> Optional[ETLResultModel]:
        """
        Obtém um resultado de ETL pelo ID da requisição.

        Args:
            request_id: ID da requisição

        Returns:
            ETLResultModel: O resultado do ETL ou None se não encontrado
        """
        try:
            return self.db.query(ETLResultModel)\
                .options(
                    joinedload(ETLResultModel.market_segments)\
                        .joinedload(MarketSegmentModel.metrics)\
                        .joinedload(MarketMetricModel.current_value),
                    joinedload(ETLResultModel.market_segments)\
                        .joinedload(MarketSegmentModel.metrics)\
                        .joinedload(MarketMetricModel.historical_values),
                    joinedload(ETLResultModel.search_trends),
                    joinedload(ETLResultModel.news_articles)
                )\
                .filter(ETLResultModel.request_id == request_id)\
                .first()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar resultado ETL {request_id}: {str(e)}")
            raise DatabaseError(f"Falha ao buscar resultado ETL {request_id}") from e


    def log_etl_run(self, request_id: str, status: str, message: Optional[str] = None, 
                   details: Optional[Dict[str, Any]] = None) -> ETLRunLogModel:
        """
        Registra um log de execução do ETL.

        Args:
            request_id: ID da requisição
            status: Status da execução ('started', 'completed', 'failed')
            message: Mensagem descritiva (opcional)
            details: Detalhes adicionais (opcional)

        Returns:
            ETLRunLogModel: O registro de log criado
        """
        try:
            log = ETLRunLogModel(
                request_id=request_id,
                status=status,
                message=message,
                details=details or {}
            )
            self.db.add(log)
            self.db.commit()
            return log
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao registrar log de execução ETL: {str(e)}")
            raise DatabaseError("Falha ao registrar log de execução ETL") from e


    def get_etl_run_logs(self, request_id: str) -> List[ETLRunLogModel]:
        """
        Obtém os logs de execução de uma requisição ETL.

        Args:
            request_id: ID da requisição

        Returns:
            List[ETLRunLogModel]: Lista de logs de execução
        """
        try:
            return self.db.query(ETLRunLogModel)\
                .filter(ETLRunLogModel.request_id == request_id)\
                .order_by(ETLRunLogModel.created_at.desc())\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar logs de execução ETL {request_id}: {str(e)}")
            raise DatabaseError(f"Falha ao buscar logs de execução ETL {request_id}") from e


    def get_recent_etl_results(self, limit: int = 10) -> List[ETLResultModel]:
        """
        Obtém os resultados de ETL mais recentes.

        Args:
            limit: Número máximo de resultados a retornar

        Returns:
            List[ETLResultModel]: Lista de resultados de ETL
        """
        try:
            return self.db.query(ETLResultModel)\
                .order_by(ETLResultModel.timestamp.desc())\
                .limit(limit)\
                .all()
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar resultados recentes de ETL: {str(e)}")
            raise DatabaseError("Falha ao buscar resultados recentes de ETL") from e
