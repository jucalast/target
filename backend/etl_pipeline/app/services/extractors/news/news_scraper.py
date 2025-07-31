"""
Serviço de Scraping de Notícias Setoriais

Este módulo implementa um serviço para coletar notícias de fontes abertas e confiáveis,
respeitando os termos de serviço e políticas de acesso de cada fonte.
"""
import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from fake_useragent import UserAgent

from shared.schemas.news import NewsArticle, NewsSource
from shared.utils.config import NEWS_API_CONFIG

logger = logging.getLogger(__name__)


class NewsScraperError(Exception):
    """Exceção personalizada para erros no serviço de notícias."""
    pass


class NewsScraper:
    """
    Serviço para coleta de notícias de fontes abertas.

    Este serviço coleta notícias de fontes confiáveis, respeitando:
    - Políticas de acesso e termos de serviço
    - Limites de taxa de requisições
    - Direitos autorais e de propriedade intelectual
    """

    # Lista de domínios permitidos para scraping
    ALLOWED_DOMAINS = [
        'agenciabrasil.ebc.com.br',  # Agência Brasil (pública)
        'agenciagov.ebc.com.br',     # Agência Gov
        'www.ibge.gov.br',           # IBGE
        'agenciadenoticias.ibge.gov.br',  # Agência de Notícias do IBGE
        'www.gov.br/agenciabrasil',  # Portal do Governo
        'agenciabrasil.ebc.com.br/radioagencia',  # Rádio Agência Brasil
    ]

    # Padrões de URL para identificar notícias
    NEWS_URL_PATTERNS = [
        r'.*/noticias/.*',
        r'.*/ultimas-noticias/.*',
        r'.*/agencia-.+',
        r'.*/[0-9]{4}/[0-9]{2}/[0-9]{2}/.*',  # URLs com data
    ]

    # Seletores CSS para extrair conteúdo de diferentes sites
    SITE_SELECTORS = {
        'agenciabrasil.ebc.com.br': {
            'title': 'h1.documentFirstHeading',
            'content': 'div.documentDescription, div.entry-content',
            'date': 'span.documentPublished > span.value',
            'author': 'span.documentAuthor > a',
            'category': 'div.documentByLine > span.documentCategory',
        },
        'www.ibge.gov.br': {
            'title': 'h1.documentFirstHeading',
            'content': 'div.documentDescription, div.entry-content',
            'date': 'span.documentPublished > span.value',
            'author': 'span.documentAuthor > a',
        },
        'default': {
            'title': 'h1, h2.article-title',
            'content': 'article, div.article-content, div.entry-content',
            'date': 'time, span.date, div.date',
            'author': 'span.author, a.author, div.author',
        }
    }


    def __init__(self, user_agent: str = None, request_timeout: int = 10):
        """
        Inicializa o serviço de scraping de notícias.

        Args:
            user_agent: User-Agent a ser usado nas requisições
            request_timeout: Timeout em segundos para as requisições HTTP
        """
        self.session = requests.Session()
        self.user_agent = user_agent or UserAgent().chrome
        self.request_timeout = request_timeout
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        })

        # Configuração de delay entre requisições (em segundos)
        self.request_delay = 2.0
        self.last_request_time = 0


    def scrape_news(self, query: str, max_results: int = 10, days_back: int = 30) -> List[NewsArticle]:
        """
        Coleta notícias relacionadas a uma consulta.

        Args:
            query: Termos de busca
            max_results: Número máximo de notícias a retornar
            days_back: Número máximo de dias para trás a partir de hoje

        Returns:
            Lista de notícias encontradas

        Raises:
            NewsScraperError: Em caso de falha na coleta
        """
        logger.info(f"Iniciando busca por notícias: '{query}' (últimos {days_back} dias)")

        try:
            # Lista para armazenar as notícias encontradas
            articles = []

            # Data mínima para as notícias
            min_date = datetime.now() - timedelta(days=days_back)

            # Para cada domínio permitido, busca notícias
            for domain in self.ALLOWED_DOMAINS:
                if len(articles) >= max_results:
                    break

                try:
                    # Obtém a URL base do domínio
                    base_url = f"https://{domain}"

                    # Busca por notícias no domínio
                    domain_articles = self._search_domain_news(
                        base_url=base_url,
                        query=query,
                        max_results=max_results - len(articles),
                        min_date=min_date
                    )

                    articles.extend(domain_articles)

                except Exception as e:
                    logger.error(f"Erro ao buscar notícias em {domain}: {str(e)}", exc_info=True)

            # Ordena as notícias por data (mais recentes primeiro)
            articles.sort(key=lambda x: x.published_at, reverse=True)

            # Limita ao número máximo de resultados
            return articles[:max_results]

        except Exception as e:
            logger.error(f"Erro ao buscar notícias: {str(e)}", exc_info=True)
            raise NewsScraperError(f"Falha ao buscar notícias: {str(e)}")


    def _search_domain_news(self, base_url: str, query: str, max_results: int, 
                          min_date: datetime) -> List[NewsArticle]:
        """
        Busca notícias em um domínio específico.

        Args:
            base_url: URL base do domínio
            query: Termos de busca
            max_results: Número máximo de notícias a retornar
            min_date: Data mínima para as notícias

        Returns:
            Lista de notícias encontradas no domínio
        """
        articles = []

        try:
            # Obtém a página inicial do domínio
            soup = self._make_request(base_url)
            if not soup:
                return []

            # Encontra links para páginas de notícias
            news_links = self._find_news_links(soup, base_url)

            # Para cada link de notícia, extrai o conteúdo
            for link in news_links:
                if len(articles) >= max_results:
                    break

                try:
                    # Verifica se o link parece ser uma notícia
                    if not self._is_news_url(link):
                        continue

                    # Extrai o conteúdo da notícia
                    article = self._extract_article(link, query)

                    # Verifica se a notícia é recente o suficiente
                    if article and article.published_at >= min_date:
                        articles.append(article)

                except Exception as e:
                    logger.warning(f"Erro ao processar notícia {link}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar notícias em {base_url}: {str(e)}", exc_info=True)

        return articles


    def _find_news_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Encontra links para notícias em uma página.

        Args:
            soup: Objeto BeautifulSoup da página
            base_url: URL base para resolver URLs relativas

        Returns:
            Lista de URLs de notícias encontradas
        """
        links = set()

        # Procura por links que correspondam aos padrões de notícias
        for a in soup.find_all('a', href=True):
            href = a['href']

            # Ignora âncoras e links vazios
            if not href or href.startswith('#'):
                continue

            # Resolve a URL relativa
            full_url = urljoin(base_url, href)

            # Verifica se o domínio está na lista de permitidos
            if not self._is_allowed_domain(full_url):
                continue

            # Verifica se o link parece ser uma notícia
            if self._is_news_url(full_url):
                links.add(full_url)

        return list(links)


    def _extract_article(self, url: str, query: str) -> Optional[NewsArticle]:
        """
        Extrai o conteúdo de uma notícia a partir da URL.

        Args:
            url: URL da notícia
            query: Termos de busca que levaram a esta notícia

        Returns:
            Objeto NewsArticle com o conteúdo extraído, ou None em caso de erro
        """
        try:
            # Faz a requisição à página da notícia
            soup = self._make_request(url)
            if not soup:
                return None

            # Obtém o domínio para selecionar os seletores apropriados
            domain = urlparse(url).netloc
            selectors = self.SITE_SELECTORS.get(domain, self.SITE_SELECTORS['default'])

            # Extrai o título
            title_elem = soup.select_one(selectors['title'])
            title = title_elem.get_text().strip() if title_elem else "Sem título"

            # Extrai o conteúdo
            content = ""
            content_elems = soup.select(selectors['content'])
            for elem in content_elems:
                # Remove elementos indesejados (comentários, scripts, etc.)
                for tag in elem.select('script, style, iframe, nav, footer, aside'):
                    tag.decompose()
                content += elem.get_text('\n', strip=True) + '\n\n'

            content = content.strip()
            if not content:
                return None

            # Extrai a data de publicação
            published_at = datetime.now()  # Valor padrão
            date_elem = soup.select_one(selectors['date'])
            if date_elem:
                try:
                    date_text = date_elem.get('datetime') or date_elem.get_text()
                    published_at = date_parser.parse(date_text, dayfirst=True)
                except (ValueError, TypeError):
                    pass

            # Extrai o autor, se disponível
            author = None
            author_elem = soup.select_one(selectors.get('author', ''))
            if author_elem:
                author = author_elem.get_text().strip()

            # Extrai a categoria, se disponível
            category = None
            category_elem = soup.select_one(selectors.get('category', ''))
            if category_elem:
                category = category_elem.get_text().strip()

            # Cria o objeto NewsArticle
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                source=NewsSource(
                    name=domain,
                    domain=domain,
                    url=f"https://{domain}"
                ),
                published_at=published_at,
                author=author,
                category=category,
                search_query=query,
                language='pt-BR',
                metadata={
                    'extracted_at': datetime.utcnow().isoformat(),
                    'content_length': len(content),
                    'word_count': len(content.split())
                }
            )

        except Exception as e:
            logger.error(f"Erro ao extrair notícia de {url}: {str(e)}", exc_info=True)
            return None


    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Faz uma requisição HTTP e retorna o conteúdo parseado.

        Args:
            url: URL para fazer a requisição

        Returns:
            Objeto BeautifulSoup com o conteúdo parseado, ou None em caso de erro
        """
        # Respeita o delay entre requisições
        self._respect_delay()

        try:
            response = self.session.get(
                url,
                timeout=self.request_timeout,
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                },
                allow_redirects=True
            )

            response.raise_for_status()

            # Atualiza o tempo da última requisição
            self.last_request_time = time.time()

            # Verifica o tipo de conteúdo
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Conteúdo não HTML em {url}: {content_type}")
                return None

            # Parseia o HTML
            return BeautifulSoup(response.text, 'html.parser')

        except requests.exceptions.RequestException as e:
            logger.warning(f"Erro na requisição para {url}: {str(e)}")
            return None


    def _respect_delay(self) -> None:
        """Aguarda o tempo necessário entre requisições."""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.request_delay:
                time.sleep(self.request_delay - elapsed)


    def _is_allowed_domain(self, url: str) -> bool:
        """Verifica se o domínio da URL está na lista de permitidos."""
        domain = urlparse(url).netloc.lower()
        return any(allowed in domain for allowed in self.ALLOWED_DOMAINS)


    def _is_news_url(self, url: str) -> bool:
        """Verifica se a URL parece ser de uma notícia."""
        # Verifica se a URL corresponde a algum padrão de notícia
        path = urlparse(url).path.lower()
        return any(re.match(pattern, path) for pattern in self.NEWS_URL_PATTERNS)


# Exemplo de uso
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    scraper = NewsScraper()
    articles = scraper.scrape_news("economia", max_results=5)

    for i, article in enumerate(articles, 1):
        print(f"\n--- Notícia {i} ---")
        print(f"Título: {article.title}")
        print(f"Fonte: {article.source.name}")
        print(f"Data: {article.published_at}")
        print(f"URL: {article.url}")
        print(f"Resumo: {article.content[:200]}...")
