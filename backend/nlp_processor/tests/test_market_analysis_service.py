
"""Tests for the Market Analysis Service."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisCreate
from app.services.market_analysis_service import MarketAnalysisService

# Test data
TEST_NICHE = "Moda sustentável"
TEST_DESCRIPTION = """
    Loja de roupas e acessórios feitos com materiais reciclados e orgânicos.
    Focamos em peças atemporais, produção ética e comércio justo.
    Nossos produtos são feitos por cooperativas locais de artesãs.
"""


class TestMarketAnalysisService:
    """Test suite for MarketAnalysisService."""

    @pytest.fixture


    def mock_db(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture


    def mock_sidra_client(self):
        """Create a mock SIDRA client."""
        mock = MagicMock()
        mock.get_table.return_value = {
            'data': [
                {'variable': '2979', 'value': 2500.00, 'period': '202301'},
                {'variable': '2980', 'value': 3000.00, 'period': '202301'}
            ],
            'table_code': '6401',
            'variables': ['2979', '2980']
        }
        return mock

    @pytest.fixture


    def service(self, mock_db, mock_sidra_client):
        """Create a MarketAnalysisService instance with mocked dependencies."""
        with patch('app.services.market_analysis_service.SidraClient', return_value=mock_sidra_client):
            return MarketAnalysisService(db=mock_db)


    def test_analyze_market_segment(self, service, mock_db, mock_sidra_client):
        """Test the complete market analysis pipeline."""
        # Prepare test input
        analysis_input = AnalysisCreate(
            niche=TEST_NICHE,
            description=TEST_DESCRIPTION
        )
        user_id = 1

        # Execute the analysis
        result = service.analyze_market_segment(user_id, analysis_input)

        # Verify the result structure
        assert 'metadata' in result
        assert 'input' in result
        assert 'nlp_analysis' in result
        assert 'market_data' in result
        assert 'insights' in result

        # Verify input was preserved
        assert result['input']['niche'] == TEST_NICHE
        assert 'sustentavel' in result['input']['description'].lower()

        # Verify NLP features were extracted
        assert 'keywords' in result['nlp_analysis']
        assert 'topics' in result['nlp_analysis']
        assert 'entities' in result['nlp_analysis']

        # Verify IBGE data was collected
        assert 'data' in result['market_data']
        assert len(result['market_data']['data']) > 0

        # Verify the result was saved to the database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()


    def test_map_to_ibge_parameters(self, service):
        """Test mapping of NLP features to IBGE parameters."""
        # Test with income-related keywords
        nlp_features = {
            'keywords': [
                {'keyword': 'renda', 'score': 0.9},
                {'keyword': 'faixa etária', 'score': 0.8}
            ]
        }

        params = service._map_to_ibge_parameters(nlp_features)

        assert params['tabela'] == '6401'  # Default table
        assert '2979' in params['variaveis']  # Income variable
        assert '200' in params['classificacoes']  # Age classification


    def test_collect_ibge_data(self, service, mock_sidra_client):
        """Test IBGE data collection."""
        test_params = {
            'tabela': '6401',
            'variaveis': ['2979'],
            'classificacoes': {},
            'localidades': ['BR'],
            'periodo': 'last'
        }

        result = service._collect_ibge_data(test_params)

        # Verify the SIDRA client was called with the correct parameters
        mock_sidra_client.get_table.assert_called_once_with(
            table_code='6401',
            variables=['2979'],
            classifications={},
            locations=['BR'],
            period='last'
        )

        # Verify the result structure
        assert 'data' in result
        assert len(result['data']) == 2
        assert 'table_code' in result
        assert 'variables' in result


    def test_generate_insights(self, service):
        """Test insight generation."""
        nlp_features = {
            'keywords': [
                {'keyword': 'renda', 'score': 0.9},
                {'keyword': 'sustentável', 'score': 0.8}
            ],
            'topics': [
                {
                    'topic_id': 0,
                    'keywords': ['moda', 'sustentável', 'ecológico'],
                    'scores': [0.5, 0.4, 0.3],
                    'similarity_to_main_text': 0.9
                }
            ]
        }

        ibge_data = {
            'data': [
                {'variable': '2979', 'value': 2500.00, 'period': '202301'},
                {'variable': '2980', 'value': 3000.00, 'period': '202301'}
            ],
            'table_code': '6401',
            'variables': ['2979', '2980']
        }

        insights = service._generate_insights(nlp_features, ibge_data)

        # Verify the result is a list
        assert isinstance(insights, list)

        # Add more specific assertions based on your insight generation logic
        # For now, just check that the function runs without errors
        assert True
