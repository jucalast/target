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
        # Valida entrada
        if not raw_data:
            logger.warning("Dados do Google Trends vazios")
            return {}
        
        # Tenta diferentes estruturas de dados
        interest_data = None
        if 'interest' in raw_data:
            interest_data = raw_data['interest']
        elif 'data' in raw_data:
            interest_data = raw_data['data']
        else:
            # Assume que raw_data já são os dados de interesse
            interest_data = raw_data
        
        # Verifica se interest_data é um DataFrame ou dicionário válido
        if hasattr(interest_data, 'empty') and interest_data.empty:
            logger.warning("DataFrame do Google Trends vazio")
            return {}
        elif isinstance(interest_data, dict) and not interest_data:
            logger.warning("Dados do Google Trends sem conteúdo")
            return {}
        elif isinstance(interest_data, list) and not interest_data:
            logger.warning("Lista de dados do Google Trends vazia")
            return {}
            
        try:
            # Processa os dados de interesse ao longo do tempo
            if hasattr(interest_data, 'columns'):  # É um DataFrame pandas
                data_to_process = interest_data
                related_queries = raw_data.get('related_queries', {})
                
                # Para cada coluna (exceto date), cria uma SearchTrend
                trends = {}
                for column in data_to_process.columns:
                    if column.lower() in ['date', 'datetime']:
                        continue
                        
                    # Extrai a série temporal para esta coluna
                    timeline = []
                    for idx, row in data_to_process.iterrows():
                        try:
                            date = row.get('date', idx)
                            value = int(row[column]) if pd.notna(row[column]) else 0
                            
                            # Converte a data para string ISO para compatibilidade com JSON
                            if hasattr(date, 'isoformat'):
                                date_str = date.isoformat()
                            elif isinstance(date, str):
                                date_str = date
                            else:
                                date_str = str(date)
                            
                            timeline.append({"date": date_str, "value": float(value)})
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Erro ao processar linha do DataFrame: {str(e)}")
                    
                    # Obtém consultas relacionadas para este termo
                    term_related = self._extract_related_queries(related_queries.get(column, {}))
                    
                    # Cria a SearchTrend
                    trends[column] = SearchTrend(
                        keyword=column,
                        values=timeline,
                        related_queries=term_related,
                        interest_by_region=[]
                    )
                
                return trends
                
            elif isinstance(interest_data, dict):  # É um dicionário com estrutura especial
                if 'columns' in interest_data and 'data' in interest_data:
                    # Formato especial: {'columns': ['date', 'term1'], 'data': [['2024-01-01', 50]]}
                    columns = interest_data['columns']
                    data_rows = interest_data['data']
                    
                    if len(columns) < 2:
                        logger.warning("Colunas insuficientes nos dados do Google Trends")
                        return {}
                    
                    # Os termos de busca são todas as colunas exceto a primeira (data)
                    terms = columns[1:]
                    related_queries = raw_data.get('related_queries', {})
                    
                    # Para cada termo, cria uma SearchTrend
                    trends = {}
                    for i, term in enumerate(terms, start=1):
                        # Extrai a série temporal para este termo
                        timeline = []
                        for row in data_rows:
                            if len(row) > i:  # Verifica se a linha tem dados para este termo
                                try:
                                    date_str = row[0]
                                    value = int(row[i]) if row[i] != '' and row[i] is not None else 0
                                    
                                    # Usa a data diretamente como string
                                    timeline.append({"date": str(date_str), "value": float(value)})
                                except (ValueError, IndexError) as e:
                                    logger.warning(f"Erro ao processar linha do Google Trends: {str(e)}")
                        
                        # Obtém consultas relacionadas para este termo
                        term_related = self._extract_related_queries(related_queries.get(term, {}))
                        
                        # Cria a SearchTrend
                        trends[term] = SearchTrend(
                            keyword=term,
                            values=timeline,
                            related_queries=term_related,
                            interest_by_region=[]
                        )
                    
                    return trends
                elif 'data' in interest_data and 'metadata' in interest_data:
                    # Formato do pytrends: {'data': DataFrame, 'metadata': {...}}
                    trends_df = interest_data['data']
                    
                    # Se trends_df é uma lista, converte para DataFrame
                    if isinstance(trends_df, list) and trends_df:
                        import pandas as pd
                        trends_df = pd.DataFrame(trends_df)
                    
                    if hasattr(trends_df, 'columns') and hasattr(trends_df, 'iterrows'):
                        # É um DataFrame pandas
                        trends = {}
                        for column in trends_df.columns:
                            if column.lower() in ['date', 'datetime']:
                                continue
                                
                            # Extrai a série temporal para esta coluna
                            timeline = []
                            for idx, row in trends_df.iterrows():
                                try:
                                    date = row.get('date', idx) if 'date' in trends_df.columns else idx
                                    value = int(row[column]) if pd.notna(row[column]) else 0
                                    
                                    # Converte a data para string ISO para compatibilidade com JSON
                                    if hasattr(date, 'isoformat'):
                                        date_str = date.isoformat()
                                    elif isinstance(date, str):
                                        date_str = date
                                    else:
                                        date_str = str(date)
                                    
                                    timeline.append({"date": date_str, "value": float(value)})
                                except (ValueError, KeyError) as e:
                                    logger.warning(f"Erro ao processar linha do DataFrame: {str(e)}")
                            
                            # Obtém consultas relacionadas para este termo
                            term_related = self._extract_related_queries(raw_data.get('related_queries', {}).get(column, {}))
                            
                            # Cria a SearchTrend
                            trends[column] = SearchTrend(
                                keyword=column,
                                values=timeline,
                                related_queries=term_related,
                                interest_by_region=[]
                            )
                        
                        return trends
                    else:
                        logger.warning(f"Dados do Google Trends não são um DataFrame válido: {type(trends_df)}")
                        return {}
                        
                else:
                    logger.warning(f"Formato de dicionário do Google Trends não suportado: {list(interest_data.keys())}")
                    return {}
                
            elif isinstance(interest_data, list) and interest_data:  # É uma lista de records
                # Converte lista de dicts para DataFrame para processamento
                try:
                    import pandas as pd
                    trends_df = pd.DataFrame(interest_data)
                    
                    if trends_df.empty:
                        logger.warning("DataFrame do Google Trends está vazio")
                        return {}
                    
                    # Remove colunas desnecessárias se existirem
                    if 'isPartial' in trends_df.columns:
                        trends_df = trends_df.drop(columns=['isPartial'])
                    
                    # Processa o DataFrame como antes
                    date_column = None
                    for col in ['date', 'Date', 'DATE']:
                        if col in trends_df.columns:
                            date_column = col
                            break
                    
                    if date_column is None:
                        logger.warning("Coluna de data não encontrada nos dados do Google Trends")
                        return {}
                    
                    # Extrai termos (todas as colunas numéricas exceto data)
                    numeric_columns = trends_df.select_dtypes(include=['number']).columns
                    terms = [col for col in numeric_columns if col != date_column]
                    
                    if not terms:
                        logger.warning("Nenhum termo encontrado nos dados do Google Trends")
                        return {}
                    
                    related_queries = raw_data.get('related_queries', {})
                    
                    # Para cada termo, cria uma SearchTrend
                    trends = {}
                    for term in terms:
                        # Extrai a série temporal para este termo
                        timeline = []
                        for _, row in trends_df.iterrows():
                            if pd.notna(row[date_column]) and pd.notna(row[term]):
                                date_val = row[date_column]
                                if hasattr(date_val, 'isoformat'):
                                    date_str = date_val.isoformat()
                                elif isinstance(date_val, str):
                                    date_str = date_val
                                else:
                                    date_str = str(date_val)
                                
                                timeline.append({"date": date_str, "value": float(row[term])})
                        
                        if not timeline:
                            continue
                        
                        term_related = related_queries.get(term, {})
                        
                        trends[term] = SearchTrend(
                            keyword=term,
                            values=timeline,
                            related_queries=term_related,
                            interest_by_region=[]
                        )
                    
                    return trends
                    
                except Exception as e:
                    logger.error(f"Erro ao processar lista de dados do Google Trends: {str(e)}")
                    return {}
            
            else:
                logger.warning(f"Formato de dados do Google Trends não suportado: {type(interest_data)}")
                return {}
            
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
            values = []
            last_point = None
            for point_dict in trend.values:
                # Agora esperamos o formato {"date": "2024-01-01", "value": 50.0}
                if "date" in point_dict and "value" in point_dict:
                    values.append(point_dict["value"])
                    last_point = point_dict
                    
            if not values or not last_point:
                continue
            
            # Calcula a tendência (variação percentual em relação à média)
            avg_value = sum(values) / len(values)
            trend_value = ((last_point["value"] - avg_value) / avg_value * 100) if avg_value > 0 else 0
            
            # Tenta converter a data string para datetime, com fallback
            try:
                if isinstance(last_point["date"], str):
                    last_date = datetime.fromisoformat(last_point["date"].replace('Z', '+00:00'))
                else:
                    last_date = datetime.now()
            except (ValueError, AttributeError):
                last_date = datetime.now()
            
            # Cria o ponto de dado atual
            current_value = DataPoint(
                value=last_point["value"],
                source=DataSource.GOOGLE_TRENDS,
                timestamp=last_date,
                confidence=0.8,  # Confiança moderada para dados do Google Trends
                quality=DataQualityLevel.MEDIUM,
                meta_info={
                    'unidade': 'índice (0-100)',
                    'fonte': 'Google Trends',
                    'termo': term
                }
            )
            
            # Cria pontos históricos
            historical_values = []
            for point_dict in trend.values:
                if "date" in point_dict and "value" in point_dict:
                    try:
                        if isinstance(point_dict["date"], str):
                            point_date = datetime.fromisoformat(point_dict["date"].replace('Z', '+00:00'))
                        else:
                            point_date = datetime.now()
                    except (ValueError, AttributeError):
                        point_date = datetime.now()
                    
                    historical_values.append(DataPoint(
                        value=point_dict["value"],
                        source=DataSource.GOOGLE_TRENDS,
                        timestamp=point_date,
                        confidence=0.8,
                        quality=DataQualityLevel.MEDIUM,
                        meta_info={'unidade': 'índice (0-100)', 'fonte': 'Google Trends'}
                    ))
            
            # Cria a métrica
            metric_name = f"tendencia_busca_{term.lower().replace(' ', '_')}"
            metrics[metric_name] = MarketMetric(
                name=f"Tendência de Busca: {term}",
                description=f"Interesse de busca no Google pelo termo '{term}'",
                unit="índice (0-100)",
                current_value=current_value,
                historical_values=historical_values,
                trend=trend_value
            )
        
        return metrics
