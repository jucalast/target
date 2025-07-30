"""
Repositório para operações de persistência de notícias.

Este módulo implementa operações específicas para manipulação de notícias no MongoDB,
extendendo a funcionalidade do repositório base.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, TEXT

from shared.schemas.news import NewsArticle, NewsSource, NewsSearchResult, NewsCategory
from shared.db.repositories.base_repository import BaseRepository

class NewsRepository(BaseRepository[NewsArticle, str]):
    """
    Repositório para operações de persistência de notícias.
    
    Esta classe estende o repositório base para fornecer operações específicas
    para manipulação de notícias no MongoDB.
    """
    
    def __init__(self):
        """Inicializa o repositório de notícias."""
        super().__init__(
            collection_name="news_articles",
            model_class=NewsArticle
        )
    
    async def create_indexes(self) -> None:
        """Cria índices para otimização de consultas."""
        # Índice de texto para busca full-text
        await self.collection.create_index([
            ("title", TEXT),
            ("content", TEXT),
            ("keywords", TEXT)
        ], name="search_text")
        
        # Índices para consultas comuns
        await self.collection.create_index([("published_at", DESCENDING)])
        await self.collection.create_index([("source.domain", ASCENDING)])
        await self.collection.create_index([("category", ASCENDING)])
        await self.collection.create_index([("language", ASCENDING)])
        await self.collection.create_index([("sentiment_score", ASCENDING)])
        
        # Índice composto para consultas por data e categoria
        await self.collection.create_index([
            ("published_at", DESCENDING),
            ("category", ASCENDING)
        ])
        
        # Índice para garantir unicidade de URLs
        await self.collection.create_index(
            [("url", ASCENDING)],
            unique=True,
            partialFilterExpression={"url": {"$type": "string"}}
        )
    
    async def search_articles(
        self,
        query: str = None,
        categories: List[str] = None,
        sources: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        min_sentiment: float = None,
        max_sentiment: float = None,
        language: str = "pt-BR",
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "published_at",
        sort_order: str = "desc"
    ) -> NewsSearchResult:
        """
        Busca artigos de notícias com base em critérios de pesquisa.
        
        Args:
            query: Termo de busca para pesquisa full-text
            categories: Lista de categorias para filtrar
            sources: Lista de domínios de fontes para filtrar
            start_date: Data de início para filtrar por data de publicação
            end_date: Data de término para filtrar por data de publicação
            min_sentiment: Pontuação mínima de sentimento (-1 a 1)
            max_sentiment: Pontuação máxima de sentimento (-1 a 1)
            language: Código de idioma para filtrar (padrão: pt-BR)
            page: Número da página (começando em 1)
            page_size: Número de itens por página
            sort_by: Campo para ordenação (padrão: published_at)
            sort_order: Ordem de classificação (asc ou desc)
            
        Returns:
            Instância de NewsSearchResult com os resultados da busca
        """
        # Constrói a consulta
        search_query = {}
        
        # Filtro por idioma
        if language:
            search_query["language"] = language
        
        # Filtro por texto (busca full-text)
        if query:
            search_query["$text"] = {"$search": query}
        
        # Filtro por categorias
        if categories:
            search_query["category"] = {"$in": categories}
        
        # Filtro por fontes
        if sources:
            search_query["source.domain"] = {"$in": sources}
        
        # Filtro por data
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            search_query["published_at"] = date_filter
        
        # Filtro por sentimento
        sentiment_filter = {}
        if min_sentiment is not None:
            sentiment_filter["$gte"] = min_sentiment
        if max_sentiment is not None:
            sentiment_filter["$lte"] = max_sentiment
        if sentiment_filter:
            search_query["sentiment_score"] = sentiment_filter
        
        # Ordenação
        sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
        sort_field = sort_by if sort_by != "relevance" else "score"
        
        # Se for uma busca por relevância, adiciona a pontuação de relevância
        if query:
            pipeline = [
                {"$match": search_query},
                {"$addFields": {"score": {"$meta": "textScore"}}},
                {"$sort": {(sort_field, sort_direction)}},
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size}
            ]
            
            # Conta o total de resultados
            count_pipeline = [
                {"$match": search_query},
                {"$count": "total"}
            ]
            
            total_result = await self.collection.aggregate(count_pipeline).to_list(1)
            total = total_result[0]["total"] if total_result else 0
            
            # Executa a consulta
            cursor = self.collection.aggregate(pipeline)
            articles = [self._convert_to_model(doc) for doc in await cursor.to_list(length=page_size)]
        else:
            # Consulta sem texto (sem pontuação de relevância)
            cursor = self.collection.find(search_query)
            
            # Conta o total de resultados
            total = await self.collection.count_documents(search_query)
            
            # Aplica ordenação e paginação
            cursor = cursor.sort(sort_field, sort_direction)
            cursor = cursor.skip((page - 1) * page_size).limit(page_size)
            
            articles = [self._convert_to_model(doc) for doc in await cursor.to_list(length=page_size)]
        
        # Calcula as facetas para filtragem
        facets = await self._get_search_facets(
            search_query=search_query,
            query=query,
            categories=categories,
            sources=sources,
            language=language
        )
        
        return NewsSearchResult(
            query=query or "",
            total_results=total,
            page=page,
            page_size=page_size,
            articles=articles,
            facets=facets
        )
    
    async def _get_search_facets(
        self,
        search_query: Dict[str, Any],
        query: str = None,
        categories: List[str] = None,
        sources: List[str] = None,
        language: str = "pt-BR"
    ) -> Dict[str, Dict[str, int]]:
        """
        Obtém facetas para filtragem de resultados de busca.
        
        Args:
            search_query: Consulta de pesquisa atual
            query: Termo de busca
            categories: Categorias selecionadas
            sources: Fontes selecionadas
            language: Idioma para filtrar
            
        Returns:
            Dicionário com as facetas para filtragem
        """
        facets = {}
        
        # Faceta por categoria
        if not categories:
            pipeline = [
                {"$match": {**search_query, "category": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            category_results = await self.collection.aggregate(pipeline).to_list(None)
            facets["categories"] = {item["_id"]: item["count"] for item in category_results}
        
        # Faceta por fonte
        if not sources:
            pipeline = [
                {"$match": {**search_query, "source.domain": {"$exists": True, "$ne": None}}},
                {"$group": {
                    "_id": {
                        "domain": "$source.domain",
                        "name": "$source.name"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}  # Limita a 10 fontes mais relevantes
            ]
            
            source_results = await self.collection.aggregate(pipeline).to_list(None)
            facets["sources"] = {
                f"{item['_id']['domain']}": {
                    "name": item['_id']['name'],
                    "count": item["count"]
                }
                for item in source_results
            }
        
        # Faceta por data (últimos 30 dias)
        date_pipeline = [
            {
                "$match": {
                    **search_query,
                    "published_at": {
                        "$gte": datetime.utcnow() - timedelta(days=30),
                        "$lte": datetime.utcnow()
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$published_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        date_results = await self.collection.aggregate(date_pipeline).to_list(None)
        facets["dates"] = {item["_id"]: item["count"] for item in date_results}
        
        return facets
    
    async def get_latest_articles(
        self,
        limit: int = 10,
        category: str = None,
        source: str = None,
        language: str = "pt-BR"
    ) -> List[NewsArticle]:
        """
        Obtém os artigos mais recentes.
        
        Args:
            limit: Número máximo de artigos a retornar
            category: Categoria para filtrar (opcional)
            source: Domínio da fonte para filtrar (opcional)
            language: Código de idioma (padrão: pt-BR)
            
        Returns:
            Lista de artigos mais recentes
        """
        query = {"language": language}
        
        if category:
            query["category"] = category
            
        if source:
            query["source.domain"] = source
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def get_articles_by_source(
        self,
        source_domain: str,
        limit: int = 10,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> List[NewsArticle]:
        """
        Obtém artigos de uma fonte específica.
        
        Args:
            source_domain: Domínio da fonte
            limit: Número máximo de artigos a retornar
            start_date: Data de início para filtrar
            end_date: Data de término para filtrar
            
        Returns:
            Lista de artigos da fonte especificada
        """
        query = {"source.domain": source_domain}
        
        # Filtro por data
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["published_at"] = date_filter
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def get_articles_by_category(
        self,
        category: str,
        limit: int = 10,
        language: str = "pt-BR"
    ) -> List[NewsArticle]:
        """
        Obtém artigos por categoria.
        
        Args:
            category: Categoria dos artigos
            limit: Número máximo de artigos a retornar
            language: Código de idioma (padrão: pt-BR)
            
        Returns:
            Lista de artigos da categoria especificada
        """
        query = {
            "category": category,
            "language": language
        }
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def get_articles_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime = None,
        category: str = None,
        source: str = None,
        limit: int = 100
    ) -> List[NewsArticle]:
        """
        Obtém artigos publicados em um intervalo de datas.
        
        Args:
            start_date: Data de início
            end_date: Data de término (opcional, padrão: agora)
            category: Categoria para filtrar (opcional)
            source: Domínio da fonte para filtrar (opcional)
            limit: Número máximo de artigos a retornar
            
        Returns:
            Lista de artigos publicados no intervalo de datas
        """
        if end_date is None:
            end_date = datetime.utcnow()
        
        query = {
            "published_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        if category:
            query["category"] = category
            
        if source:
            query["source.domain"] = source
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def get_articles_by_sentiment(
        self,
        min_score: float = 0.1,
        max_score: float = 1.0,
        limit: int = 10,
        category: str = None,
        source: str = None
    ) -> List[NewsArticle]:
        """
        Obtém artigos com pontuação de sentimento dentro de um intervalo.
        
        Args:
            min_score: Pontuação mínima de sentimento (-1 a 1)
            max_score: Pontuação máxima de sentimento (-1 a 1)
            limit: Número máximo de artigos a retornar
            category: Categoria para filtrar (opcional)
            source: Domínio da fonte para filtrar (opcional)
            
        Returns:
            Lista de artigos com pontuação de sentimento no intervalo especificado
        """
        query = {
            "sentiment_score": {
                "$gte": min_score,
                "$lte": max_score
            }
        }
        
        if category:
            query["category"] = category
            
        if source:
            query["source.domain"] = source
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def get_article_by_url(self, url: str) -> Optional[NewsArticle]:
        """
        Obtém um artigo pela URL.
        
        Args:
            url: URL do artigo
            
        Returns:
            O artigo correspondente à URL ou None se não encontrado
        """
        article = await self.collection.find_one({"url": url})
        return self._convert_to_model(article) if article else None
    
    async def article_exists(self, url: str) -> bool:
        """
        Verifica se um artigo com a URL especificada já existe.
        
        Args:
            url: URL do artigo
            
        Returns:
            True se o artigo existir, False caso contrário
        """
        return await self.collection.count_documents({"url": url}, limit=1) > 0
    
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
        update_data = {
            "sentiment_score": sentiment_score,
            "updated_at": datetime.utcnow()
        }
        
        if keywords is not None:
            update_data["keywords"] = keywords
        
        result = await self.collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    
    async def get_article_count_by_source(self) -> Dict[str, int]:
        """
        Obtém a contagem de artigos por fonte.
        
        Returns:
            Dicionário com a contagem de artigos por domínio de fonte
        """
        pipeline = [
            {"$group": {"_id": "$source.domain", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def get_article_count_by_category(self) -> Dict[str, int]:
        """
        Obtém a contagem de artigos por categoria.
        
        Returns:
            Dicionário com a contagem de artigos por categoria
        """
        pipeline = [
            {"$match": {"category": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in results}
    
    async def get_average_sentiment_by_category(self) -> Dict[str, float]:
        """
        Calcula a média de sentimento por categoria.
        
        Returns:
            Dicionário com a média de sentimento por categoria
        """
        pipeline = [
            {
                "$match": {
                    "sentiment_score": {"$exists": True, "$ne": None},
                    "category": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "avg_sentiment": {"$avg": "$sentiment_score"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"avg_sentiment": -1}}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["avg_sentiment"] for item in results}
    
    async def get_trending_keywords(
        self,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtém as palavras-chave mais frequentes em um período.
        
        Args:
            days: Número de dias para trás a partir de agora
            limit: Número máximo de palavras-chave a retornar
            
        Returns:
            Lista de dicionários com palavra-chave e contagem
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "published_at": {"$gte": start_date},
                    "keywords": {"$exists": True, "$ne": []}
                }
            },
            {"$unwind": "$keywords"},
            {"$group": {"_id": "$keywords", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(None)
        return [{"keyword": item["_id"], "count": item["count"]} for item in results]
    
    async def get_articles_without_sentiment(self, limit: int = 100) -> List[NewsArticle]:
        """
        Obtém artigos que ainda não tiveram o sentimento analisado.
        
        Args:
            limit: Número máximo de artigos a retornar
            
        Returns:
            Lista de artigos sem análise de sentimento
        """
        query = {
            "sentiment_score": {"$exists": False},
            "content": {"$exists": True, "$ne": ""}
        }
        
        cursor = self.collection.find(query)
        cursor = cursor.sort("published_at", DESCENDING)
        cursor = cursor.limit(limit)
        
        return [self._convert_to_model(doc) for doc in await cursor.to_list(length=limit)]
    
    async def delete_old_articles(self, days: int = 90) -> int:
        """
        Remove artigos mais antigos que o número especificado de dias.
        
        Args:
            days: Número de dias para manter os artigos
            
        Returns:
            Número de artigos removidos
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.collection.delete_many({
            "published_at": {"$lt": cutoff_date}
        })
        
        return result.deleted_count
