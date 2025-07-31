"""ETL Pipeline Service

Orchestrates data extraction, transformation, and loading from multiple sources.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session

from shared.schemas.analysis import AnalysisCreate
from shared.db.models.analysis import Analysis as AnalysisModel
from etl_pipeline.app.services.nlp_service import extract_features
from etl_pipeline.app.services.sidra_mapper import SIDRAMapper
from etl_pipeline.app.services.google_trends_service import GoogleTrendsService
from etl_pipeline.app.services.sidra_client import SidraClient

logger = logging.getLogger(__name__)

class ETLPipeline:
    """ETL pipeline for market analysis data."""
    
    def __init__(self, db: Session, max_workers: int = 3):
        self.db = db
        self.max_workers = max_workers
        self.sidra_mapper = SIDRAMapper()
        self.sidra_client = SidraClient()
        self.google_trends = GoogleTrendsService()
        self.cache = {}
    
    def run_pipeline(self, user_id: int, analysis_input: AnalysisCreate) -> Dict[str, Any]:
        """Run the complete ETL pipeline."""
        logger.info(f"Starting ETL pipeline for user {user_id}")
        start_time = time.time()
        
        try:
            # 1. Extract data
            self._extract_data(analysis_input)
            
            # 2. Transform data
            transformed = self._transform_data(analysis_input)
            
            # 3. Load data
            result = self._load_data(user_id, analysis_input, transformed)
            
            return {
                'status': 'success',
                'analysis_id': result.id,
                'processing_time': time.time() - start_time,
                'sources': list(transformed.keys() - {'metadata'})
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _extract_data(self, analysis_input: AnalysisCreate) -> None:
        """Extract data from all sources."""
        # Extract NLP features
        self.cache['nlp_features'] = extract_features(
            niche=analysis_input.niche,
            description=analysis_input.description
        )
        
        # Extract from other sources in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._extract_ibge_data),
                executor.submit(self._extract_google_trends)
            ]
            for future in as_completed(futures):
                future.result()
    
    def _extract_ibge_data(self) -> None:
        """Extract data from IBGE SIDRA."""
        try:
            keywords = [kw['keyword'] for kw in self.cache['nlp_features'].get('keywords', [])]
            params = self.sidra_mapper.map_terms_to_sidra_parameters(keywords)
            
            table_code = params.pop('tabela', '6401')
            self.cache['ibge_data'] = self.sidra_client.get_table(
                table_code=table_code,
                variables=params.get('variaveis', []),
                classifications=params.get('classificacoes', {})
            )
        except Exception as e:
            logger.error(f"IBGE extraction failed: {str(e)}")
            self.cache['ibge_data'] = {}
    
    def _extract_google_trends(self) -> None:
        """Extract data from Google Trends."""
        try:
            keywords = [kw['keyword'] for kw in self.cache['nlp_features'].get('keywords', [])[:5]]
            
            self.cache['google_trends'] = {
                'interest': self.google_trends.get_interest_over_time(keywords, 'today 12-m', 'BR'),
                'related': {k: self.google_trends.get_related_queries([k], 'today 3-m', 'BR') 
                           for k in keywords}
            }
        except Exception as e:
            logger.error(f"Google Trends extraction failed: {str(e)}")
            self.cache['google_trends'] = {}
    
    def _transform_data(self, analysis_input: AnalysisCreate) -> Dict[str, Any]:
        """Transform extracted data into a unified format."""
        return {
            'metadata': {
                'user_input': {
                    'niche': analysis_input.niche,
                    'description': analysis_input.description,
                    'timestamp': datetime.utcnow().isoformat()
                }
            },
            'nlp_features': self.cache.get('nlp_features', {}),
            'ibge_data': self.cache.get('ibge_data', {}),
            'google_trends': self.cache.get('google_trends', {})
        }
    
    def _load_data(self, user_id: int, analysis_input: AnalysisCreate, 
                  transformed_data: Dict[str, Any]) -> AnalysisModel:
        """Load transformed data into the database."""
        analysis = AnalysisModel(
            user_id=user_id,
            niche=analysis_input.niche,
            description=analysis_input.description,
            data=transformed_data,
            status='completed'
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
