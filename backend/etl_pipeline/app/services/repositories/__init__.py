"""
Módulo de repositórios para persistência de dados.

Este pacote contém implementações de repositórios para acesso a dados
do sistema, incluindo o repositório de notícias.
"""
from .news_repository import NewsRepository

__all__ = [
    'NewsRepository',
]
