"""
Transformador de Notícias

Este módulo contém classes para processar e transformar notícias coletadas
de várias fontes em um formato padronizado para análise posterior.
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter

import spacy
from spacy.lang.pt.stop_words import STOP_WORDS as PT_STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np

from shared.schemas.news import NewsArticle, NewsSource, NewsCategory
from shared.schemas.etl_output import MarketSegment, MarketMetric, DataPoint, DataSource, DataQualityLevel

logger = logging.getLogger(__name__)


class NewsTransformerError(Exception):
    """Exceção personalizada para erros no processamento de notícias."""
    pass


class NewsTransformer:
    """
    Transforma notícias brutas em insights estruturados.

    Esta classe é responsável por:
    - Processar texto (limpeza, normalização)
    - Extrair palavras-chave e tópicos
    - Analisar sentimento
    - Identificar entidades nomeadas
    - Agrupar notícias relacionadas
    - Gerar métricas de mercado
    """


    def __init__(self, nlp_model: str = 'pt_core_news_lg'):
        """
        Inicializa o transformador de notícias.

        Args:
            nlp_model: Nome do modelo spaCy a ser carregado
        """
        self.nlp_model_name = nlp_model
        self.nlp = None
        self.vectorizer = None
        self.lda = None

        # Configurações
        self.max_keywords = 10
        self.num_topics = 5
        self.topic_words = 5
        self.cluster_size = 5

        # Inicializa o modelo de linguagem
        self._load_models()


    def _load_models(self) -> None:
        """Carrega os modelos de NLP necessários."""
        try:
            logger.info(f"Carregando modelo de linguagem: {self.nlp_model_name}")
            self.nlp = spacy.load(self.nlp_model_name)

            # Configura o pipeline personalizado para melhor desempenho
            if not self.nlp.has_pipe('sentencizer'):
                self.nlp.add_pipe('sentencizer')

            # Desativa componentes não utilizados para melhor desempenho
            disable_pipes = ['parser', 'ner', 'textcat']
            for pipe in disable_pipes:
                if pipe in self.nlp.pipe_names:
                    self.nlp.disable_pipe(pipe)

            logger.info("Modelo de linguagem carregado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo de linguagem: {str(e)}")
            raise NewsTransformerError(f"Falha ao carregar modelo de linguagem: {str(e)}")


    def transform(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Processa uma lista de artigos de notícias.

        Args:
            articles: Lista de artigos de notícias para processar

        Returns:
            Dicionário com os resultados do processamento, incluindo:
            - articles: Lista de artigos processados
            - keywords: Palavras-chave extraídas
            - topics: Tópicos identificados
            - sentiment: Análise de sentimento agregada
            - entities: Entidades nomeadas mais frequentes
            - clusters: Grupos de notícias relacionadas
        """
        if not articles:
            logger.warning("Nenhum artigo fornecido para processamento")
            return {}

        logger.info(f"Iniciando processamento de {len(articles)} artigos de notícias")

        try:
            # 1. Processa cada artigo individualmente
            processed_articles = []
            all_texts = []

            for article in articles:
                processed = self._process_article(article)
                processed_articles.append(processed)
                all_texts.append(processed.content)

            # 2. Análise de tópicos
            topics = self._extract_topics(all_texts)

            # 3. Agrupamento de notícias relacionadas
            clusters = self._cluster_articles(processed_articles)

            # 4. Extrai entidades nomeadas mais frequentes
            entities = self._extract_common_entities(processed_articles)

            # 5. Análise de sentimento agregada
            sentiment = self._aggregate_sentiment(processed_articles)

            # 6. Gera métricas de mercado
            market_metrics = self._generate_market_metrics(processed_articles, topics, sentiment)

            logger.info("Processamento de notícias concluído com sucesso")

            return {
                'articles': processed_articles,
                'topics': topics,
                'clusters': clusters,
                'sentiment': sentiment,
                'entities': entities,
                'market_metrics': market_metrics
            }

        except Exception as e:
            logger.error(f"Erro ao processar artigos: {str(e)}", exc_info=True)
            raise NewsTransformerError(f"Falha ao processar artigos: {str(e)}")


    def _process_article(self, article: NewsArticle) -> NewsArticle:
        """
        Processa um único artigo de notícia.

        Args:
            article: Artigo a ser processado

        Returns:
            Artigo processado com campos adicionais
        """
        if not article.content:
            return article

        try:
            # Processa o texto com spaCy
            doc = self.nlp(article.content)

            # Extrai frases para resumo (primeiras 3 frases)
            sentences = [sent.text for sent in doc.sents][:3]
            summary = ' '.join(sentences)

            # Extrai entidades nomeadas
            entities = []
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })

            # Calcula sentimento (simplificado - em produção, usar modelo específico)
            sentiment_score = self._calculate_sentiment(doc)

            # Extrai palavras-chave
            keywords = self._extract_keywords(doc)

            # Atualiza o artigo com os dados processados
            article.summary = summary
            article.entities = entities
            article.sentiment_score = sentiment_score
            article.keywords = keywords
            article.metadata.update({
                'processed_at': datetime.utcnow().isoformat(),
                'word_count': len(doc),
                'sentence_count': len(list(doc.sents)),
                'entity_count': len(entities)
            })

            return article

        except Exception as e:
            logger.error(f"Erro ao processar artigo: {str(e)}", exc_info=True)
            return article


    def _calculate_sentiment(self, doc) -> float:
        """
        Calcula uma pontuação de sentimento para o documento.

        Nota: Esta é uma implementação simplificada. Em produção,
        considere usar um modelo de análise de sentimento treinado.

        Args:
            doc: Documento spaCy processado

        Returns:
            Pontuação de sentimento entre -1 (negativo) e 1 (positivo)
        """
        # Lista de palavras positivas e negativas em português
        positive_words = {
            'bom', 'bem', 'ótimo', 'excelente', 'maravilhoso', 'incrível',
            'positivo', 'ótima', 'ótimos', 'ótimas', 'feliz', 'alegre',
            'sucesso', 'crescer', 'crescimento', 'lucro', 'lucrativo',
            'avanço', 'avançar', 'melhor', 'melhorar', 'ótimo', 'ótima'
        }

        negative_words = {
            'ruim', 'péssimo', 'terrível', 'horrível', 'negativo',
            'triste', 'tristeza', 'fracasso', 'fracassar', 'cair', 'queda',
            'prejuízo', 'prejudicar', 'pior', 'piorar', 'ruim', 'ruins'
        }

        # Conta palavras positivas e negativas
        pos_count = sum(1 for token in doc if token.lemma_.lower() in positive_words)
        neg_count = sum(1 for token in doc if token.lemma_.lower() in negative_words)

        # Calcula a pontuação de sentimento
        total = pos_count + neg_count
        if total == 0:
            return 0.0

        sentiment = (pos_count - neg_count) / total
        return max(-1.0, min(1.0, sentiment))  # Garante o intervalo [-1, 1]


    def _extract_keywords(self, doc, top_n: int = 10) -> List[str]:
        """
        Extrai as principais palavras-chave do documento.

        Args:
            doc: Documento spaCy processado
            top_n: Número de palavras-chave a retornar

        Returns:
            Lista de palavras-chave ordenadas por relevância
        """
        # Filtra tokens relevantes
        words = []
        for token in doc:
            # Considera apenas substantivos, adjetivos e verbos
            if (token.pos_ in {'NOUN', 'ADJ', 'VERB'} and 
                not token.is_stop and 
                not token.is_punct and 
                not token.like_num and
                len(token.text) > 2):
                words.append(token.lemma_.lower())

        # Conta a frequência das palavras
        word_freq = Counter(words)

        # Retorna as n palavras mais comuns
        return [word for word, _ in word_freq.most_common(top_n)]


    def _extract_topics(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extrai tópicos principais dos textos usando LDA.

        Args:
            texts: Lista de textos para análise

        Returns:
            Lista de tópicos com suas palavras-chave
        """
        if not texts:
            return []

        try:
            # Cria a matriz de contagem de termos
            vectorizer = CountVectorizer(
                max_df=0.95, 
                min_df=2,
                stop_words=list(PT_STOP_WORDS),
                max_features=1000
            )

            # Ajusta o vetorizador aos textos
            doc_term_matrix = vectorizer.fit_transform(texts)

            # Treina o modelo LDA
            lda = LatentDirichletAllocation(
                n_components=min(self.num_topics, len(texts)),
                random_state=42,
                learning_method='online'
            )

            lda.fit(doc_term_matrix)

            # Extrai as palavras-chave para cada tópico
            feature_names = vectorizer.get_feature_names_out()
            topics = []

            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[:-self.topic_words - 1:-1]
                top_words = [feature_names[i] for i in top_words_idx]

                topics.append({
                    'topic_id': topic_idx,
                    'keywords': top_words,
                    'weight': float(topic.sum())  # Peso do tópico
                })

            return topics

        except Exception as e:
            logger.error(f"Erro ao extrair tópicos: {str(e)}", exc_info=True)
            return []


    def _cluster_articles(self, articles: List[NewsArticle]) -> List[Dict[str, Any]]:
        """
        Agrupa artigos relacionados usando similaridade semântica.

        Args:
            articles: Lista de artigos para agrupar

        Returns:
            Lista de clusters com artigos relacionados
        """
        if not articles or len(articles) < 2:
            return []

        try:
            # Prepara os textos para vetorização
            texts = [f"{a.title} {a.summary or a.content[:500]}" for a in articles]

            # Vetoriza os textos usando TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=list(PT_STOP_WORDS)
            )

            X = vectorizer.fit_transform(texts)

            # Define o número de clusters (máximo 5 ou metade dos artigos)
            n_clusters = min(5, max(2, len(articles) // 2))

            # Aplica K-means para agrupar os artigos
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )

            clusters = kmeans.fit_predict(X)

            # Organiza os artigos por cluster
            cluster_groups = {i: [] for i in range(n_clusters)}
            for idx, cluster_id in enumerate(clusters):
                cluster_groups[cluster_id].append(articles[idx].id or idx)

            # Retorna os clusters formatados
            return [
                {
                    'cluster_id': cluster_id,
                    'article_ids': article_ids,
                    'size': len(article_ids),
                    'keywords': self._extract_cluster_keywords(
                        [articles[i] for i in range(len(articles)) if i in article_ids]
                    )
                }
                for cluster_id, article_ids in cluster_groups.items()
                if article_ids  # Apenas clusters não vazios
            ]

        except Exception as e:
            logger.error(f"Erro ao agrupar artigos: {str(e)}", exc_info=True)
            return []


    def _extract_cluster_keywords(self, articles: List[NewsArticle]) -> List[str]:
        """
        Extrai palavras-chave de um cluster de artigos.

        Args:
            articles: Lista de artigos no cluster

        Returns:
            Lista de palavras-chave do cluster
        """
        if not articles:
            return []

        # Combina os textos dos artigos
        combined_text = " ".join(
            f"{a.title} {a.summary or a.content[:500]}" 
            for a in articles if a.content
        )

        if not combined_text:
            return []

        # Processa o texto combinado
        doc = self.nlp(combined_text)

        # Extrai palavras-chave
        keywords = self._extract_keywords(doc, top_n=10)

        return keywords


    def _extract_common_entities(self, articles: List[NewsArticle]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extrai as entidades nomeadas mais comuns dos artigos.

        Args:
            articles: Lista de artigos processados

        Returns:
            Dicionário com as entidades agrupadas por tipo
        """
        if not articles:
            return {}

        entity_counter = {}

        for article in articles:
            if not hasattr(article, 'entities') or not article.entities:
                continue

            for ent in article.entities:
                ent_type = ent.get('label', 'OTHER')
                ent_text = ent.get('text', '').strip()

                if not ent_text or len(ent_text) < 2:
                    continue

                if ent_type not in entity_counter:
                    entity_counter[ent_type] = Counter()

                entity_counter[ent_type][ent_text] += 1

        # Ordena as entidades por frequência
        result = {}
        for ent_type, counter in entity_counter.items():
            result[ent_type] = [
                {'text': text, 'count': count}
                for text, count in counter.most_common(10)  # Top 10 por tipo
            ]

        return result


    def _aggregate_sentiment(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Calcula estatísticas de sentimento agregadas.

        Args:
            articles: Lista de artigos processados

        Returns:
            Dicionário com estatísticas de sentimento
        """
        if not articles:
            return {
                'average': 0.0,
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 100.0,
                'count': 0
            }

        sentiments = []
        positive = 0
        negative = 0
        neutral = 0

        for article in articles:
            if hasattr(article, 'sentiment_score') and article.sentiment_score is not None:
                score = article.sentiment_score
                sentiments.append(score)

                if score > 0.1:
                    positive += 1
                elif score < -0.1:
                    negative += 1
                else:
                    neutral += 1

        total = len(sentiments) or 1  # Evita divisão por zero

        return {
            'average': sum(sentiments) / total if sentiments else 0.0,
            'positive': (positive / total) * 100,
            'negative': (negative / total) * 100,
            'neutral': (neutral / total) * 100,
            'count': total
        }


    def _generate_market_metrics(
        self, 
        articles: List[NewsArticle],
        topics: List[Dict[str, Any]],
        sentiment: Dict[str, Any]
    ) -> Dict[str, MarketMetric]:
        """
        Gera métricas de mercado a partir das notícias processadas.

        Args:
            articles: Lista de artigos processados
            topics: Tópicos extraídos
            sentiment: Análise de sentimento agregada

        Returns:
            Dicionário de métricas de mercado
        """
        metrics = {}

        # 1. Métrica de Volume de Notícias
        metrics['news_volume'] = MarketMetric(
            name="Volume de Notícias",
            description="Número total de notícias coletadas",
            unit="unidade",
            current_value=DataPoint(
                value=len(articles),
                source=DataSource.NEWS_SCRAPER,
                timestamp=datetime.utcnow(),
                confidence=1.0,
                quality=DataQualityLevel.HIGH,
                meta_info={
                    'time_period': 'total',
                    'source_types': list({a.source.type for a in articles if hasattr(a, 'source')})
                }
            )
        )

        # 2. Métrica de Sentimento Médio
        metrics['average_sentiment'] = MarketMetric(
            name="Sentimento Médio das Notícias",
            description="Média do sentimento das notícias (-1 a 1)",
            unit="pontuação",
            current_value=DataPoint(
                value=sentiment.get('average', 0.0),
                source=DataSource.NEWS_SCRAPER,
                timestamp=datetime.utcnow(),
                confidence=0.8 if len(articles) >= 5 else 0.5,
                quality=DataQualityLevel.MEDIUM,
                meta_info={
                    'sample_size': len(articles),
                    'positive_percent': sentiment.get('positive', 0.0),
                    'negative_percent': sentiment.get('negative', 0.0),
                    'neutral_percent': sentiment.get('neutral', 0.0)
                }
            )
        )

        # 3. Tópicos Principais
        if topics:
            main_topics = sorted(topics, key=lambda x: x.get('weight', 0), reverse=True)[:3]

            metrics['main_topics'] = MarketMetric(
                name="Tópicos Principais nas Notícias",
                description="Principais tópicos discutidos nas notícias",
                unit="lista",
                current_value=DataPoint(
                    value=[t['keywords'] for t in main_topics],
                    source=DataSource.NEWS_SCRAPER,
                    timestamp=datetime.utcnow(),
                    confidence=0.9 if len(articles) >= 10 else 0.6,
                    quality=DataQualityLevel.HIGH,
                    meta_info={
                        'topic_count': len(topics),
                        'topic_weights': [t.get('weight', 0) for t in main_topics]
                    }
                )
            )

        # 4. Fontes Mais Citadas
        if hasattr(articles[0], 'source'):
            sources = [a.source.name for a in articles if hasattr(a, 'source')]
            source_counts = Counter(sources)
            top_sources = source_counts.most_common(5)

            metrics['top_sources'] = MarketMetric(
                name="Fontes Mais Citadas",
                description="Fontes de notícias mais frequentes",
                unit="lista",
                current_value=DataPoint(
                    value=[{"source": src, "count": cnt} for src, cnt in top_sources],
                    source=DataSource.NEWS_SCRAPER,
                    timestamp=datetime.utcnow(),
                    confidence=1.0,
                    quality=DataQualityLevel.HIGH,
                    meta_info={
                        'total_sources': len(source_counts),
                        'articles_analyzed': len(articles)
                    }
                )
            )

        return metrics
