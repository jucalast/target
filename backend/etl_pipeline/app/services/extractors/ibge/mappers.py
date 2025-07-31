"""
Módulo de mapeamento de conceitos para códigos SIDRA do IBGE.

Este módulo é responsável por traduzir conceitos de negócio (como 'jovens_adultos', 
'consumo_cultural') e nomes de localidades em códigos específicos da API SIDRA do IBGE, 
permitindo a construção de consultas de forma mais intuitiva.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from unidecode import unidecode

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# --- Estruturas de Dados e Constantes ---


class Location(TypedDict):
    """
    Representa uma localização com seu código e nível territorial no padrão IBGE.
    """
    code: str
    level: str
    name: str

# Níveis Territoriais do IBGE e seus códigos correspondentes
# Fonte: Documentação da API SIDRA
TERRITORIAL_LEVELS = {
    "1": "Brasil",
    "2": "Grande Região",
    "3": "Unidade da Federação",
    "6": "Município",
    "7": "Região Metropolitana",
    "8": "Mesorregião Geográfica",
    "9": "Microrregião Geográfica",
}

# Mapeamento normalizado de localidades comuns para seus códigos e níveis
# A chave é o nome normalizado (minúsculo, sem acentos ou caracteres especiais)
COMMON_LOCATIONS: Dict[str, Location] = {
    # Nível Nacional
    'brasil': {'code': '1', 'level': '1', 'name': 'Brasil'},
    'brazil': {'code': '1', 'level': '1', 'name': 'Brasil'},

    # Grandes Regiões
    'norte': {'code': '1', 'level': '2', 'name': 'Região Norte'},
    'regiao norte': {'code': '1', 'level': '2', 'name': 'Região Norte'},
    'nordeste': {'code': '2', 'level': '2', 'name': 'Região Nordeste'},
    'regiao nordeste': {'code': '2', 'level': '2', 'name': 'Região Nordeste'},
    'sudeste': {'code': '3', 'level': '2', 'name': 'Região Sudeste'},
    'regiao sudeste': {'code': '3', 'level': '2', 'name': 'Região Sudeste'},
    'sul': {'code': '4', 'level': '2', 'name': 'Região Sul'},
    'regiao sul': {'code': '4', 'level': '2', 'name': 'Região Sul'},
    'centro oeste': {'code': '5', 'level': '2', 'name': 'Região Centro-Oeste'},
    'centro-oeste': {'code': '5', 'level': '2', 'name': 'Região Centro-Oeste'},

    # Unidades da Federação (Exemplos)
    'sao paulo': {'code': '35', 'level': '3', 'name': 'São Paulo'},
    'sp': {'code': '35', 'level': '3', 'name': 'São Paulo'},
    'rio de janeiro': {'code': '33', 'level': '3', 'name': 'Rio de Janeiro'},
    'rj': {'code': '33', 'level': '3', 'name': 'Rio de Janeiro'},
    'minas gerais': {'code': '31', 'level': '3', 'name': 'Minas Gerais'},
    'mg': {'code': '31', 'level': '3', 'name': 'Minas Gerais'},
    'bahia': {'code': '29', 'level': '3', 'name': 'Bahia'},
    'ba': {'code': '29', 'level': '3', 'name': 'Bahia'},

    # Municípios (Capitais - Exemplos)
    'sao paulo capital': {'code': '3550308', 'level': '6', 'name': 'São Paulo (Capital)'},
    'sao paulo sp': {'code': '3550308', 'level': '6', 'name': 'São Paulo (Capital)'},
    'rio de janeiro capital': {'code': '3304557', 'level': '6', 'name': 'Rio de Janeiro (Capital)'},
    'rio de janeiro rj': {'code': '3304557', 'level': '6', 'name': 'Rio de Janeiro (Capital)'},
    'belo horizonte': {'code': '3106200', 'level': '6', 'name': 'Belo Horizonte'},
    'bh': {'code': '3106200', 'level': '6', 'name': 'Belo Horizonte'},
    'salvador': {'code': '2927408', 'level': '6', 'name': 'Salvador'},
}

# Mapeamento de siglas de UF para códigos IBGE
UF_IBGE_CODES = {
    'AC': '12', 'AL': '27', 'AP': '16', 'AM': '13', 'BA': '29', 'CE': '23',
    'DF': '53', 'ES': '32', 'GO': '52', 'MA': '21', 'MT': '51', 'MS': '50',
    'MG': '31', 'PA': '15', 'PB': '25', 'PR': '41', 'PE': '26', 'PI': '22',
    'RJ': '33', 'RN': '24', 'RS': '43', 'RO': '11', 'RR': '14', 'SC': '42',
    'SP': '35', 'SE': '28', 'TO': '17'
}


class SIDRAMapper:
    """
    Mapeia conceitos de negócio e localidades para códigos da API SIDRA do IBGE.

    Esta classe facilita a consulta à API SIDRA ao permitir o uso de termos
    comuns (ex: 'sudeste', 'população jovem') em vez de códigos numéricos.
    """


    def __init__(self, mapping_file: Optional[str] = None):
        """
        Inicializa o mapeador com os dados de conceitos e outras personalizações.

        Args:
            mapping_file: Caminho para o arquivo JSON de mapeamento. Se não for 
                          fornecido, tenta localizar o arquivo em:
                          1. data/ibge/sidra_mappings.json (relativo ao diretório do projeto)
                          2. app/data/ibge/sidra_mappings.json (relativo ao diretório do projeto)
        """
        if mapping_file is None:
            # Tenta encontrar o arquivo em locais padrão
            base_dir = Path(__file__).parent.parent.parent.parent  # Volta para a raiz do projeto
            possible_paths = [
                base_dir / 'data' / 'ibge' / 'mappings' / 'sidra_mappings.json',  # Caminho correto
                base_dir / 'data' / 'ibge' / 'sidra_mappings.json',  # Mantendo para compatibilidade
                base_dir / 'app' / 'data' / 'ibge' / 'mappings' / 'sidra_mappings.json',
                base_dir / 'app' / 'services' / 'ibge' / 'data' / 'sidra_mappings.json'
            ]

            for path in possible_paths:
                if path.exists():
                    mapping_file = str(path)
                    logger.info(f"Arquivo de mapeamento encontrado em: {mapping_file}")
                    break
            else:
                # Nenhum arquivo encontrado, usa um mapeamento vazio
                logger.warning("Nenhum arquivo de mapeamento encontrado. Procurou em: " + 
                             ", ".join(str(p) for p in possible_paths))
                self.mappings = {"tables": {}, "variables": {}, "classifications": {}, "concepts": {}}
                return

        self.mapping_file = Path(mapping_file)
        self.mappings = self._load_mappings()


    def _load_mappings(self) -> Dict[str, Any]:
        """Carrega os mapeamentos do arquivo JSON."""
        try:
            if not hasattr(self, 'mapping_file'):
                logger.warning("Nenhum arquivo de mapeamento definido. Usando mapeamento vazio.")
                return {"tables": {}, "variables": {}, "classifications": {}, "concepts": {}}

            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                logger.info(f"Carregando mapeamentos de: {self.mapping_file}")
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Arquivo de mapeamento não encontrado: {self.mapping_file}")
            return {"tables": {}, "variables": {}, "classifications": {}, "concepts": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar o arquivo de mapeamento {self.mapping_file}: {e}")
            return {"tables": {}, "variables": {}, "classifications": {}, "concepts": {}}
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar mapeamentos: {e}")
            return {"tables": {}, "variables": {}, "classifications": {}, "concepts": {}}


    def _normalize_text(self, text: str) -> str:
        """
        Normaliza uma string para facilitar a busca e a correspondência.
        Converte para minúsculas, remove acentos e caracteres não alfanuméricos.

        Args:
            text: A string de entrada a ser normalizada.

        Returns:
            A string normalizada.
        """
        if not text:
            return ''

        # Converte para minúsculas e remove acentos
        normalized = unidecode(text.lower())

        # Mantém letras, números, espaços, hífen e sublinhados. Remove outros caracteres.
        normalized = re.sub(r'[^a-z0-9\s_-]', '', normalized)

        # Substitui múltiplos espaços por um único espaço
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized


    def get_location_info(self, location_name: str) -> Optional[Location]:
        """
        Obtém informações detalhadas de uma localização, incluindo código, nível e nome.

        Args:
            location_name: O nome da localidade (ex: 'São Paulo', 'Região Sul', 'bh').

        Returns:
            Um dicionário do tipo `Location` se a localização for encontrada, 
            caso contrário, None.
        """
        if not location_name:
            return None

        normalized = self._normalize_text(location_name)

        # 1. Busca no mapeamento de localidades comuns
        if normalized in COMMON_LOCATIONS:
            return COMMON_LOCATIONS[normalized]

        # 2. Verifica se é uma sigla de UF
        if len(normalized) == 2 and normalized.upper() in UF_IBGE_CODES:
            code = UF_IBGE_CODES[normalized.upper()]
            return {'code': code, 'level': '3', 'name': location_name}

        # 3. Verifica se é um código numérico direto
        if normalized.isdigit():
            level = str(len(normalized)) if len(normalized) in [1, 2] else '6' # Heurística simples
            if len(normalized) == 1: level = '2' # Grande Região
            if len(normalized) == 2: level = '3' # UF
            if len(normalized) == 7: level = '6' # Município

            return {'code': normalized, 'level': level, 'name': location_name}

        logger.warning(f"Localização não encontrada para o termo: '{location_name}'")
        return None


    def get_concept_mapping(self, concept: str) -> Dict[str, Any]:
        """
        Obtém o mapeamento SIDRA completo para um conceito de negócio.

        Args:
            concept: O nome do conceito (ex: 'jovens_adultos', 'pib_per_capita').

        Returns:
            Um dicionário contendo os parâmetros da API SIDRA para o conceito.

        Raises:
            ValueError: Se o conceito não for encontrado nos mapeamentos.
        """
        normalized_concept = self._normalize_text(concept)
        mapping = self.mappings.get('concepts', {}).get(normalized_concept)

        if not mapping:
            raise ValueError(f"Conceito '{concept}' não encontrado nos mapeamentos.")
        return mapping


    def get_variable_info(self, table_code: str, variable_name: str) -> Dict[str, Any]:
        """
        Obtém os detalhes de uma variável específica de uma tabela.

        Args:
            table_code: O código da tabela SIDRA.
            variable_name: O nome ou alias da variável.

        Returns:
            Um dicionário com os dados da variável.

        Raises:
            ValueError: Se a variável não for encontrada para a tabela especificada.
        """
        table_key = str(table_code)
        normalized_var = self._normalize_text(variable_name)

        variables = self.mappings.get('variables', [])
        for var in variables:
            if var.get('table') == table_key and self._normalize_text(var.get('name')) == normalized_var:
                return var

        raise ValueError(f"Variável '{variable_name}' não encontrada na tabela '{table_code}'.")


    def get_table_info(self, table_code: str) -> Dict[str, Any]:
        """
        Obtém metadados sobre uma tabela SIDRA.

        Args:
            table_code: O código da tabela SIDRA.

        Returns:
            Dicionário com os metadados da tabela.

        Raises:
            ValueError: Se a tabela não for encontrada nos mapeamentos.
        """
        table_key = str(table_code)
        tables = self.mappings.get('tables', [])
        for table in tables:
            if table.get('code') == table_key:
                return table

        raise ValueError(f"Tabela '{table_code}' não encontrada nos mapeamentos.")


    def list_available_concepts(self) -> List[str]:
        """
        Retorna uma lista com todos os nomes de conceitos disponíveis.

        Returns:
            Uma lista de strings com os nomes dos conceitos.
        """
        return list(self.mappings.get('concepts', {}).keys())


    def list_available_tables(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista de todas as tabelas disponíveis com seus metadados.

        Returns:
            Uma lista de dicionários, cada um representando uma tabela.
        """
        return self.mappings.get('tables', [])
