"""Tests for the ETL pipeline service."""
import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from sqlalchemy.orm import Session

from shared.schemas.analysis import AnalysisCreate
from shared.db.models.analysis import Analysis as AnalysisModel
from etl_pipeline.app.services.etl_pipeline import ETLPipeline

# Test data
TEST_ANALYSIS_INPUT = AnalysisCreate(
    niche="Tecnologia",
    description="Análise do mercado de tecnologia no Brasil"
)

# Mock data
MOCK_NLP_FEATURES = {
    'keywords': [
        {'keyword': 'tecnologia', 'score': 0.9},
        {'keyword': 'inovação', 'score': 0.8}
    ],
    'topics': [
        {'topic': 'tecnologia', 'weight': 0.9},
        {'topic': 'inovação', 'weight': 0.8}
    ]
}

MOCK_IBGE_DATA = {
    'table_code': '6401',
    'data': [{'variable': 'PNAD', 'value': 1000}]
}

MOCK_GOOGLE_TRENDS = {
    'interest': {
        'data': [{'date': '2023-01-01', 'value': 75}],
        'metadata': {'status': 'success'}
    },
    'related': {'tecnologia': {'top': [], 'rising': []}}
}


class TestETLPipeline:
    """Test suite for the ETLPipeline class."""

    @pytest.fixture


    def mock_db_session(self):
        """Create a mock database session."""
        with patch('sqlalchemy.orm.Session') as mock_session:
            yield mock_session()

    @pytest.fixture


    def mock_etl_dependencies(self):
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

            mock_sidra.return_value.get_table.return_value = MOCK_IBGE_DATA

            mock_trends.return_value.get_interest_over_time.return_value = MOCK_GOOGLE_TRENDS['interest']
            mock_trends.return_value.get_related_queries.return_value = MOCK_GOOGLE_TRENDS['related']

            yield {
                'nlp': mock_nlp,
                'mapper': mock_mapper,
                'sidra': mock_sidra,
                'trends': mock_trends
            }


    def test_pipeline_execution(self, mock_db_session, mock_etl_dependencies):
        """Test the complete ETL pipeline execution."""
        # Setup
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None

        analysis = AnalysisModel(
            id=1,
            user_id=1,
            niche=TEST_ANALYSIS_INPUT.niche,
            description=TEST_ANALYSIS_INPUT.description,
            data={},
            status='completed'
        )
        mock_db_session.add.return_value = analysis

        # Execute
        pipeline = ETLPipeline(mock_db_session)
        result = pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        # Verify
        assert result['status'] == 'success'
        assert 'analysis_id' in result
        assert result['sources'] == ['nlp_features', 'ibge_data', 'google_trends']

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()


    def test_extract_data(self, mock_db_session, mock_etl_dependencies):
        """Test the data extraction phase."""
        pipeline = ETLPipeline(mock_db_session)
        pipeline._extract_data(TEST_ANALYSIS_INPUT)

        # Verify NLP features were extracted
        mock_etl_dependencies['nlp'].assert_called_once_with(
            niche=TEST_ANALYSIS_INPUT.niche,
            description=TEST_ANALYSIS_INPUT.description
        )

        # Verify IBGE data was extracted
        mock_etl_dependencies['sidra'].return_value.get_table.assert_called_once()

        # Verify Google Trends data was extracted
        mock_etl_dependencies['trends'].return_value.get_interest_over_time.assert_called_once()
        mock_etl_dependencies['trends'].return_value.get_related_queries.assert_called()


    def test_transform_data(self, mock_db_session, mock_etl_dependencies):
        """Test the data transformation phase."""
        pipeline = ETLPipeline(mock_db_session)
        pipeline.cache = {
            'nlp_features': MOCK_NLP_FEATURES,
            'ibge_data': MOCK_IBGE_DATA,
            'google_trends': MOCK_GOOGLE_TRENDS
        }

        result = pipeline._transform_data(TEST_ANALYSIS_INPUT)

        # Verify the structure of the transformed data
        assert 'metadata' in result
        assert 'nlp_features' in result
        assert 'ibge_data' in result
        assert 'google_trends' in result

        # Verify user input was preserved
        assert result['metadata']['user_input']['niche'] == TEST_ANALYSIS_INPUT.niche
        assert result['metadata']['user_input']['description'] == TEST_ANALYSIS_INPUT.description


    def test_load_data(self, mock_db_session):
        """Test the data loading phase."""
        # Setup
        test_data = {
            'metadata': {'test': 'data'},
            'nlp_features': MOCK_NLP_FEATURES,
            'ibge_data': MOCK_IBGE_DATA,
            'google_trends': MOCK_GOOGLE_TRENDS
        }

        # Mock database operations
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None

        # Create a mock analysis object that will be returned by refresh
        analysis = AnalysisModel(
            id=1,
            user_id=1,
            niche=TEST_ANALYSIS_INPUT.niche,
            description=TEST_ANALYSIS_INPUT.description,
            data=test_data,
            status='completed'
        )


        def refresh_side_effect(instance):
            instance.id = 1

        mock_db_session.refresh.side_effect = refresh_side_effect

        # Execute
        pipeline = ETLPipeline(mock_db_session)
        result = pipeline._load_data(1, TEST_ANALYSIS_INPUT, test_data)

        # Verify
        assert result is not None
        assert result.id == 1
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()


    def test_error_handling(self, mock_db_session, mock_etl_dependencies):
        """Test error handling in the pipeline."""
        # Make NLP extraction fail
        mock_etl_dependencies['nlp'].side_effect = Exception("NLP processing failed")

        pipeline = ETLPipeline(mock_db_session)

        with pytest.raises(Exception) as exc_info:
            pipeline.run_pipeline(1, TEST_ANALYSIS_INPUT)

        assert "NLP processing failed" in str(exc_info.value)
