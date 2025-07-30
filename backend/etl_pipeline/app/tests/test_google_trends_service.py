"""Tests for the Google Trends service."""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime

from etl_pipeline.app.services.google_trends_service import GoogleTrendsService

# Sample data for testing
SAMPLE_INTEREST_OVER_TIME = pd.DataFrame(
    data=[[75, 25], [80, 30], [85, 35]],
    columns=['term1', 'term2'],
    index=pd.date_range(start='2023-01-01', periods=3, freq='D')
)

SAMPLE_RELATED_QUERIES = {
    'term1': {
        'top': pd.DataFrame({
            'query': ['related1', 'related2'],
            'value': [90, 80]
        }),
        'rising': pd.DataFrame({
            'query': ['rising1', 'rising2'],
            'value': [1000, 800]
        })
    }
}

SAMPLE_INTEREST_BY_REGION = pd.DataFrame({
    'geoName': ['São Paulo', 'Rio de Janeiro', 'Minas Gerais'],
    'term1': [100, 80, 60],
    'term2': [50, 40, 30]
}).set_index('geoName')

SAMPLE_SUGGESTIONS = [
    {'title': 'suggestion1', 'type': 'Term'},
    {'title': 'suggestion2', 'type': 'Term'}
]

SAMPLE_TRENDING_SEARCHES = pd.DataFrame({
    0: ['trend1', 'trend2', 'trend3']
})

class TestGoogleTrendsService:
    """Test suite for the GoogleTrendsService class."""
    
    @pytest.fixture
    def mock_pytrends(self):
        """Create a mock pytrends object."""
        with patch('pytrends.request.TrendReq') as mock_trend_req:
            mock_instance = mock_trend_req.return_value
            
            # Set up mock return values
            mock_instance.interest_over_time.return_value = SAMPLE_INTEREST_OVER_TIME
            mock_instance.related_queries.return_value = SAMPLE_RELATED_QUERIES
            mock_instance.interest_by_region.return_value = SAMPLE_INTEREST_BY_REGION
            mock_instance.suggestions.return_value = SAMPLE_SUGGESTIONS
            mock_instance.trending_searches.return_value = SAMPLE_TRENDING_SEARCHES
            mock_instance.today_searches.return_value = SAMPLE_TRENDING_SEARCHES
            
            yield mock_instance
    
    def test_initialization(self, mock_pytrends):
        """Test that the service initializes correctly."""
        service = GoogleTrendsService()
        assert service is not None
        assert service.hl == 'pt-BR'
        assert service.tz == 180
    
    def test_interest_over_time(self, mock_pytrends):
        """Test getting interest over time data."""
        service = GoogleTrendsService()
        keywords = ['term1', 'term2']
        
        result = service.get_interest_over_time(keywords)
        
        # Check that the pytrends methods were called correctly
        mock_pytrends.build_payload.assert_called_once()
        mock_pytrends.interest_over_time.assert_called_once()
        
        # Check the result structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'success'
        assert result['metadata']['keywords'] == keywords
        assert len(result['data']) == 3  # 3 days of data
    
    def test_related_queries(self, mock_pytrends):
        """Test getting related queries."""
        service = GoogleTrendsService()
        keywords = ['term1']
        
        result = service.get_related_queries(keywords)
        
        # Check that the pytrends methods were called correctly
        mock_pytrends.build_payload.assert_called_once()
        mock_pytrends.related_queries.assert_called_once()
        
        # Check the result structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'success'
        assert 'term1' in result['data']
        assert 'top' in result['data']['term1']
        assert 'rising' in result['data']['term1']
    
    def test_interest_by_region(self, mock_pytrends):
        """Test getting interest by region."""
        service = GoogleTrendsService()
        keywords = ['term1', 'term2']
        
        result = service.get_interest_by_region(keywords)
        
        # Check that the pytrends method was called correctly
        mock_pytrends.interest_by_region.assert_called_once()
        
        # Check the result structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'success'
        assert len(result['data']) == 3  # 3 regions
    
    def test_get_suggestions(self, mock_pytrends):
        """Test getting search suggestions."""
        service = GoogleTrendsService()
        keyword = 'test'
        
        result = service.get_suggestions(keyword)
        
        # Check that the pytrends method was called correctly
        mock_pytrends.suggestions.assert_called_once_with(keyword)
        
        # Check the result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['title'] == 'suggestion1'
    
    def test_get_trending_searches(self, mock_pytrends):
        """Test getting trending searches."""
        service = GoogleTrendsService()
        geo = 'BR'
        
        result = service.get_trending_searches(geo)
        
        # Check that the pytrends method was called correctly
        mock_pytrends.trending_searches.assert_called_once()
        
        # Check the result structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'success'
        assert len(result['data']) == 3  # 3 trending searches
    
    def test_get_today_searches(self, mock_pytrends):
        """Test getting today's trending searches."""
        service = GoogleTrendsService()
        geo = 'BR'
        
        result = service.get_today_searches(geo)
        
        # Check that the pytrends method was called correctly
        mock_pytrends.today_searches.assert_called_once()
        
        # Check the result structure
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'success'
        assert len(result['data']) == 3  # 3 trending searches
    
    def test_error_handling(self, mock_pytrends):
        """Test error handling in the service."""
        # Make the mock raise an exception
        mock_pytrends.build_payload.side_effect = Exception("API Error")
        
        service = GoogleTrendsService()
        
        # Test with a method that uses build_payload
        result = service.get_interest_over_time(['term1'])
        
        # Check that the error was handled gracefully
        assert 'data' in result
        assert 'metadata' in result
        assert result['metadata']['status'] == 'error'
        assert 'API Error' in result['metadata']['message']
    
    def test_rate_limiting(self, mock_pytrends):
        """Test that rate limiting is applied between requests."""
        with patch('time.sleep') as mock_sleep:
            service = GoogleTrendsService()
            
            # Make multiple requests
            service.get_interest_over_time(['term1'])
            service.get_interest_over_time(['term2'])
            
            # Check that sleep was called between requests
            assert mock_sleep.call_count >= 2
    
    def test_empty_keywords(self, mock_pytrends):
        """Test behavior with empty keyword list."""
        service = GoogleTrendsService()
        
        result = service.get_interest_over_time([])
        
        assert result['metadata']['status'] == 'error'
        assert 'No keywords provided' in result['metadata']['message']
        
        # Verify no API calls were made
        mock_pytrends.build_payload.assert_not_called()
        mock_pytrends.interest_over_time.assert_not_called()
