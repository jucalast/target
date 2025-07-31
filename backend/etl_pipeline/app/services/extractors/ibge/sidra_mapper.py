"""SIDRA Mapper Service

This service handles the mapping of natural language terms and concepts to
IBGE SIDRA API parameters and codes.
"""
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass


class SIDRAParameter:
    """Represents a SIDRA API parameter with its possible values."""
    code: str
    name: str
    description: str
    values: Dict[str, str]  # code: description


    def get_matching_codes(self, terms: List[str]) -> List[str]:
        """Find parameter values that match the given terms."""
        matches = []
        for code, desc in self.values.items():
            desc_lower = desc.lower()
            if any(term.lower() in desc_lower for term in terms):
                matches.append(code)
        return matches


class SIDRAMapper:
    """Maps natural language terms to SIDRA API parameters and codes."""


    def __init__(self):
        # Initialize with common SIDRA parameters
        self.parameters = self._initialize_parameters()

        # Term to parameter mapping (customizable)
        self.term_to_parameter = {
            # Demographics
            'idade': '200',
            'faixa etária': '200',
            'gênero': '143',
            'sexo': '143',
            'escolaridade': '276',
            'instrução': '276',
            'raça': '93',
            'cor': '93',
            'estado civil': '200',
            'região': '1',
            'uf': '1',
            'município': '1',

            # Economic
            'renda': '6793',
            'salário': '6793',
            'ocupação': '6793',
            'emprego': '6793',
            'desemprego': '6793',
            'setor': '6793',
            'atividade': '6793',

            # Consumption
            'consumo': '11046',
            'gasto': '11046',
            'despesa': '11046',
            'compra': '11046',
            'venda': '11046',
            'comércio': '11046',

            # Categories
            'alimentação': '11046',
            'alimento': '11046',
            'moradia': '11046',
            'habitação': '11046',
            'transporte': '11046',
            'saúde': '11046',
            'educação': '11046',
            'lazer': '11046',
            'cultura': '11046',
            'vestuário': '11046',
            'roupa': '11046',
            'eletrodoméstico': '11046',
            'eletrônico': '11046',
            'tecnologia': '11046',
        }

        # Table mappings
        self.table_mappings = {
            # PNAD Contínua
            '6401': {
                'name': 'PNAD Contínua - Rendimento e outras características',
                'description': 'Dados sobre rendimento, trabalho, desemprego e outras características da população',
                'parameters': ['200', '6793', '143', '276', '93']
            },

            # POF - Pesquisa de Orçamentos Familiares
            '7482': {
                'name': 'POF - Despesas',
                'description': 'Dados sobre despesas das famílias brasileiras',
                'parameters': ['11046', '11047']
            },

            # POF - Bens Duráveis
            '7493': {
                'name': 'POF - Bens Duráveis',
                'description': 'Posse de bens duráveis pelas famílias',
                'parameters': ['11046']
            },

            # PNAD Contínua - Outros
            '4093': {
                'name': 'PNAD Contínua - Outros trabalhos',
                'description': 'Dados sobre outros trabalhos e rendimentos',
                'parameters': ['6793']
            }
        }


    def _initialize_parameters(self) -> Dict[str, SIDRAParameter]:
        """Initialize SIDRA parameters with their possible values."""
        return {
            # Age group
            '200': SIDRAParameter(
                code='200',
                name='Faixa etária',
                description='Faixas de idade da população',
                values={
                    '1933': '14 a 17 anos',
                    '1934': '18 a 24 anos',
                    '1935': '25 a 39 anos',
                    '1936': '40 a 59 anos',
                    '1937': '60 anos ou mais'
                }
            ),

            # Gender
            '143': SIDRAParameter(
                code='143',
                name='Sexo',
                description='Sexo da pessoa',
                values={
                    'M': 'Homens',
                    'F': 'Mulheres'
                }
            ),

            # Education level
            '276': SIDRAParameter(
                code='276',
                name='Nível de instrução',
                description='Nível de instrução da pessoa',
                values={
                    '29576': 'Sem instrução e fundamental incompleto',
                    '29577': 'Fundamental completo e médio incompleto',
                    '29578': 'Médio completo e superior incompleto',
                    '29579': 'Superior completo',
                    '29580': 'Pós-graduação'
                }
            ),

            # Race/Color
            '93': SIDRAParameter(
                code='93',
                name='Cor ou raça',
                description='Cor ou raça da pessoa',
                values={
                    '1': 'Branca',
                    '2': 'Preta',
                    '3': 'Amarela',
                    '4': 'Parda',
                    '5': 'Indígena',
                    '9': 'Ignorado'
                }
            ),

            # Income
            '6793': SIDRAParameter(
                code='6793',
                name='Rendimento',
                description='Faixas de rendimento',
                values={
                    '0': 'Sem rendimento',
                    '1': 'Até 1 salário mínimo',
                    '2': 'Mais de 1 a 2 salários mínimos',
                    '3': 'Mais de 2 a 3 salários mínimos',
                    '4': 'Mais de 3 a 5 salários mínimos',
                    '5': 'Mais de 5 a 10 salários mínimos',
                    '6': 'Mais de 10 a 20 salários mínimos',
                    '7': 'Mais de 20 salários mínimos',
                    '8': 'Sem declaração'
                }
            ),

            # Expense categories (POF)
            '11046': SIDRAParameter(
                code='11046',
                name='Categorias de despesa',
                description='Categorias de despesa da POF',
                values={
                    '114023': 'Habitação',
                    '114024': 'Alimentação',
                    '114025': 'Saúde',
                    '114026': 'Bens duráveis',
                    '114027': 'Recreação e cultura',
                    '114028': 'Esportes',
                    '114029': 'Educação',
                    '114030': 'Vestuário',
                    '114031': 'Transporte',
                    '114032': 'Comunicação',
                    '114033': 'Despesas diversas',
                    '114034': 'Impostos',
                    '114035': 'Poupança e investimentos',
                    '114036': 'Doações',
                    '114037': 'Outras despesas'
                }
            )
        }


    def map_terms_to_sidra_parameters(
        self, 
        terms: List[str],
        preferred_table: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Map natural language terms to SIDRA API parameters.

        Args:
            terms: List of terms to map
            preferred_table: Optional preferred SIDRA table code

        Returns:
            Dictionary with mapped parameters
        """
        logger.info(f"Mapping terms to SIDRA parameters: {terms}")

        # Normalize terms
        normalized_terms = [t.lower() for t in terms]

        # Find matching parameters
        matched_parameters = defaultdict(list)

        # First, try direct term matching
        for term in normalized_terms:
            if term in self.term_to_parameter:
                param_code = self.term_to_parameter[term]
                matched_parameters[param_code].append(term)

        # If no direct matches, try fuzzy matching with parameter names and descriptions
        if not matched_parameters:
            for param_code, param in self.parameters.items():
                param_terms = [param.name.lower()] + param.description.lower().split()
                if any(term in ' '.join(param_terms) for term in normalized_terms):
                    matched_parameters[param_code].extend(normalized_terms)

        # If we have a preferred table, filter parameters to those available in that table
        if preferred_table and preferred_table in self.table_mappings:
            available_params = self.table_mappings[preferred_table]['parameters']
            matched_parameters = {
                k: v for k, v in matched_parameters.items() 
                if k in available_params
            }

        # If still no matches, use default parameters
        if not matched_parameters:
            logger.warning("No specific parameters matched, using defaults")
            matched_parameters = {
                '200': ['idade', 'faixa etária'],  # Age
                '6793': ['renda', 'salário'],     # Income
                '11046': ['consumo', 'gasto']      # Expenses
            }

        # Build the result
        result = {
            'tabela': preferred_table or '6401',  # Default to PNAD Contínua
            'variaveis': [],
            'classificacoes': {},
            'localidades': ['BR'],  # Default to Brazil
            'periodo': 'last',      # Default to most recent period
            'matched_terms': {}
        }

        # Add matched parameters to the result
        for param_code, matched_terms in matched_parameters.items():
            if param_code in self.parameters:
                param = self.parameters[param_code]

                # Add to variables or classifications based on parameter type
                if param_code in ['6793', '2979', '2980']:  # Variables
                    result['variaveis'].append(param_code)
                else:  # Classifications
                    result['classificacoes'][param_code] = 'all'  # Get all values initially

                # Record which terms matched this parameter
                result['matched_terms'][param_code] = {
                    'name': param.name,
                    'description': param.description,
                    'matched_terms': matched_terms
                }

        # If we have specific values for some parameters, add them
        self._refine_parameter_values(result, normalized_terms)

        logger.info(f"Mapped to SIDRA parameters: {result}")
        return result


    def _refine_parameter_values(self, result: Dict[str, Any], terms: List[str]) -> None:
        """Refine parameter values based on the input terms."""
        for param_code in list(result['classificacoes'].keys()):
            if param_code in self.parameters:
                param = self.parameters[param_code]
                matched_values = param.get_matching_codes(terms)

                if matched_values:
                    # If we found specific matches, use those
                    result['classificacoes'][param_code] = ','.join(matched_values)
                else:
                    # Otherwise, keep 'all' to get all values
                    pass


    def get_table_info(self, table_code: str) -> Dict[str, Any]:
        """Get information about a SIDRA table."""
        return self.table_mappings.get(table_code, {})


    def get_parameter_info(self, param_code: str) -> Dict[str, Any]:
        """Get information about a SIDRA parameter."""
        if param_code in self.parameters:
            param = self.parameters[param_code]
            return {
                'code': param.code,
                'name': param.name,
                'description': param.description,
                'values': param.values
            }
        return {}


    def suggest_tables(self, terms: List[str]) -> List[Dict[str, Any]]:
        """Suggest relevant SIDRA tables based on input terms."""
        scores = []

        for table_code, table_info in self.table_mappings.items():
            score = 0
            table_terms = (
                table_info['name'].lower().split() + 
                table_info['description'].lower().split()
            )

            for term in terms:
                term = term.lower()
                score += sum(1 for t in table_terms if term in t)

            if score > 0:
                scores.append({
                    'table_code': table_code,
                    'name': table_info['name'],
                    'description': table_info['description'],
                    'score': score
                })

        # Sort by score (descending)
        return sorted(scores, key=lambda x: x['score'], reverse=True)
