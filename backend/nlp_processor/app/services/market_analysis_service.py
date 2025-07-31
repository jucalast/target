"""Market Analysis Service

Orchestrates NLP processing with IBGE data collection for market analysis.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.schemas.analysis import AnalysisCreate
from app.models.analysis import Analysis as AnalysisModel
from .nlp_service import extract_features
from .sidra_client import SidraClient  # Assumes we have a SIDRA client

logger = logging.getLogger(__name__)

class MarketAnalysisService:
    """Service for market analysis combining NLP with IBGE data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.sidra_client = SidraClient()
        
    def analyze_market_segment(self, user_id: int, analysis_input: AnalysisCreate) -> Dict[str, Any]:
        """Orchestrate the market analysis pipeline."""
        logger.info(f"Starting market analysis for: {analysis_input.niche}")
        
        # 1. Extract NLP features
        nlp_features = self._extract_nlp_features(analysis_input)
        
        # 2. Map to IBGE parameters
        ibge_parameters = self._map_to_ibge_parameters(nlp_features)
        
        # 3. Collect IBGE data
        ibge_data = self._collect_ibge_data(ibge_parameters)
        
        # 4. Combine results
        analysis_result = self._combine_results(
            nlp_features=nlp_features,
            ibge_data=ibge_data,
            user_id=user_id,
            analysis_input=analysis_input
        )
        
        # 5. Save to database
        db_analysis = self._save_analysis(analysis_result)
        analysis_result['metadata']['analysis_id'] = db_analysis.id
        
        logger.info(f"Analysis completed. ID: {db_analysis.id}")
        return analysis_result
    
    def _extract_nlp_features(self, analysis_input: AnalysisCreate) -> Dict[str, Any]:
        """Extract features using NLP service."""
        return extract_features(
            niche=analysis_input.niche,
            description=analysis_input.description
        )
    
    def _map_to_ibge_parameters(self, nlp_features: Dict[str, Any]) -> Dict[str, Any]:
        """Map NLP concepts to IBGE API parameters."""
        parameters = {
            'tabela': '6401',  # Default to PNAD Contínua
            'variaveis': [],
            'classificacoes': {},
            'localidades': ['BR'],
            'periodo': 'last'
        }
        
        # Simplified mapping - expand as needed
        keywords = [kw['keyword'] for kw in nlp_features.get('keywords', [])]
        
        # Example mapping (simplified)
        if any(kw in ['renda', 'salário'] for kw in keywords):
            parameters['variaveis'].extend(['2979', '2980'])  # Income variables
            
        if any(kw in ['idade', 'faixa etária'] for kw in keywords):
            parameters['classificacoes']['200'] = '1933'  # Age range
            
        return parameters
    
    def _collect_ibge_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from IBGE SIDRA API."""
        try:
            return self.sidra_client.get_table(
                table_code=parameters['tabela'],
                variables=parameters.get('variaveis', []),
                classifications=parameters.get('classificacoes', {}),
                locations=parameters.get('localidades', ['BR']),
                period=parameters.get('periodo', 'last')
            )
        except Exception as e:
            logger.error(f"Error fetching IBGE data: {str(e)}")
            return {'error': str(e), 'data': []}
    
    def _combine_results(self, nlp_features: Dict[str, Any], 
                        ibge_data: Dict[str, Any],
                        user_id: int,
                        analysis_input: AnalysisCreate) -> Dict[str, Any]:
        """Combine NLP and IBGE data into final result."""
        return {
            'metadata': {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            },
            'input': {
                'niche': analysis_input.niche,
                'description': analysis_input.description
            },
            'nlp_analysis': nlp_features,
            'market_data': ibge_data,
            'insights': self._generate_insights(nlp_features, ibge_data)
        }
    
    def _generate_insights(self, nlp_features: Dict[str, Any], 
                          ibge_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate initial insights from the analysis."""
        insights = []
        # Add insight generation logic here
        return insights
        
    def _save_analysis(self, analysis_result: Dict[str, Any]) -> AnalysisModel:
        """Save analysis results to database."""
        db_analysis = AnalysisModel(
            user_id=analysis_result['metadata']['user_id'],
            niche=analysis_result['input']['niche'],
            description=analysis_result['input']['description'],
            normalized_text=analysis_result['nlp_analysis'].get('normalized_text', ''),
            keywords=analysis_result['nlp_analysis'].get('keywords', []),
            entities=analysis_result['nlp_analysis'].get('entities', []),
            embedding=analysis_result['nlp_analysis'].get('embeddings', {}).get('spacy', []),
            ibge_data=analysis_result['market_data'],
            insights=analysis_result['insights']
        )
        
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        
        return db_analysis
