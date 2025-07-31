"""Data formatters for standardizing output formats."""
from typing import Dict, Any, List, Optional
from datetime import datetime

    MarketAnalysisOutput, NLPAnalysis, Keyword, Topic, Entity, Embedding,
    IBGEData, GoogleTrendsData
)

def format_market_analysis(
    analysis_id: str,
    input_data: Dict[str, Any],
    nlp_features: Dict[str, Any],
    ibge_data: Dict[str, Any],
    google_trends_data: Optional[Dict[str, Any]] = None,
    insights: Optional[Dict[str, Any]] = None,
    processing_time: Optional[float] = None,
    status: str = "completed"
) -> MarketAnalysisOutput:
"""Format market analysis data into a standardized output format."""
    return MarketAnalysisOutput(
        analysis_id=analysis_id,
        timestamp=datetime.utcnow(),
        status=status,
        input=input_data,
        nlp=_format_nlp_analysis(nlp_features),
        ibge={
        code: _format_ibge_data(code, data)
            for code, data in ibge_data.items()
        },
        google_trends=
            _format_google_trends(google_trends_data) if google_trends_data else None,
        insights=insights or {},
        processing_time=processing_time
    )

def _format_nlp_analysis(features: Dict[str, Any]) -> NLPAnalysis:
"""Format NLP features."""
    return NLPAnalysis(
        keywords=[
        Keyword(keyword=k['keyword'], score=k.get('score', 0.0), \
                source=k.get('source'))
            for k in features.get('keywords', [])
],
topics=[
Topic(
    label=t['topic'],
    weight=t.get('weight', 0.0),
    keywords=[
    Keyword(keyword=kw['keyword'], score=kw.get('score', 0.0))
                    for kw in t.get('keywords', [])
]
            )
            for t in features.get('topics', [])
],
entities=[
Entity(text=e['text'], type=e['type'], start=e['start'], \
                end=e['end'])
            for e in features.get('entities', [])
],
embeddings={
k: Embedding(
    model=v.get('model', ''),
    vector=v.get('vector', []),
    dim=len(v.get('vector', []))
            )
            for k, v in features.get('embeddings', {}).items()
        }
    )

def _format_ibge_data(table_code: str, data: Dict[str, Any]) -> IBGEData:
"""Format IBGE data."""
    return IBGEData(
        table_code=table_code,
        table_name=data.get('metadata', {}).get('name', ''),
        period=data.get('period', ''),
        data=data.get('data', []),
        variables=data.get('variables', [])
    )

def _format_google_trends(data: Dict[str, Any]) -> GoogleTrendsData:
"""Format Google Trends data."""
    return GoogleTrendsData(
        interest_over_time=data.get('interest_over_time', {}).get('data', []),
        related_queries={
        k: v.get('data', {})
            for k, v in data.get('related_queries', {}).items()
        }
    )
