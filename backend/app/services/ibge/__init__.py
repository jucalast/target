"""
Módulo de integração com a API do IBGE.

Este pacote contém os serviços necessários para acessar e processar dados
do IBGE, incluindo POF (Pesquisa de Orçamentos Familiares) e PNAD Contínua.
"""

from .sidra_connector import SIDRAClient, SIDRAService
from .mappers import SIDRAMapper

__all__ = ["SIDRAClient", "SIDRAService", "SIDRAMapper"]
