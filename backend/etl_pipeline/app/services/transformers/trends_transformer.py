"""
Transformador de dados do Google Trends.

Este módulo contém classes para transformar os dados brutos do Google Trends
em um formato padronizado para análise posterior.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from shared.schemas.etl_output import SearchTrend, MarketMetric, DataPoint, DataSource, DataQualityLevel

logger = logging.getLogger(__name__)

class TrendsTransformer:
    """Transforma dados brutos do Google Trends em métricas padronizadas."""
    
    def __init__(self):
        self.processed_data = {}
    
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, SearchTrend]:
        """
        Transforma os dados brutos do Google Trends em tendências de busca.
        
        Args:
            raw_data: Dicionário com os dados brutos do Google Trends
            
        Returns:
            Dicionário de SearchTrend com as tendências processadas
        """
        if not raw_data or 'interest' not in raw_data or not raw_data['interest'].get('data'):
            logger.warning("Dados do Google Trends vazios ou em formato inválido")
            return {}
            
        try:
            # Processa os dados de interesse ao longo do tempo
            interest_data = raw_data['interest']['data']
            related_queries = raw_data.get('related', {})
            
            # Para cada termo de busca, cria uma SearchTrend
            trends = {}
            
            # Obtém a lista de termos de busca
            if not interest_data:
                return {}
                
            # O primeiro item contém as colunas (data, termo1, termo2, ...)
            columns = interest_data[0]
            if len(columns) < 2:  # Precisa ter pelo menos data e um termo
                return {}
                
            # Os termos de busca são todas as colunas exceto a primeira (data)
            terms = columns[1:]
            
            # Para cada termo, cria uma SearchTrend
            for i, term in enumerate(terms, start=1):
                # Extrai a série temporal para este termo
                timeline = []
                for row in interest_data[1:]:  # Pula o cabeçalho
                    if len(row) > i:  # Verifica se a linha tem dados para este termo
                        try:
                            date_str = row[0]
                            value = int(row[i]) if row[i] != '' else 0
                            
                            # Converte a data para datetime
                            date = self._parse_date(date_str)
                            if date:
                                timeline.append({"date": date, "value": value})
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Erro ao processar linha do Google Trends: {str(e)}")
                
                # Obtém consultas relacionadas para este termo
                term_related = self._extract_related_queries(related_queries.get(term, {}))
                
                # Cria a SearchTrend
                trends[term] = SearchTrend(
                    keyword=term,
                    values=timeline,
                    related_queries=term_related,
                    interest_by_region=[]  # Pode ser preenchido posteriormente
                )
            
            return trends
            
        except Exception as e:
            logger.error(f"Erro ao transformar dados do Google Trends: {str(e)}", exc_info=True)
            return {}
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Converte uma string de data do Google Trends para datetime."""
        try:
            # Tenta diferentes formatos de data
            formats = [
                '%Y-%m-%d',  # 2023-01-01
                '%Y-%m',    # 2023-01
                '%Y'        # 2023
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning(f"Formato de data não reconhecido: {date_str}")
            return None
            
        except Exception as e:
            logger.warning(f"Erro ao converter data '{date_str}': {str(e)}")
            return None
    
    def _extract_related_queries(self, related_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai consultas relacionadas dos dados brutos."""
        result = []
        
        if not related_data:
            return result
        
        try:
            # Processa consultas em alta (rising)
            if 'rising' in related_data and related_data['rising']:
                rising = related_data['rising']
                if isinstance(rising, list) and len(rising) > 0:
                    result.append({
                        'type': 'rising',
                        'queries': [
                            {
                                'query': item.get('query', ''),
                                'value': item.get('value', 0),
                                'growth': item.get('growth', 0)
                            }
                            for item in rising
                        ]
                    })
            
            # Processa principais consultas (top)
            if 'top' in related_data and related_data['top']:
                top = related_data['top']
                if isinstance(top, list) and len(top) > 0:
                    result.append({
                        'type': 'top',
                        'queries': [
                            {
                                'query': item.get('query', ''),
                                'value': item.get('value', 0)
                            }
                            for item in top
                        ]
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao extrair consultas relacionadas: {str(e)}")
            return []
    
    def create_market_metrics(self, trends_data: Dict[str, SearchTrend]) -> Dict[str, MarketMetric]:
        """
        Cria métricas de mercado a partir dos dados de tendências.
        
        Args:
            trends_data: Dicionário de SearchTrend com as tendências processadas
            
        Returns:
            Dicionário de MarketMetric com as métricas de tendência
        """
        metrics = {}
        
        for term, trend in trends_data.items():
            if not trend.values:
                continue
                
            # Calcula métricas básicas
            values = [point['value'] for point in trend.values if 'value' in point]
            if not values:
                continue
                
            # Ponto de dado atual (último valor disponível)
            last_point = trend.values[-1]
            
            # Calcula a tendência (variação percentual em relação à média)
            avg_value = sum(values) / len(values)
            trend_value = ((last_point['value'] - avg_value) / avg_value * 100) if avg_value > 0 else 0
            
            # Cria o ponto de dado atual
            current_value = DataPoint(
                value=last_point['value'],
                source=DataSource.GOOGLE_TRENDS,
                timestamp=last_point['date'],
                confidence=0.8,  # Confiança moderada para dados do Google Trends
                quality=DataQualityLevel.MEDIUM,
                meta_info={
                    'unidade': 'índice (0-100)',
                    'fonte': 'Google Trends',
                    'termo': term
                }
            )
            
            # Cria a métrica
            metric_name = f"tendencia_busca_{term.lower().replace(' ', '_')}"
            metrics[metric_name] = MarketMetric(
                name=f"Tendência de Busca: {term}",
                description=f"Interesse de busca no Google pelo termo '{term}'",
                unit="índice (0-100)",
                current_value=current_value,
                historical_values=[
                    DataPoint(
                        value=point['value'],
                        source=DataSource.GOOGLE_TRENDS,
                        timestamp=point['date'],
                        confidence=0.8,
                        quality=DataQualityLevel.MEDIUM,
                        meta_info={'unidade': 'índice (0-100)', 'fonte': 'Google Trends'}
                    )
                    for point in trend.values
                ],
                trend=trend_value
            )
        
        return metrics
