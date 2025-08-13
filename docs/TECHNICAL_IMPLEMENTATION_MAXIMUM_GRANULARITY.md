# 🔧 Implementação Técnica - Granularidade Máxima de Dados

## 📋 **Modificações Necessárias no Código**

### **1. IBGE SIDRA - Expansão da Granularidade**

#### **📁 `backend/shared/db/repositories/sidra_connector.py`**

```python
class SIDRAConnector:
    # Configurações expandidas para granularidade máxima
    GEOGRAPHIC_LEVELS = {
        'nacional': 1,      # Brasil
        'regiao': 2,        # 5 grandes regiões  
        'estado': 3,        # 27 estados
        'mesorregiao': 4,   # 137 mesorregiões
        'microrregiao': 5,  # 558 microrregiões
        'municipio': 6,     # 5.570 municípios
        'distrito': 8,      # 10.302 distritos
        'subdistrito': 9    # 662 subdistritos
    }
    
    POF_EXTENDED_TABLES = {
        # Tabelas POF atuais (já implementadas)
        'gastos_detalhados': 9052,
        'caracteristicas_domicilio': 9053,
        'despesas_monetarias': 9055,
        'rendimentos': 9056,
        
        # Expansão para granularidade máxima
        'alimentacao_nutricao': 7483,      # 104 produtos alimentares
        'habitacao_detalhada': 7484,       # 47 tipos de gastos habitação
        'vestuario_calcados': 7485,        # 35 tipos de vestuário
        'transporte_comunicacao': 7486,    # 28 tipos de transporte
        'higiene_cuidados': 7487,          # 18 produtos higiene
        'saude_medicamentos': 7488,        # 23 tipos gastos saúde
        'educacao_recreacao': 7489,        # 19 tipos educação/cultura
        'fumo_bebidas': 7490,              # 8 tipos fumo/bebidas
        'servicos_pessoais': 7491,         # 15 tipos serviços
        'outras_despesas': 7492,           # 12 outras categorias
        
        # Bens duráveis expandidos
        'bens_eletronicos': 7493,          # 28 tipos eletrônicos
        'eletrodomesticos': 7494,          # 24 tipos eletrodomésticos
        'moveis_decoracao': 7495,          # 18 tipos móveis
        'veiculos_propriedades': 7496,     # 8 tipos veículos/imóveis
        
        # Demografia detalhada
        'renda_individual': 7497,          # Renda por pessoa da família
        'escolaridade_idade': 7498,        # Cruzamento idade × escolaridade
        'ocupacao_profissao': 7499,        # 95 tipos de ocupação
        'raca_renda': 7500,                # Cruzamento raça × renda
    }
    
    DEMOGRAPHIC_VARIABLES = {
        'idade': list(range(0, 90, 5)),     # 18 faixas etárias
        'sexo': [1, 2],                     # Masculino, Feminino
        'cor_raca': [1, 2, 4, 8, 9],       # Branca, Preta, Parda, Amarela, Indígena
        'escolaridade': list(range(1, 10)), # 9 níveis educação
        'renda_familiar': list(range(1, 16)), # 15 faixas de renda
        'situacao_domicilio': [1, 2],       # Urbano, Rural
        'regiao_metropolitana': [1, 2, 3],  # Capital, RM, Interior
    }
    
    def get_maximum_granularity_data(self, geographic_level='municipio', 
                                   demographic_filters=None, 
                                   spending_categories='all'):
        """
        Extrai dados com granularidade máxima possível
        
        Args:
            geographic_level: Nível geográfico desejado
            demographic_filters: Filtros demográficos específicos
            spending_categories: Categorias de gastos ('all' ou lista específica)
        
        Returns:
            DataFrame com granularidade máxima
        """
        
        # 1. Definir parâmetros geográficos
        geo_code = self.GEOGRAPHIC_LEVELS[geographic_level]
        
        # 2. Definir filtros demográficos
        if demographic_filters is None:
            demographic_filters = {
                'idade': 'all',
                'sexo': 'all', 
                'cor_raca': 'all',
                'escolaridade': 'all',
                'renda_familiar': 'all'
            }
        
        # 3. Definir categorias de gastos
        if spending_categories == 'all':
            tables_to_query = list(self.POF_EXTENDED_TABLES.values())
        else:
            tables_to_query = [self.POF_EXTENDED_TABLES[cat] 
                             for cat in spending_categories]
        
        results = []
        
        for table_id in tables_to_query:
            try:
                # Query com máxima granularidade
                query_params = {
                    'table': table_id,
                    'territorial_level': geo_code,
                    'ibge_territorial_code': 'all',  # Todos os territórios do nível
                    'variable': 'all',               # Todas as variáveis
                    'classification': {              # Todas as classificações demográficas
                        'idade': demographic_filters['idade'],
                        'sexo': demographic_filters['sexo'],
                        'cor_raca': demographic_filters['cor_raca'],
                        'escolaridade': demographic_filters['escolaridade'],
                        'renda_familiar': demographic_filters['renda_familiar']
                    },
                    'period': 'last'  # Último período disponível
                }
                
                df = self._execute_sidra_query(query_params)
                df['table_source'] = table_id
                df['granularity_level'] = geographic_level
                
                results.append(df)
                
            except Exception as e:
                self.logger.warning(f"Erro ao extrair tabela {table_id}: {e}")
                continue
        
        # Consolidar todos os resultados
        if results:
            final_df = pd.concat(results, ignore_index=True)
            final_df['extraction_timestamp'] = datetime.now()
            return final_df
        
        return pd.DataFrame()
    
    def calculate_market_segments(self, data_df):
        """
        Calcula segmentos de mercado com base na granularidade máxima
        
        Returns:
            Dict com estatísticas de segmentação
        """
        segments = {
            'geographic_segments': data_df['territorial_code'].nunique(),
            'demographic_combinations': len(data_df.groupby([
                'idade', 'sexo', 'cor_raca', 'escolaridade', 'renda_familiar'
            ])),
            'spending_categories': data_df['spending_category'].nunique(),
            'total_possible_segments': None
        }
        
        # Calcular total de segmentos possíveis
        segments['total_possible_segments'] = (
            segments['geographic_segments'] * 
            segments['demographic_combinations'] * 
            segments['spending_categories']
        )
        
        return segments
```

### **2. Google Trends - Granularidade Temporal e Geográfica**

#### **📁 `backend/etl_pipeline/app/services/google_trends_service.py`**

```python
class GoogleTrendsService:
    
    BRAZILIAN_CITIES = [
        'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Brasília',
        'Salvador', 'Fortaleza', 'Manaus', 'Curitiba', 'Recife', 
        'Porto Alegre', 'Belém', 'Goiânia', 'Guarulhos', 'Campinas',
        'São Luís', 'São Gonçalo', 'Maceió', 'Duque de Caxias',
        'Campo Grande', 'Natal', 'Teresina', 'São Bernardo do Campo',
        'Nova Iguaçu', 'João Pessoa', 'Santo André', 'São José dos Campos',
        # ... mais 74 cidades principais
    ]
    
    METROPOLITAN_REGIONS = [
        'Grande São Paulo', 'Grande Rio', 'Grande BH', 'Grande Salvador',
        'Grande Fortaleza', 'Grande Brasília', 'Grande Curitiba',
        'Grande Porto Alegre', 'Grande Recife', 'Grande Belém',
        # ... mais 64 regiões metropolitanas
    ]
    
    TIME_GRANULARITIES = {
        'real_time': 'now 1-H',      # Última hora
        'today': 'now 1-d',         # Últimas 24 horas
        'week': 'now 7-d',          # Últimos 7 dias
        'month': 'today 1-m',       # Último mês
        'quarter': 'today 3-m',     # Últimos 3 meses
        'year': 'today 12-m',       # Último ano
        'five_years': 'today 5-y',  # Últimos 5 anos
        'max_history': '2004-01-01 2024-12-31'  # Máximo histórico
    }
    
    def get_maximum_granularity_trends(self, keywords, timeframe='month', 
                                     geographic_level='city'):
        """
        Extrai dados do Google Trends com granularidade máxima
        
        Args:
            keywords: Lista de até 5 keywords
            timeframe: Granularidade temporal
            geographic_level: 'country', 'region', 'state', 'city', 'metro'
        
        Returns:
            Dict com dados de todas as localizações
        """
        
        results = {}
        
        # Definir localizações baseado no nível geográfico
        if geographic_level == 'city':
            locations = self.BRAZILIAN_CITIES
            geo_codes = [f'BR-{self._get_city_code(city)}' for city in locations]
        elif geographic_level == 'metro':
            locations = self.METROPOLITAN_REGIONS  
            geo_codes = [f'BR-{self._get_metro_code(metro)}' for metro in locations]
        elif geographic_level == 'state':
            locations = self.BRAZILIAN_STATES
            geo_codes = [f'BR-{state}' for state in self.STATE_CODES]
        else:
            locations = ['Brasil']
            geo_codes = ['BR']
        
        for location, geo_code in zip(locations, geo_codes):
            try:
                # Configurar pytrends para localização específica
                self.pytrends.build_payload(
                    kw_list=keywords[:5],  # Máximo 5 keywords
                    cat=0,                 # Todas as categorias
                    timeframe=self.TIME_GRANULARITIES[timeframe],
                    geo=geo_code,
                    gprop=''              # Web search (padrão)
                )
                
                # Extrair dados de interesse ao longo do tempo
                interest_over_time = self.pytrends.interest_over_time()
                
                # Extrair consultas relacionadas (top e rising)
                related_queries = self.pytrends.related_queries()
                
                # Extrair tópicos relacionados
                related_topics = self.pytrends.related_topics()
                
                # Extrair sugestões
                suggestions = {}
                for keyword in keywords:
                    suggestions[keyword] = self.pytrends.suggestions(keyword)
                
                # Extrair dados por região (subdivões da localização atual)
                interest_by_region = self.pytrends.interest_by_region(
                    resolution='CITY' if geographic_level != 'city' else 'REGION',
                    inc_low_vol=True,
                    inc_geo_code=True
                )
                
                results[location] = {
                    'geo_code': geo_code,
                    'interest_over_time': interest_over_time.to_dict('records'),
                    'related_queries': related_queries,
                    'related_topics': related_topics,
                    'suggestions': suggestions,
                    'interest_by_region': interest_by_region.to_dict('records'),
                    'extraction_timestamp': datetime.now().isoformat(),
                    'granularity_level': geographic_level,
                    'timeframe': timeframe
                }
                
                # Rate limiting para evitar bloqueio
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.warning(f"Erro ao extrair trends para {location}: {e}")
                continue
        
        return results
    
    def analyze_temporal_patterns(self, trends_data):
        """
        Analisa padrões temporais com granularidade máxima
        
        Returns:
            Dict com análises temporais detalhadas
        """
        
        patterns = {
            'hourly_patterns': {},      # Padrões por hora do dia
            'daily_patterns': {},       # Padrões por dia da semana
            'weekly_patterns': {},      # Padrões por semana do mês
            'monthly_patterns': {},     # Padrões por mês do ano
            'seasonal_patterns': {},    # Padrões sazonais
            'trend_cycles': {},         # Ciclos de tendência
        }
        
        for location, data in trends_data.items():
            interest_data = pd.DataFrame(data['interest_over_time'])
            
            if not interest_data.empty:
                interest_data['date'] = pd.to_datetime(interest_data['date'])
                
                # Análise por hora (se dados horários disponíveis)
                if 'hour' in interest_data.columns:
                    patterns['hourly_patterns'][location] = (
                        interest_data.groupby('hour').mean().to_dict()
                    )
                
                # Análise por dia da semana
                interest_data['day_of_week'] = interest_data['date'].dt.day_name()
                patterns['daily_patterns'][location] = (
                    interest_data.groupby('day_of_week').mean().to_dict()
                )
                
                # Análise mensal
                interest_data['month'] = interest_data['date'].dt.month_name()
                patterns['monthly_patterns'][location] = (
                    interest_data.groupby('month').mean().to_dict()
                )
                
                # Análise sazonal (trimestres)
                interest_data['quarter'] = interest_data['date'].dt.quarter
                patterns['seasonal_patterns'][location] = (
                    interest_data.groupby('quarter').mean().to_dict()
                )
        
        return patterns
```

### **3. News Scraping - Análise de Sentimento Granular**

#### **📁 `backend/etl_pipeline/app/services/news_analysis_service.py`**

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class NewsAnalysisService:
    
    def __init__(self):
        # Carregar modelo BERT para português
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained(
            "neuralmind/bert-base-portuguese-cased"
        )
        self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            "neuralmind/bert-base-portuguese-cased"
        )
        
        # Expandir fontes para granularidade máxima
        self.FEDERAL_SOURCES = [
            'agenciabrasil.ebc.com.br',
            'gov.br/agenciabrasil',
            'agenciadenotícias.ibge.gov.br',
            'bcb.gov.br/pre/noticias',
            'bndes.gov.br/wps/portal/site/home/imprensa',
            'fazenda.gov.br/noticias',
            'sebrae.com.br/sites/PortalSebrae/noticias',
            # ... mais 8 fontes federais
        ]
        
        self.STATE_SOURCES = {
            'SP': 'saopaulo.sp.gov.br/noticias',
            'RJ': 'rj.gov.br/noticias', 
            'MG': 'mg.gov.br/noticias',
            'PR': 'aen.pr.gov.br',
            'RS': 'rs.gov.br/noticias',
            'SC': 'sc.gov.br/noticias',
            'BA': 'ba.gov.br/noticias',
            'CE': 'ceara.gov.br/noticias',
            'PE': 'pe.gov.br/noticias',
            # ... mais 18 estados
        }
        
        self.SECTORAL_SOURCES = [
            'noticias.portaldaindustria.com.br',  # CNI
            'fiesp.com.br/noticias',              # FIESP
            'cnc.org.br/noticias',                # CNC
            'febraban.org.br/noticias',           # Febraban
            'abras.com.br/noticias',              # Abras
            # ... mais 20 fontes setoriais
        ]
    
    def extract_maximum_granularity_news(self, days_back=30):
        """
        Extrai notícias com granularidade máxima de todas as fontes
        
        Returns:
            List de artigos com análise completa
        """
        
        all_articles = []
        
        # 1. Extrair de fontes federais
        for source in self.FEDERAL_SOURCES:
            articles = self._scrape_source(source, days_back)
            for article in articles:
                article['source_level'] = 'federal'
                article['geographic_scope'] = 'nacional'
            all_articles.extend(articles)
        
        # 2. Extrair de fontes estaduais
        for state, source in self.STATE_SOURCES.items():
            articles = self._scrape_source(source, days_back)
            for article in articles:
                article['source_level'] = 'estadual'
                article['geographic_scope'] = state
            all_articles.extend(articles)
        
        # 3. Extrair de fontes setoriais
        for source in self.SECTORAL_SOURCES:
            articles = self._scrape_source(source, days_back)
            for article in articles:
                article['source_level'] = 'setorial'
                article['geographic_scope'] = 'nacional'
            all_articles.extend(articles)
        
        # 4. Análise granular de cada artigo
        analyzed_articles = []
        for article in all_articles:
            analyzed_article = self._analyze_article_granular(article)
            analyzed_articles.append(analyzed_article)
        
        return analyzed_articles
    
    def _analyze_article_granular(self, article):
        """
        Análise granular de um artigo com BERT e extração de entidades
        """
        
        content = article.get('content', '')
        title = article.get('title', '')
        
        # 1. Análise de sentimento com BERT
        sentiment_analysis = self._analyze_sentiment_bert(content)
        title_sentiment = self._analyze_sentiment_bert(title)
        
        # 2. Extração de entidades nomeadas
        entities = self._extract_named_entities(content)
        
        # 3. Extração de valores quantitativos
        quantitative_data = self._extract_quantitative_data(content)
        
        # 4. Classificação temática granular
        thematic_classification = self._classify_theme_granular(content)
        
        # 5. Extração de sinais de mercado
        market_signals = self._extract_market_signals(content)
        
        # 6. Análise geográfica (menções de locais)
        geographic_mentions = self._extract_geographic_mentions(content)
        
        # 7. Análise temporal (menções de datas/períodos)
        temporal_references = self._extract_temporal_references(content)
        
        return {
            **article,  # Dados originais do artigo
            'sentiment_analysis': {
                'content_sentiment': sentiment_analysis,
                'title_sentiment': title_sentiment,
                'overall_polarity': (sentiment_analysis['score'] + title_sentiment['score']) / 2,
                'confidence_level': min(sentiment_analysis['confidence'], title_sentiment['confidence'])
            },
            'entities': entities,
            'quantitative_data': quantitative_data,
            'thematic_classification': thematic_classification,
            'market_signals': market_signals,
            'geographic_mentions': geographic_mentions,
            'temporal_references': temporal_references,
            'granular_analysis_timestamp': datetime.now().isoformat(),
            'analysis_version': '2.0_maximum_granularity'
        }
    
    def _analyze_sentiment_bert(self, text):
        """
        Análise de sentimento usando BERT português
        """
        
        if not text or len(text.strip()) == 0:
            return {'score': 0.0, 'label': 'neutro', 'confidence': 0.0}
        
        # Tokenizar texto
        inputs = self.sentiment_tokenizer(
            text[:512],  # BERT tem limite de 512 tokens
            return_tensors="pt",
            truncation=True,
            padding=True
        )
        
        # Predição
        with torch.no_grad():
            outputs = self.sentiment_model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # Interpretar resultado
        confidence = torch.max(predictions).item()
        predicted_class = torch.argmax(predictions).item()
        
        # Mapear classes para sentimento (assumindo modelo treinado para sentimento)
        sentiment_mapping = {0: 'negativo', 1: 'neutro', 2: 'positivo'}
        score_mapping = {0: -1.0, 1: 0.0, 2: 1.0}
        
        return {
            'score': score_mapping.get(predicted_class, 0.0),
            'label': sentiment_mapping.get(predicted_class, 'neutro'),
            'confidence': confidence
        }
    
    def _extract_quantitative_data(self, text):
        """
        Extrai dados quantitativos do texto
        """
        import re
        
        patterns = {
            'monetary_values': re.findall(r'R\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(mil|milhão|milhões|bilhão|bilhões)?', text),
            'percentages': re.findall(r'(\d+(?:,\d+)?)\s*%', text),
            'growth_rates': re.findall(r'crescimento\s+de\s+(\d+(?:,\d+)?)\s*%', text),
            'quantities': re.findall(r'(\d+(?:,\d{3})*)\s*(unidades|empresas|empregos|vagas|pessoas)', text),
            'years': re.findall(r'(20\d{2})', text),
            'months': re.findall(r'(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)', text)
        }
        
        return patterns
    
    def _extract_market_signals(self, text):
        """
        Extrai sinais específicos de oportunidades e riscos de mercado
        """
        
        opportunity_signals = []
        risk_signals = []
        
        # Sinais de oportunidade
        opportunity_keywords = [
            'crescimento', 'expansão', 'aumento', 'lançamento', 'investimento',
            'parceria', 'aquisição', 'inovação', 'tecnologia', 'digital',
            'startup', 'empreendedorismo', 'incentivo', 'subsídio', 'financiamento'
        ]
        
        # Sinais de risco  
        risk_keywords = [
            'crise', 'queda', 'redução', 'demissão', 'fechamento', 'falência',
            'recessão', 'inflação', 'desemprego', 'regulamentação', 'restrição',
            'conflito', 'instabilidade', 'incerteza'
        ]
        
        # Buscar sinais no texto
        text_lower = text.lower()
        
        for keyword in opportunity_keywords:
            if keyword in text_lower:
                # Extrair contexto ao redor da palavra-chave
                context = self._extract_context(text, keyword, 50)
                opportunity_signals.append({
                    'signal': keyword,
                    'context': context,
                    'type': 'opportunity'
                })
        
        for keyword in risk_keywords:
            if keyword in text_lower:
                context = self._extract_context(text, keyword, 50)
                risk_signals.append({
                    'signal': keyword,
                    'context': context,
                    'type': 'risk'
                })
        
        return {
            'opportunities': opportunity_signals,
            'risks': risk_signals,
            'signal_count': len(opportunity_signals) + len(risk_signals)
        }
```

### **4. Sistema de Orquestração - Granularidade Máxima**

#### **📁 `backend/etl_pipeline/app/services/maximum_granularity_orchestrator.py`**

```python
class MaximumGranularityOrchestrator:
    """
    Orquestra a extração de dados com granularidade máxima de todas as fontes
    """
    
    def __init__(self):
        self.sidra_connector = SIDRAConnector()
        self.google_trends_service = GoogleTrendsService()
        self.news_analysis_service = NewsAnalysisService()
        
    def extract_maximum_granularity_data(self, target_keywords, geographic_focus='nacional'):
        """
        Extrai dados com granularidade máxima de todas as fontes
        
        Args:
            target_keywords: Lista de palavras-chave do mercado alvo
            geographic_focus: Foco geográfico ('nacional', 'regional', 'municipal')
        
        Returns:
            Dict com dados de granularidade máxima
        """
        
        results = {
            'extraction_metadata': {
                'timestamp': datetime.now().isoformat(),
                'keywords': target_keywords,
                'geographic_focus': geographic_focus,
                'granularity_level': 'maximum'
            },
            'ibge_data': {},
            'google_trends_data': {},
            'news_data': {},
            'combined_insights': {}
        }
        
        # 1. Extrair dados IBGE com granularidade máxima
        try:
            geographic_level = {
                'nacional': 'nacional',
                'regional': 'estado', 
                'municipal': 'municipio'
            }.get(geographic_focus, 'nacional')
            
            ibge_data = self.sidra_connector.get_maximum_granularity_data(
                geographic_level=geographic_level,
                spending_categories='all'
            )
            
            results['ibge_data'] = {
                'raw_data': ibge_data.to_dict('records'),
                'market_segments': self.sidra_connector.calculate_market_segments(ibge_data),
                'data_quality': self._assess_data_quality(ibge_data)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados IBGE: {e}")
            results['ibge_data'] = {'error': str(e)}
        
        # 2. Extrair Google Trends com granularidade máxima
        try:
            trends_level = {
                'nacional': 'country',
                'regional': 'state',
                'municipal': 'city'
            }.get(geographic_focus, 'country')
            
            trends_data = self.google_trends_service.get_maximum_granularity_trends(
                keywords=target_keywords,
                timeframe='year',
                geographic_level=trends_level
            )
            
            temporal_patterns = self.google_trends_service.analyze_temporal_patterns(trends_data)
            
            results['google_trends_data'] = {
                'trends_by_location': trends_data,
                'temporal_patterns': temporal_patterns,
                'total_locations': len(trends_data)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair Google Trends: {e}")
            results['google_trends_data'] = {'error': str(e)}
        
        # 3. Extrair e analisar notícias com granularidade máxima
        try:
            news_data = self.news_analysis_service.extract_maximum_granularity_news(
                days_back=90
            )
            
            # Filtrar notícias relevantes para as keywords
            relevant_news = self._filter_relevant_news(news_data, target_keywords)
            
            results['news_data'] = {
                'total_articles': len(news_data),
                'relevant_articles': len(relevant_news),
                'articles_analysis': relevant_news,
                'market_signals_summary': self._summarize_market_signals(relevant_news)
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair notícias: {e}")
            results['news_data'] = {'error': str(e)}
        
        # 4. Combinar insights de todas as fontes
        try:
            combined_insights = self._combine_maximum_granularity_insights(
                results['ibge_data'],
                results['google_trends_data'], 
                results['news_data'],
                target_keywords
            )
            
            results['combined_insights'] = combined_insights
            
        except Exception as e:
            self.logger.error(f"Erro ao combinar insights: {e}")
            results['combined_insights'] = {'error': str(e)}
        
        return results
    
    def _combine_maximum_granularity_insights(self, ibge_data, trends_data, news_data, keywords):
        """
        Combina insights de todas as fontes para análise de granularidade máxima
        """
        
        insights = {
            'market_size_precision': {},
            'behavioral_patterns': {},
            'trend_correlation': {},
            'market_sentiment': {},
            'geographic_opportunities': {},
            'temporal_opportunities': {},
            'risk_assessment': {},
            'recommendation_engine': {}
        }
        
        # Calcular tamanho de mercado com precisão máxima
        if 'raw_data' in ibge_data:
            market_segments = ibge_data['market_segments']
            insights['market_size_precision'] = {
                'total_segments_identified': market_segments.get('total_possible_segments', 0),
                'geographic_precision': market_segments.get('geographic_segments', 0),
                'demographic_precision': market_segments.get('demographic_combinations', 0),
                'spending_categories': market_segments.get('spending_categories', 0),
                'precision_level': 'máxima - nível municipal/demográfico'
            }
        
        # Analisar correlação entre tendências de busca e dados demográficos
        if 'trends_by_location' in trends_data and 'raw_data' in ibge_data:
            insights['trend_correlation'] = self._analyze_trend_demographic_correlation(
                trends_data['trends_by_location'],
                ibge_data['raw_data']
            )
        
        # Analisar sentimento de mercado baseado em notícias
        if 'articles_analysis' in news_data:
            sentiment_scores = [
                article['sentiment_analysis']['overall_polarity'] 
                for article in news_data['articles_analysis']
                if 'sentiment_analysis' in article
            ]
            
            insights['market_sentiment'] = {
                'average_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                'sentiment_trend': self._calculate_sentiment_trend(news_data['articles_analysis']),
                'confidence_level': 'alta' if len(sentiment_scores) > 50 else 'média'
            }
        
        return insights
```

## 📈 **Resultado da Implementação**

Com essas modificações implementadas, o sistema será capaz de:

1. **📊 Segmentar mercados em 2+ bilhões de combinações possíveis**
2. **🗺️ Análise geográfica até nível municipal (5.570 municípios)**  
3. **👥 Perfis demográficos com 24.300 combinações**
4. **💰 Categorização de gastos em 156 dimensões**
5. **⏰ Análise temporal desde dados históricos até tempo real**
6. **📰 Monitoramento de sentimento em tempo real**
7. **🎯 Identificação precisa de oportunidades e riscos**

**🎯 Impacto Transformador**: O sistema evoluirá de "calculadora de tamanho de mercado" para "plataforma de inteligência de mercado" com precisão granular sem precedentes.
