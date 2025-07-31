"""
Serviço de carregamento de notícias no banco de dados.

Este módulo implementa a lógica para persistir notícias processadas
no banco de dados MongoDB, garantindo a integridade e consistência
dos dados.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from shared.schemas.news import NewsArticle, NewsSource
from ...services.repositories import NewsRepository

logger = logging.getLogger(__name__)


class NewsLoaderError(Exception):
    """Exceção para erros no carregamento de notícias."""
    pass


class NewsLoader:
    """
    Serviço para carregar notícias no banco de dados.

    Este serviço é responsável por gerenciar a persistência de notícias
    no banco de dados MongoDB, incluindo operações de inserção em lote,
    atualização e verificação de duplicatas.
    """


    def __init__(self, repository: NewsRepository = None):
        """
        Inicializa o carregador de notícias.

        Args:
            repository: Instância do repositório de notícias (opcional)
        """
        self.repository = repository or NewsRepository()

    async def initialize(self) -> None:
        """
        Inicializa o carregador, criando índices necessários.
        """
        try:
            await self.repository.create_indexes()
            logger.info("Índices do repositório de notícias criados com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar índices do repositório de notícias: {str(e)}")
            raise NewsLoaderError(f"Falha ao inicializar NewsLoader: {str(e)}")

    async def load_articles(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """
        Carrega uma lista de artigos no banco de dados.

        Este método realiza uma operação de upsert em lote, atualizando
        artigos existentes ou inserindo novos quando necessário.

        Args:
            articles: Lista de artigos para carregar

        Returns:
            Dicionário com estatísticas da operação:
            - 'processed': Número total de artigos processados
            - 'inserted': Número de novos artigos inseridos
            - 'updated': Número de artigos atualizados
            - 'errors': Número de erros ocorridos
        """
        if not articles:
            logger.warning("Nenhum artigo fornecido para carregamento")
            return {
                'processed': 0,
                'inserted': 0,
                'updated': 0,
                'errors': 0
            }

        stats = {
            'processed': len(articles),
            'inserted': 0,
            'updated': 0,
            'errors': 0
        }

        try:
            # Verifica se os artigos já existem no banco de dados
            existing_urls = await self._get_existing_article_urls(articles)

            # Prepara as operações de upsert em lote
            operations = []
            current_time = datetime.utcnow()

            for article in articles:
                try:
                    # Verifica se o artigo já existe
                    article_exists = article.url in existing_urls

                    # Atualiza os metadados
                    article.updated_at = current_time

                    if not article_exists:
                        article.created_at = current_time
                        stats['inserted'] += 1
                    else:
                        stats['updated'] += 1

                    # Prepara a operação de upsert
                    operation = UpdateOne(
                        {'url': article.url},
                        {'$set': article.dict(exclude={'id'})},
                        upsert=True
                    )
                    operations.append(operation)

                except Exception as e:
                    logger.error(f"Erro ao processar artigo {getattr(article, 'url', 'unknown')}: {str(e)}", 
                                exc_info=True)
                    stats['errors'] += 1

            # Executa as operações em lote, se houver
            if operations:
                try:
                    result = await self.repository.collection.bulk_write(operations, ordered=False)
                    logger.info(f"Operações de carregamento concluídas: {result.bulk_api_result}")
                except BulkWriteError as bwe:
                    # Loga erros de escrita em lote, mas continua a execução
                    logger.error(f"Erros durante operação em lote: {bwe.details}")
                    stats['errors'] += len(bwe.details.get('writeErrors', []))

            return stats

        except Exception as e:
            logger.error(f"Erro ao carregar artigos: {str(e)}", exc_info=True)
            raise NewsLoaderError(f"Falha ao carregar artigos: {str(e)}")

    async def _get_existing_article_urls(self, articles: List[NewsArticle]) -> set:
        """
        Obtém os URLs dos artigos que já existem no banco de dados.

        Args:
            articles: Lista de artigos para verificar

        Returns:
            Conjunto de URLs que já existem no banco de dados
        """
        urls = {article.url for article in articles if hasattr(article, 'url') and article.url}

        if not urls:
            return set()

        # Busca os URLs existentes no banco de dados
        cursor = self.repository.collection.find(
            {'url': {'$in': list(urls)}},
            {'url': 1, '_id': 0}
        )

        existing_urls = {doc['url'] for doc in await cursor.to_list(length=len(urls))}
        return existing_urls

    async def update_article_sentiment(
        self,
        article_id: str,
        sentiment_score: float,
        keywords: List[str] = None
    ) -> bool:
        """
        Atualiza a pontuação de sentimento e palavras-chave de um artigo.

        Args:
            article_id: ID do artigo
            sentiment_score: Nova pontuação de sentimento
            keywords: Lista de palavras-chave (opcional)

        Returns:
            True se a atualização for bem-sucedida, False caso contrário
        """
        try:
            return await self.repository.update_article_sentiment(
                article_id=article_id,
                sentiment_score=sentiment_score,
                keywords=keywords
            )
        except Exception as e:
            logger.error(f"Erro ao atualizar sentimento do artigo {article_id}: {str(e)}", exc_info=True)
            raise NewsLoaderError(f"Falha ao atualizar sentimento do artigo: {str(e)}")

    async def get_articles_without_sentiment(self, limit: int = 100) -> List[NewsArticle]:
        """
        Obtém artigos que ainda não tiveram o sentimento analisado.

        Args:
            limit: Número máximo de artigos a retornar

        Returns:
            Lista de artigos sem análise de sentimento
        """
        try:
            return await self.repository.get_articles_without_sentiment(limit=limit)
        except Exception as e:
            logger.error(f"Erro ao buscar artigos sem sentimento: {str(e)}", exc_info=True)
            raise NewsLoaderError(f"Falha ao buscar artigos sem sentimento: {str(e)}")

    async def cleanup_old_articles(self, days_to_keep: int = 90) -> int:
        """
        Remove artigos mais antigos que o número especificado de dias.

        Args:
            days_to_keep: Número de dias para manter os artigos

        Returns:
            Número de artigos removidos
        """
        try:
            deleted_count = await self.repository.delete_old_articles(days=days_to_keep)
            logger.info(f"Removidos {deleted_count} artigos com mais de {days_to_keep} dias")
            return deleted_count
        except Exception as e:
            logger.error(f"Erro ao limpar artigos antigos: {str(e)}", exc_info=True)
            raise NewsLoaderError(f"Falha ao limpar artigos antigos: {str(e)}")

    async def get_article_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas sobre os artigos armazenados.

        Returns:
            Dicionário com estatísticas dos artigos
        """
        try:
            stats = {}

            # Contagem total de artigos
            total_articles = await self.repository.count()
            stats['total_articles'] = total_articles

            # Contagem por fonte
            stats['by_source'] = await self.repository.get_article_count_by_source()

            # Contagem por categoria
            stats['by_category'] = await self.repository.get_article_count_by_category()

            # Média de sentimento por categoria
            stats['avg_sentiment_by_category'] = await self.repository.get_average_sentiment_by_category()

            # Artigos por período
            now = datetime.utcnow()
            stats['last_24h'] = await self.repository.count({
                'published_at': {
                    '$gte': now - timedelta(days=1),
                    '$lte': now
                }
            })

            stats['last_7_days'] = await self.repository.count({
                'published_at': {
                    '$gte': now - timedelta(days=7),
                    '$lte': now
                }
            })

            stats['last_30_days'] = await self.repository.count({
                'published_at': {
                    '$gte': now - timedelta(days=30),
                    '$lte': now
                }
            })

            return stats

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de artigos: {str(e)}", exc_info=True)
            raise NewsLoaderError(f"Falha ao obter estatísticas de artigos: {str(e)}")
