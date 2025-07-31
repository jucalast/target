"""
Transformador de dados do IBGE SIDRA.

Este módulo contém classes para transformar os dados brutos do IBGE SIDRA
em um formato padronizado para análise posterior.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from shared.schemas.etl_output import MarketSegment, MarketMetric, DataPoint, DataSource, DataQualityLevel

logger = logging.getLogger(__name__)


class IBGETransformer:
    """Transforma dados brutos do IBGE SIDRA em métricas padronizadas."""

    # Mapeamento de códigos de variáveis para nomes amigáveis
    VARIABLE_MAPPING = {
        # PNAD Contínua - Tabela 6401
        "4099": "populacao_total",
        "4100": "populacao_ocupada",
        "4103": "taxa_desemprego",
        "4104": "taxa_participacao",
        "4119": "rendimento_medio",
        "4120": "rendimento_mediano",
        "4121": "rendimento_medio_ocupados",
        "4122": "rendimento_mediano_ocupados",

        # POF - Tabela 7482 (Despesas)
        "11046": "despesa_media_mensal",
        "11047": "despesa_media_anual",

        # PNAD - Tabela 6407 (Rendimento)
        "2979": "rendimento_medio_todas_fontes",
        "2980": "rendimento_mediano_todas_fontes",
    }

    # Mapeamento de classificações para nomes amigáveis
    CLASSIFICATION_MAPPING = {
        "200": {
            "name": "faixa_etaria",
            "categories": {
                "1930": "14_a_17_anos",
                "1931": "18_a_24_anos",
                "1932": "25_a_39_anos",
                "1933": "40_a_59_anos",
                "1934": "60_anos_ou_mais",
            }
        },
        "201": {
            "name": "sexo",
            "categories": {
                "3": "homens",
                "4": "mulheres"
            }
        },
        "202": {
            "name": "cor_ou_raca",
            "categories": {
                "5": "branca",
                "6": "preta",
                "7": "parda",
                "8": "amarela",
                "9": "indigena"
            }
        }
    }


    def __init__(self):
        self.processed_data = {}


    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, MarketSegment]:
        """
        Transforma os dados brutos do IBGE em segmentos de mercado.

        Args:
            raw_data: Dicionário com os dados brutos do IBGE SIDRA

        Returns:
            Dicionário de MarketSegment com os dados transformados
        """
        if not raw_data or 'value' not in raw_data or not raw_data['value']:
            logger.warning("Dados do IBGE vazios ou em formato inválido")
            return {}

        try:
            # Converte os dados para DataFrame
            df = pd.DataFrame(raw_data['value'])

            # Processa os dados por variável
            for _, row in df.iterrows():
                self._process_row(row)

            return self._create_market_segments()

        except Exception as e:
            logger.error(f"Erro ao transformar dados do IBGE: {str(e)}", exc_info=True)
            return {}


    def _process_row(self, row: pd.Series) -> None:
        """Processa uma linha de dados do IBGE."""
        try:
            variable_code = str(row.get('V', ''))
            classification_code = str(row.get('C', ''))
            category_code = str(row.get('C2', ''))

            # Obtém o nome amigável da variável
            var_name = self.VARIABLE_MAPPING.get(variable_code, f"var_{variable_code}")

            # Obtém o nome da classificação e categoria, se houver
            classification_name = "geral"
            category_name = "total"

            if classification_code and category_code:
                classification_info = self.CLASSIFICATION_MAPPING.get(classification_code, {})
                classification_name = classification_info.get('name', f"class_{classification_code}")

                if 'categories' in classification_info:
                    category_name = classification_info['categories'].get(
                        category_code, 
                        f"cat_{category_code}"
                    )

            # Obtém o valor e a unidade
            value = self._parse_value(row.get('V', ''), row.get('D1C', ''))
            unit = row.get('D1N', '')

            # Armazena o dado processado
            if classification_name not in self.processed_data:
                self.processed_data[classification_name] = {}

            if category_name not in self.processed_data[classification_name]:
                self.processed_data[classification_name][category_name] = {}

            self.processed_data[classification_name][category_name][var_name] = {
                'value': value,
                'unit': unit,
                'timestamp': row.get('D1C', '')
            }

        except Exception as e:
            logger.error(f"Erro ao processar linha do IBGE: {str(e)}", exc_info=True)


    def _create_market_segments(self) -> Dict[str, MarketSegment]:
        """Cria segmentos de mercado a partir dos dados processados."""
        segments = {}

        # Cria um segmento para cada classificação
        for classification, categories in self.processed_data.items():
            for category, metrics in categories.items():
                segment_name = f"{classification}_{category}"

                # Cria as métricas do segmento
                market_metrics = {}

                for metric_name, metric_data in metrics.items():
                    # Cria o ponto de dado atual
                    current_value = DataPoint(
                        value=metric_data['value'],
                        source=DataSource.IBGE_SIDRA,
                        timestamp=datetime.strptime(metric_data['timestamp'], '%Y%m'),
                        confidence=0.9,  # Alto nível de confiança para dados do IBGE
                        quality=DataQualityLevel.HIGH,
                        meta_info={
                            'unidade': metric_data['unit'],
                            'fonte': 'IBGE SIDRA'
                        }
                    )

                    # Cria a métrica
                    market_metrics[metric_name] = MarketMetric(
                        name=self._get_metric_display_name(metric_name),
                        description=self._get_metric_description(metric_name),
                        unit=metric_data['unit'],
                        current_value=current_value,
                        historical_values=[current_value]  # Por enquanto, só temos o valor atual
                    )

                # Cria o segmento
                segments[segment_name] = MarketSegment(
                    name=self._get_segment_display_name(classification, category),
                    description=f"Dados para {category} baseados na classificação {classification}",
                    metrics=market_metrics
                )

        return segments


    def _parse_value(self, value: str, code: str) -> float:
        """Converte o valor para o tipo apropriado."""
        try:
            # Remove pontos de milhar e substitui vírgula por ponto
            clean_value = str(value).replace('.', '').replace(',', '.')
            return float(clean_value)
        except (ValueError, TypeError):
            logger.warning(f"Não foi possível converter o valor '{value}' (código: {code}) para float")
            return 0.0


    def _get_metric_display_name(self, metric_code: str) -> str:
        """Retorna o nome de exibição amigável para uma métrica."""
        names = {
            'populacao_total': 'População Total',
            'populacao_ocupada': 'População Ocupada',
            'taxa_desemprego': 'Taxa de Desemprego',
            'taxa_participacao': 'Taxa de Participação',
            'rendimento_medio': 'Rendimento Médio',
            'rendimento_mediano': 'Rendimento Mediano',
            'despesa_media_mensal': 'Despesa Média Mensal',
            'despesa_media_anual': 'Despesa Média Anual',
        }
        return names.get(metric_code, metric_code.replace('_', ' ').title())


    def _get_metric_description(self, metric_code: str) -> str:
        """Retorna a descrição detalhada de uma métrica."""
        descriptions = {
            'populacao_total': 'Número total de pessoas na população de referência',
            'populacao_ocupada': 'Número de pessoas ocupadas na semana de referência',
            'taxa_desemprego': 'Percentual de desempregados na força de trabalho',
            'taxa_participacao': 'Percentual da população em idade ativa que está na força de trabalho',
            'rendimento_medio': 'Rendimento médio de todas as fontes de renda',
            'rendimento_mediano': 'Rendimento mediano de todas as fontes de renda',
            'despesa_media_mensal': 'Média de despesas mensais por domicílio',
            'despesa_media_anual': 'Média de despesas anuais por domicílio',
        }
        return descriptions.get(metric_code, '')


    def _get_segment_display_name(self, classification: str, category: str) -> str:
        """Retorna o nome de exibição amigável para um segmento."""
        # Exemplo: "faixa_etaria_25_a_39_anos" -> "Faixa Etária: 25 a 39 Anos"
        if classification == 'faixa_etaria':
            return f"Faixa Etária: {category.replace('_', ' ').title()}"
        elif classification == 'sexo':
            return f"Sexo: {category.title()}"
        elif classification == 'cor_ou_raca':
            return f"Cor/Raça: {category.title()}"
        else:
            return f"{classification.replace('_', ' ').title()}: {category.replace('_', ' ').title()}"
