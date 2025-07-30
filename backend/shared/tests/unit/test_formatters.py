"""Tests for the data formatters."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from shared.schemas.output_schema import MarketAnalysisOutput
from shared.utils.formatters import (
    format_market_analysis,
    _format_nlp_analysis,
    _format_ibge_data,
    _format_google_trends
)

# Test data
TEST_ANALYSIS_ID = str(uuid4())
TEST_INPUT = {
    "niche": "Tecnologia",
    "description": "Análise do mercado de tecnologia no Brasil"
}

TEST_NLP_FEATURES = {
    "keywords": [
        {"keyword": "tecnologia", "score": 0.95, "source": "tfidf"},
        {"keyword": "inovação", "score": 0.87, "source": "tfidf"}
    ],
    "topics": [
        {
            "topic": "Tecnologia e Inovação",
            "weight": 0.92,
            "keywords": [
                {"keyword": "tecnologia", "score": 0.98},
                {"keyword": "inovação", "score": 0.95}
            ]
        }
    ],
    "entities": [
        {"text": "Brasil", "type": "LOC", "start": 30, "end": 36}
    ],
    "embeddings": {
        "spacy": {
            "model": "pt_core_news_lg",
            "vector": [0.1, 0.2, 0.3],
            "normalized": True
        }
    }
}

TEST_IBGE_DATA = {
    "6401": {
        "metadata": {"name": "PNAD Contínua - Rendimento"},
        "period": "2023-01/2023-12",
        "data": [{"variable": "Rendimento médio", "value": 2500.0}],
        "variables": [{"code": "V1", "name": "Rendimento médio"}]
    }
}

TEST_GOOGLE_TRENDS = {
    "interest_over_time": {
        "data": [
            {"date": "2023-01-01", "value": 75, "keyword": "tecnologia"}
        ]
    },
    "related_queries": {
        "tecnologia": {
            "data": {
                "top": [
                    {"query": "tecnologia 2023", "value": 100}
                ]
            }
        }
    }
}

class TestFormatters:
    """Test suite for the formatter utilities."""
    
    def test_format_nlp_analysis(self):
        """Test formatting of NLP features."""
        result = _format_nlp_analysis(TEST_NLP_FEATURES)
        
        # Check keywords
        assert len(result.keywords) == 2
        assert result.keywords[0].keyword == "tecnologia"
        assert result.keywords[0].score == 0.95
        
        # Check topics
        assert len(result.topics) == 1
        assert result.topics[0].label == "Tecnologia e Inovação"
        assert len(result.topics[0].keywords) == 2
        
        # Check entities
        assert len(result.entities) == 1
        assert result.entities[0].text == "Brasil"
        
        # Check embeddings
        assert "spacy" in result.embeddings
        assert len(result.embeddings["spacy"].vector) == 3
    
    def test_format_ibge_data(self):
        """Test formatting of IBGE data."""
        table_code = "6401"
        result = _format_ibge_data(table_code, TEST_IBGE_DATA[table_code])
        
        assert result.table_code == table_code
        assert result.table_name == "PNAD Contínua - Rendimento"
        assert len(result.data) == 1
        assert len(result.variables) == 1
    
    def test_format_google_trends(self):
        """Test formatting of Google Trends data."""
        result = _format_google_trends(TEST_GOOGLE_TRENDS)
        
        assert len(result.interest_over_time) == 1
        assert "tecnologia" in result.related_queries
        assert len(result.related_queries["tecnologia"].get("top", [])) == 1
    
    def test_format_market_analysis_complete(self):
        """Test complete market analysis formatting."""
        result = format_market_analysis(
            analysis_id=TEST_ANALYSIS_ID,
            input_data=TEST_INPUT,
            nlp_features=TEST_NLP_FEATURES,
            ibge_data=TEST_IBGE_DATA,
            google_trends_data=TEST_GOOGLE_TRENDS,
            insights={"test_insight": 123},
            processing_time=1.23,
            status="completed"
        )
        
        # Check basic fields
        assert isinstance(result, MarketAnalysisOutput)
        assert result.analysis_id == TEST_ANALYSIS_ID
        assert result.status == "completed"
        assert result.processing_time == 1.23
        
        # Check input data
        assert result.input["niche"] == "Tecnologia"
        
        # Check NLP features
        assert len(result.nlp.keywords) == 2
        assert len(result.nlp.topics) == 1
        
        # Check IBGE data
        assert "6401" in result.ibge
        assert result.ibge["6401"].table_name == "PNAD Contínua - Rendimento"
        
        # Check Google Trends
        assert result.google_trends is not None
        assert len(result.google_trends.interest_over_time) == 1
        
        # Check insights
        assert result.insights == {"test_insight": 123}
    
    def test_format_market_analysis_minimal(self):
        """Test market analysis formatting with minimal data."""
        result = format_market_analysis(
            analysis_id=TEST_ANALYSIS_ID,
            input_data={"test": "input"},
            nlp_features={},
            ibge_data={},
            google_trends_data=None,
            insights=None,
            processing_time=None,
            status="processing"
        )
        
        assert result.status == "processing"
        assert result.input == {"test": "input"}
        assert len(result.nlp.keywords) == 0
        assert len(result.ibge) == 0
        assert result.google_trends is None
        assert result.insights == {}
    
    def test_timestamp_is_utc(self):
        """Test that timestamps are in UTC."""
        result = format_market_analysis(
            analysis_id=TEST_ANALYSIS_ID,
            input_data={"test": "input"},
            nlp_features={},
            ibge_data={}
        )
        
        # Check that the timestamp is timezone-aware and in UTC
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.tzinfo.utcoffset(result.timestamp) == timezone.utc.utcoffset(None)
