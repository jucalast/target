"""
Google Trends Service

This service provides functionality to collect search interest data from Google Trends.
It's designed to be used as a supplementary data source for market analysis.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import random
import pandas as pd
from pytrends.request import TrendReq
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Service for collecting and processing Google Trends data."""


    def __init__(self, hl: str = 'pt-BR', tz: int = 180, timeout: int = (10, 25)):
        """
        Initialize the Google Trends service.

        Args:
            hl: Language (default: 'pt-BR' for Brazilian Portuguese)
            tz: Timezone offset in minutes (default: 180 for Brasilia time)
            timeout: Timeout for requests in seconds (connect, read)
        """
        self.hl = hl
        self.tz = tz
        self.timeout = timeout
        self.pytrends = None
        self._connect()


    def _connect(self) -> None:
        """Establish a connection to Google Trends."""
        try:
            self.pytrends = TrendReq(
                hl=self.hl,
                tz=self.tz,
                timeout=self.timeout,
                retries=2,
                backoff_factor=0.1,
                requests_args={'verify': False}
            )
            logger.info("Successfully connected to Google Trends")
        except Exception as e:
            logger.error(f"Failed to connect to Google Trends: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )


    def _make_request(self, func, *args, **kwargs):
        """Make a request with retry logic and rate limiting."""
        try:
            # Add random delay to avoid hitting rate limits
            time.sleep(random.uniform(1, 3))
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Request failed: {str(e)}. Retrying...")
            self._connect()  # Reconnect before retrying
            raise


    def get_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = 'today 12-m',
        geo: str = 'BR',
        gprop: str = 'web',
        cat: int = 0,
        sleep: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get interest over time for the given keywords.

        Args:
            keywords: List of search terms
            timeframe: Time period for the data (e.g., 'today 12-m' for last 12 months)
            geo: Geographic location (default: 'BR' for Brazil)
            gprop: Google's property to filter on (web, news, images, froogle, youtube)
            cat: Category to narrow results (0 for all categories)
            sleep: Seconds to wait between requests

        Returns:
            Dictionary containing the interest over time data and metadata
        """
        if not keywords:
            return {'data': pd.DataFrame(), 'metadata': {'status': 'error', 'message': 'No keywords provided'}}

        logger.info(f"Fetching interest over time for keywords: {keywords}")

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
                return {'data': df, 'metadata': {'status': 'no_data', 'message': 'No data returned'}}

            # Prepare the result
            result = {
                'data': df.reset_index().to_dict('records'),
                'metadata': {
                    'status': 'success',
                    'keywords': keywords,
                    'timeframe': timeframe,
                    'geo': geo,
                    'gprop': gprop,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data_points': len(df)
                }
            }

            # Add sleep if needed to avoid rate limiting
            if sleep > 0:
                time.sleep(sleep)

            return result

        except Exception as e:
            logger.error(f"Error getting interest over time: {str(e)}")
            return {
                'data': pd.DataFrame(),
                'metadata': {
                    'status': 'error',
                    'message': str(e),
                    'keywords': keywords,
                    'timestamp': datetime.utcnow().isoformat()
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
