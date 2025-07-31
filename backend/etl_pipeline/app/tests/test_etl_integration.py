"""Integration tests for the ETL pipeline."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from sqlalchemy.orm import Session

from shared.schemas.analysis import AnalysisCreate
from etl_pipeline.app.services.etl_pipeline import ETLPipeline

# Test data
TEST_ANALYSIS_INPUT = AnalysisCreate(
    niche="Tecnologia",
    description="Análise do mercado de tecnologia no Brasil"
)

# Mock data
MOCK_NLP_FEATURES = {
    'keywords': [
        {'keyword': 'tecnologia', 'score': 0.95, 'source': 'tfidf'},
        {'keyword': 'inovação', 'score': 0.87, 'source': 'tfidf'}
    ],
    'topics': [
        {
            'topic': 'Tecnologia e Inovação',
            'weight': 0.92,
            'keywords': [
                {'keyword': 'tecnologia', 'score': 0.98},
                {'keyword': 'inovação', 'score': 0.95}
            ]
        }
    ],
    'entities': [
        {'text': 'Brasil', 'type': 'LOC', 'start': 30, 'end': 36}
    ],
    'embeddings': {
        'spacy': {
            'model': 'pt_core_news_lg',
            'vector': [0.1, 0.2, 0.3],
            'normalized': True
        }
    }
}

MOCK_IBGE_DATA = {
    '6401': {
        'metadata': {'name': 'PNAD Contínua'},
        'period': '2023-01/2023-12',
        'data': [{'variable': 'Rendimento', 'value': 2500.0}],
        'variables': [{'code': 'V1', 'name': 'Rendimento médio'}],
        'classifications': {}
    }
}

MOCK_GOOGLE_TRENDS = {
    'interest_over_time': {
        'data': [
            {'date': '2023-01-01', 'value': 75, 'keyword': 'tecnologia'}
        ],
        'metadata': {'status': 'success'}
    },
    'related_queries': {
        'tecnologia': {
            'data': {
                'top': [
                    {'query': 'tecnologia 2023', 'value': 100}
                ]
            }
        }
    }
}


class TestETLIntegration:
    """Integration tests for the ETL pipeline."""

    @pytest.fixture


    def mock_dependencies(self):
        """Mock all external dependencies of the ETL pipeline."""
        with patch('app.services.nlp_service.extract_features') as mock_nlp, \
             patch('app.services.sidra_mapper.SIDRAMapper') as mock_mapper, \
             patch('app.services.sidra_client.SidraClient') as mock_sidra, \
             patch('app.services.google_trends_service.GoogleTrendsService') as mock_trends:

            # Configure mocks
            mock_nlp.return_value = MOCK_NLP_FEATURES

            mock_mapper.return_value.map_terms_to_sidra_parameters.return_value = {
                'tabela': '6401',
                'variaveis': ['V1'],
                'classificacoes': {'C1': ['V1']}
            }

            mock_sidra.return_value.get_table.return_value = MOCK_IBGE_DATA['6401']

            mock_trends.return_value.get_interest_over_time.return_value = MOCK_GOOGLE_TRENDS['interest_over_time']
            mock_trends.return_value.get_related_queries.return_value = MOCK_GOOGLE_TRENDS['related_queries']['tecnologia']

            yield {
                'nlp': mock_nlp,
                'mapper': mock_mapper,
                'sidra': mock_sidra,
                'trends': mock_trends
            }


    def test_complete_etl_flow(self, mock_dependencies):
        """Test the complete ETL flow with all components."""
        # Setup
        mock_db = MagicMock(spec=Session)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        # Create a mock analysis object that will be returned by refresh
        analysis = MagicMock()
        analysis.id = 1
        mock_db.refresh = lambda x: setattr(x, 'id', 1)

        # Execute
        pipeline = ETLPipeline(mock_db)
        result = pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        # Verify
        assert result['status'] == 'success'
        assert 'analysis_id' in result

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify NLP service was called
        mock_dependencies['nlp'].assert_called_once_with(
            niche=TEST_ANALYSIS_INPUT.niche,
            description=TEST_ANALYSIS_INPUT.description
        )

        # Verify SIDRA mapper was called with keywords
        mock_dependencies['mapper'].return_value.map_terms_to_sidra_parameters.assert_called_once()

        # Verify SIDRA client was called
        mock_dependencies['sidra'].return_value.get_table.assert_called_once()

        # Verify Google Trends was called
        mock_dependencies['trends'].return_value.get_interest_over_time.assert_called_once()
        mock_dependencies['trends'].return_value.get_related_queries.assert_called_once()


    def test_etl_with_missing_optional_data(self, mock_dependencies):
        """Test ETL pipeline when optional data sources are missing."""
        # Setup - make Google Trends return no data
        mock_dependencies['trends'].return_value.get_interest_over_time.return_value = {'data': []}
        mock_dependencies['trends'].return_value.get_related_queries.return_value = {}

        mock_db = MagicMock(spec=Session)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh = lambda x: setattr(x, 'id', 1)

        # Execute
        pipeline = ETLPipeline(mock_db)
        result = pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        # Verify
        assert result['status'] == 'success'
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


    def test_etl_error_handling(self, mock_dependencies):
        """Test error handling in the ETL pipeline."""
        # Make NLP extraction fail
        mock_dependencies['nlp'].side_effect = Exception("NLP processing failed")

        mock_db = MagicMock(spec=Session)

        # Execute and verify exception is raised
        pipeline = ETLPipeline(mock_db)

        with pytest.raises(Exception) as exc_info:
            pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        assert "NLP processing failed" in str(exc_info.value)

        # Verify no database operations were performed
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()


    def test_etl_with_ibge_error(self, mock_dependencies):
        """Test ETL pipeline when IBGE data fetch fails."""
        # Make SIDRA client raise an exception
        mock_dependencies['sidra'].return_value.get_table.side_effect = Exception("IBGE API error")

        mock_db = MagicMock(spec=Session)
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh = lambda x: setattr(x, 'id', 1)

        # Execute
        pipeline = ETLPipeline(mock_db)
        result = pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        # Verify
        assert result['status'] == 'success'  # Should still succeed with partial data
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify Google Trends was still called
        mock_dependencies['trends'].return_value.get_interest_over_time.assert_called_once()
