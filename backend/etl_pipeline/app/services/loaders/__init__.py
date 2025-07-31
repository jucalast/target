"""
Módulo de carregadores de dados para o pipeline ETL.

Este pacote contém implementações de carregadores para diferentes tipos
de dados que serão processados pelo pipeline ETL.
"""
from .news_loader import NewsLoader, NewsLoaderError

__all__ = [
    'NewsLoader',
    'NewsLoaderError',
]
