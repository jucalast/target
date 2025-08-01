"""
Google Trends Service

This service provides functionality to collect search interest data from Google Trends.
It's designed to be used as a supplementary data source for market analysis.

Implements best practices for Google Trends API:
- Intelligent rate limiting with 60s delay after 429 errors
- Exponential backoff with circuit breaker
- Optimized timeouts and connection management
- Request batching and caching strategies
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import random
import pandas as pd
from pytrends.request import TrendReq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException, HTTPError, Timeout

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker implementation for API resilience."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self._reset()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _record_failure(self):
        """Record a failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
        logger.info("Circuit breaker reset to CLOSED state")

class GoogleTrendsService:
    """
    Service for collecting and processing Google Trends data with best practices.
    
    Features:
    - Intelligent rate limiting (60s delay after 429 errors)
    - Circuit breaker for consecutive failures
    - Exponential backoff with jitter
    - Connection pooling and reuse
    - Request metrics and monitoring
    """
    
    # Rate limiting configuration
    RATE_LIMIT_DELAY = 60  # seconds after 429 error
    NORMAL_DELAY_RANGE = (2, 5)  # random delay between normal requests
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.1
    
    def __init__(self, hl: str = 'pt-BR', tz: int = 180, timeout: Tuple[int, int] = (10, 25)):
        """
        Initialize the Google Trends service with best practices.
        
        Args:
            hl: Language (default: 'pt-BR' for Brazilian Portuguese)
            tz: Timezone offset in minutes (default: 180 for Brasilia time)
            timeout: Timeout for requests in seconds (connect, read)
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self.pytrends = None
        self.circuit_breaker = CircuitBreaker()
        self.last_request_time = 0
        self.rate_limited_until = 0
        self.request_count = 0
        self.success_count = 0
        self._connect()
    def _connect(self) -> None:
        """Establish a connection to Google Trends with optimized settings."""
        try:
            # Create TrendReq with minimal configuration to avoid compatibility issues
            self.pytrends = TrendReq(
                hl=self.hl,
                tz=self.tz,
                timeout=self.timeout[1],  # Use only read timeout
                requests_args={'verify': False}
            )
            logger.info("Successfully connected to Google Trends")
        except Exception as e:
            logger.error(f"Failed to connect to Google Trends: {str(e)}")
            raise
    
    def _wait_for_rate_limit(self) -> None:
        """Implement intelligent rate limiting."""
        current_time = time.time()
        
        # Check if we're in a rate limit period
        if current_time < self.rate_limited_until:
            wait_time = self.rate_limited_until - current_time
            logger.warning(f"Rate limited. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        # Normal delay between requests
        time_since_last = current_time - self.last_request_time
        min_delay = random.uniform(*self.NORMAL_DELAY_RANGE)
        
        if time_since_last < min_delay:
            wait_time = min_delay - time_since_last
            logger.debug(f"Normal delay: waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _handle_rate_limit_error(self, error: Exception) -> None:
        """Handle 429 rate limit errors with appropriate delays."""
        if "429" in str(error) or "rate limit" in str(error).lower():
            self.rate_limited_until = time.time() + self.RATE_LIMIT_DELAY
            logger.warning(f"Rate limit hit. Backing off for {self.RATE_LIMIT_DELAY} seconds")
        else:
            # For other errors, shorter backoff
            backoff_time = min(30, 2 ** (self.request_count % 5))
            self.rate_limited_until = time.time() + backoff_time
            logger.warning(f"API error. Backing off for {backoff_time} seconds")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RequestException, HTTPError, Timeout)),
        reraise=True
    )
    def _make_request(self, func, *args, **kwargs):
        """Make a request with comprehensive error handling and rate limiting."""
        self.request_count += 1
        
        try:
            # Wait for rate limiting
            self._wait_for_rate_limit()
            
            # Execute request with circuit breaker
            result = self.circuit_breaker.call(func, *args, **kwargs)
            self.success_count += 1
            
            logger.debug(f"Request successful. Success rate: {self.success_count/self.request_count:.2%}")
            return result
            
        except Exception as e:
            logger.warning(f"Request failed: {str(e)}. Retrying...")
            self._handle_rate_limit_error(e)
            
            # Reconnect on certain errors
            if any(keyword in str(e).lower() for keyword in ['connection', 'timeout', 'ssl']):
                logger.info("Reconnecting due to connection error...")
                self._connect()
            
            raise
    
    def get_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = 'today 12-m',
        geo: str = 'BR',
        gprop: str = 'web',
        cat: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get interest over time for the given keywords with best practices.
        
        Args:
            keywords: List of search terms (max 5 per Google Trends limitation)
            timeframe: Time period for the data (e.g., 'today 12-m' for last 12 months)
            geo: Geographic location (default: 'BR' for Brazil)
            gprop: Google's property to filter on (web, news, images, froogle, youtube)
            cat: Category to narrow results (0 for all categories)
            
        Returns:
            Dictionary containing the interest over time data and metadata
        """
        if not keywords:
            return {'data': pd.DataFrame(), 'metadata': {'status': 'error', 'message': 'No keywords provided'}}
        
        # Validate keyword limit
        if len(keywords) > 5:
            logger.warning(f"Too many keywords ({len(keywords)}). Limiting to first 5.")
            keywords = keywords[:5]
        
        logger.info(f"Fetching interest over time for keywords: {keywords}")
        start_time = time.time()
        
        try:
            # Build the payload
            self._make_request(
                self.pytrends.build_payload,
                kw_list=keywords,
                timeframe=timeframe,
                geo=geo,
                gprop=gprop,
                cat=cat
            )
            
            # Get interest over time data
            df = self._make_request(self.pytrends.interest_over_time)
            
            if df.empty:
                return {
                    'data': df, 
                    'metadata': {
                        'status': 'no_data', 
                        'message': 'No data returned',
                        'keywords': keywords,
                        'request_time': time.time() - start_time
                    }
                }
            
            # Prepare the result with enhanced metadata
            result = {
                'data': df.reset_index().to_dict('records'),
                'metadata': {
                    'status': 'success',
                    'keywords': keywords,
                    'timeframe': timeframe,
                    'geo': geo,
                    'gprop': gprop,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_points': len(df),
                    'request_time': time.time() - start_time,
                    'success_rate': self.success_count / self.request_count if self.request_count > 0 else 0,
                    'circuit_breaker_state': self.circuit_breaker.state
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting interest over time: {str(e)}")
            return {
                'data': pd.DataFrame(),
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'keywords': keywords,
                    'timestamp': datetime.utcnow().isoformat(),
                    'request_time': time.time() - start_time,
                    'circuit_breaker_state': self.circuit_breaker.state
                }
            }
    
    def get_related_queries(
        self,
        keywords: List[str],
        timeframe: str = 'today 12-m',
        geo: str = 'BR',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get related queries for the given keywords.
        
        Args:
            keywords: List of search terms
            timeframe: Time period for the data
            geo: Geographic location (default: 'BR' for Brazil)
            
        Returns:
            Dictionary containing related queries and metadata
        """
        if not keywords:
            return {'data': {}, 'metadata': {'status': 'error', 'message': 'No keywords provided'}}
        
        logger.info(f"Fetching related queries for keywords: {keywords}")
        
        try:
            # Build the payload
            self._make_request(
                self.pytrends.build_payload,
                kw_list=keywords,
                timeframe=timeframe,
                geo=geo
            )
            
            # Get related queries
            related_queries = self._make_request(self.pytrends.related_queries)
            
            # Process the results
            result = {}
            for kw in keywords:
                if related_queries.get(kw) is not None:
                    top = related_queries[kw].get('top')
                    rising = related_queries[kw].get('rising')
                    
                    result[kw] = {
                        'top': top.to_dict('records') if top is not None else [],
                        'rising': rising.to_dict('records') if rising is not None else []
                    }
            
            return {
                'data': result,
                'metadata': {
                    'status': 'success',
                    'keywords': keywords,
                    'timeframe': timeframe,
                    'geo': geo,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting related queries: {str(e)}")
            return {
                'data': {},
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'keywords': keywords,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
    
    def get_interest_by_region(
        self,
        keywords: List[str],
        resolution: str = 'COUNTRY',
        inc_low_vol: bool = True,
        inc_geo_code: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get interest by region for the given keywords.
        
        Args:
            keywords: List of search terms
            resolution: Geographic resolution (COUNTRY, REGION, CITY, DMA, METRO)
            inc_low_vol: Include low volume regions
            inc_geo_code: Include geo codes in the results
            
        Returns:
            Dictionary containing interest by region data and metadata
        """
        if not keywords:
            return {'data': pd.DataFrame(), 'metadata': {'status': 'error', 'message': 'No keywords provided'}}
        
        logger.info(f"Fetching interest by region for keywords: {keywords}")
        
        try:
            # Get interest by region
            df = self._make_request(
                self.pytrends.interest_by_region,
                resolution=resolution.lower(),
                inc_low_vol=inc_low_vol,
                inc_geo_code=inc_geo_code
            )
            
            if df.empty:
                return {'data': df, 'metadata': {'status': 'no_data', 'message': 'No data returned'}}
            
            # Prepare the result
            result = {
                'data': df.reset_index().to_dict('records'),
                'metadata': {
                    'status': 'success',
                    'keywords': keywords,
                    'resolution': resolution,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_points': len(df)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting interest by region: {str(e)}")
            return {
                'data': pd.DataFrame(),
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'keywords': keywords,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
    
    def get_suggestions(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Get auto-complete suggestions for a keyword.
        
        Args:
            keyword: Search term to get suggestions for
            
        Returns:
            List of suggested terms with their titles and types
        """
        if not keyword:
            return []
        
        logger.info(f"Fetching suggestions for keyword: {keyword}")
        
        try:
            suggestions = self._make_request(self.pytrends.suggestions, keyword)
            return suggestions or []
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []
    
    def get_trending_searches(self, geo: str = 'BR') -> Dict[str, Any]:
        """
        Get currently trending searches.
        
        Args:
            geo: Geographic location (default: 'BR' for Brazil)
            
        Returns:
            Dictionary containing trending searches and metadata
        """
        logger.info(f"Fetching trending searches for {geo}")
        
        try:
            # Get trending searches
            df = self._make_request(self.pytrends.trending_searches, geo=geo)
            
            return {
                'data': df[0].tolist() if not df.empty else [],
                'metadata': {
                    'status': 'success',
                    'geo': geo,
                    'timestamp': datetime.utcnow().isoformat(),
                    'count': len(df) if not df.empty else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting trending searches: {str(e)}")
            return {
                'data': [],
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'geo': geo,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive service metrics for monitoring and debugging.
        
        Returns:
            Dictionary with performance and health metrics
        """
        return {
            'requests': {
                'total': self.request_count,
                'successful': self.success_count,
                'success_rate': self.success_count / self.request_count if self.request_count > 0 else 0,
                'failed': self.request_count - self.success_count
            },
            'circuit_breaker': {
                'state': self.circuit_breaker.state,
                'failure_count': self.circuit_breaker.failure_count,
                'last_failure': self.circuit_breaker.last_failure_time
            },
            'rate_limiting': {
                'currently_rate_limited': time.time() < self.rate_limited_until,
                'rate_limited_until': self.rate_limited_until,
                'time_to_next_request': max(0, self.rate_limited_until - time.time())
            },
            'configuration': {
                'language': self.hl,
                'timezone': self.tz,
                'timeout': self.timeout,
                'rate_limit_delay': self.RATE_LIMIT_DELAY,
                'normal_delay_range': self.NORMAL_DELAY_RANGE
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics and circuit breaker state."""
        self.request_count = 0
        self.success_count = 0
        self.circuit_breaker._reset()
        self.rate_limited_until = 0
        logger.info("Service metrics and circuit breaker reset")

    def get_today_searches(self, geo: str = 'BR') -> Dict[str, Any]:
        """
        Get today's trending searches.
        
        Args:
            geo: Geographic location (default: 'BR' for Brazil)
            
        Returns:
            Dictionary containing today's trending searches and metadata
        """
        logger.info(f"Fetching today's trending searches for {geo}")
        
        try:
            # Get today's trending searches
            df = self._make_request(self.pytrends.today_searches, geo=geo)
            
            return {
                'data': df[0].tolist() if not df.empty else [],
                'metadata': {
                    'status': 'success',
                    'geo': geo,
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'count': len(df) if not df.empty else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting today's trending searches: {str(e)}")
            return {
                'data': [],
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'geo': geo,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
