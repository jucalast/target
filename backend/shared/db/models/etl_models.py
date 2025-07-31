"""
Modelos SQLAlchemy para armazenamento de resultados do ETL.

Este módulo define os modelos de banco de dados para armazenar os resultados
do pipeline ETL no PostgreSQL.
"""
from datetime import datetime

from enum import Enum

from sqlalchemy import Column, String, JSON, DateTime, Float, Integer, \

    ForeignKey, Table, Text

from sqlalchemy.orm import relationship, declarative_base

from shared.db.postgres import Base

etl_result_news = Table(
    'etl_result_news',
    Base.metadata,
    Column('etl_result_id', PG_UUID(as_uuid=
        True), ForeignKey('etl_results.id'), \
        primary_key=True),
        Column('news_article_id', PG_UUID(as_uuid=True), \
        ForeignKey('news_articles.id'), primary_key=True)
)

class DataSource(str, Enum):
"""Fontes de dados suportadas pelo pipeline ETL."""
    IBGE_SIDRA = "ibge_sidra"
    GOOGLE_TRENDS = "google_trends"
    NEWS_SCRAPING = "news_scraping"
    NLP_PROCESSING = "nlp_processing"

class DataQualityLevel(str, Enum):
"""Níveis de qualidade dos dados."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

class DataPointModel(Base):
"""Modelo para armazenar pontos de dados genéricos."""
    __tablename__ = "data_points"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    value = Column(JSON, nullable=False)
    source = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(Float, default=1.0)
    quality = Column(String(20), default=DataQualityLevel.UNKNOWN)
    meta_info = Column('metadata', JSONB, \
        default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    metric_id = Column(PG_UUID(as_uuid=True), ForeignKey('market_metrics.id'))

    def __repr__(self):
    return f"<DataPoint(id={self.id}, value={self.value}, \
            source={self.source})>"

class MarketMetricModel(Base):
"""Modelo para métricas de mercado."""
    __tablename__ = "market_metrics"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    unit = Column(String(50), default="")
    trend = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    segment_id =
        Column(PG_UUID(as_uuid=True), ForeignKey('market_segments.id'), \
        nullable=False)
    current_value_id = Column(PG_UUID(as_uuid=True), \
        ForeignKey('data_points.id'), nullable=True)

    current_value = relationship("DataPointModel", \
        foreign_keys=[current_value_id], uselist=False)
    historical_values = relationship("DataPointModel", backref="metric")

    def __repr__(self):
    return f"<MarketMetric(id={self.id}, name={self.name}, \
            segment_id={self.segment_id})>"

class MarketSegmentModel(Base):
"""Modelo para segmentos de mercado."""
    __tablename__ = "market_segments"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    etl_result_id =
        Column(PG_UUID(as_uuid=True), ForeignKey('etl_results.id'), \
        nullable=False)
    metrics =
        relationship("MarketMetricModel", backref="segment", cascade="all, \
        delete-orphan")

    def __repr__(self):
    return f"<MarketSegment(id={self.id}, name={self.name}, \
            etl_result_id={self.etl_result_id})>"

class NewsArticleModel(Base):
"""Modelo para artigos de notícias."""
    __tablename__ = "news_articles"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(512), nullable=False)
    source = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    summary = Column(Text, default="")
    sentiment = Column(Float, nullable=True)
    keywords = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    etl_results = relationship("ETLResultModel", secondary=etl_result_news, \
        back_populates="news_articles")

    def __repr__(self):
    return f"<NewsArticle(id={self.id}, title={self.title[:50]}...)>"

class SearchTrendModel(Base):
"""Modelo para tendências de busca."""
    __tablename__ = "search_trends"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    keyword = Column(String(255), nullable=False)
    values = Column(JSONB, \
        nullable=False)
    related_queries = Column(JSONB, default=[])
    interest_by_region = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    etl_result_id =
        Column(PG_UUID(as_uuid=True), ForeignKey('etl_results.id'), \
        nullable=False)

    def __repr__(self):
    return f"<SearchTrend(id={self.id}, keyword={self.keyword}, \
            etl_result_id={self.etl_result_id})>"

class ETLResultModel(Base):
"""Modelo para resultados de execuções do ETL."""
    __tablename__ = "etl_results"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(String(100), nullable=False, unique=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processing_time = Column(Float, nullable=False)
    user_input = Column(JSONB, default={})
    nlp_features = Column(JSONB, default={})
    raw_data = Column(JSONB, default={})
    stats = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, \
        onupdate=datetime.utcnow)

    market_segments =
        relationship("MarketSegmentModel", backref="etl_result", \
        cascade="all, delete-orphan")
    search_trends = relationship("SearchTrendModel", backref="etl_result", \
        cascade="all, delete-orphan")
    news_articles =
        relationship("NewsArticleModel", secondary=etl_result_news, \
        back_populates="etl_results")

    def __repr__(self):
    return f"<ETLResult(id={self.id}, request_id={self.request_id}, \
            timestamp={self.timestamp})>"

class ETLRunLogModel(Base):
"""Modelo para logs de execução do ETL."""
    __tablename__ = "etl_run_logs"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)
        'failed'
    message = Column(Text, nullable=True)
    details = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
    return f"<ETLRunLog(id={self.id}, request_id={self.request_id}, \
            status={self.status})>"
