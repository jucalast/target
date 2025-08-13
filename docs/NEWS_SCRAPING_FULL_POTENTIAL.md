# News Scraping - Potencial Completo de Dados

## 📊 Fontes Atualmente Utilizadas vs. Disponível

### ✅ **EM USO ATUAL (~10% do potencial)**
| Fonte | Domínio | Status | Artigos/Dia |
|-------|---------|--------|-------------|
| Agência Brasil | agenciabrasil.ebc.com.br | ✅ Ativo | 2-3 |
| G1 | g1.globo.com | ✅ Ativo | 2-3 |
| Valor Econômico | valor.globo.com | ✅ Ativo | 1-2 |

### 🚀 **POTENCIAL INEXPLORADO (90% não utilizado)**

#### **Fontes Governamentais Oficiais (Legalmente Seguras)**
| Fonte | Domínio | Potencial Diário | Área de Cobertura |
|-------|---------|-----------------|-------------------|
| **Portal Gov.br** | gov.br/agenciabrasil | 20-30 artigos | Todas as áreas |
| **IBGE Notícias** | agenciadenotícias.ibge.gov.br | 5-10 artigos | Economia, Demografia |
| **Banco Central** | bcb.gov.br/pre/noticias | 3-5 artigos | Economia, Finanças |
| **BNDES** | bndes.gov.br/wps/portal/site/home/imprensa | 2-4 artigos | Desenvolvimento, Setores |
| **Ministério da Economia** | fazenda.gov.br/noticias | 5-8 artigos | Política Econômica |
| **SEBRAE** | sebrae.com.br/sites/PortalSebrae/noticias | 10-15 artigos | Pequenas Empresas |
| **FIESP** | fiesp.com.br/noticias | 5-10 artigos | Indústria |
| **CNI** | noticias.portaldaindustria.com.br | 8-12 artigos | Indústria Nacional |

#### **Portais Estaduais (Expansão Regional)**
| Estado | Portal Oficial | Potencial Diário | Cobertura |
|--------|----------------|-----------------|-----------|
| **São Paulo** | saopaulo.sp.gov.br/noticias | 15-20 artigos | Economia SP |
| **Rio de Janeiro** | rj.gov.br/noticias | 10-15 artigos | Economia RJ |
| **Minas Gerais** | mg.gov.br/noticias | 8-12 artigos | Economia MG |
| **Paraná** | aen.pr.gov.br | 6-10 artigos | Economia PR |

#### **Fontes Setoriais Especializadas**
| Setor | Fonte | Domínio | Potencial |
|-------|-------|---------|-----------|
| **Tecnologia** | Portal MCTI | mctic.gov.br | 3-5 artigos/dia |
| **Agricultura** | MAPA Notícias | gov.br/agricultura/pt-br/assuntos/noticias | 5-8 artigos/dia |
| **Saúde** | Portal Saúde | saude.gov.br/noticias | 8-12 artigos/dia |
| **Educação** | Portal MEC | mec.gov.br/component/tags/tag/noticias | 4-6 artigos/dia |
| **Turismo** | Portal Turismo | turismo.gov.br/noticias.html | 2-4 artigos/dia |

## 🔍 **Análise de Sentimento Não Implementada**

### **ATUAL: Scraping Básico**
```python
# Só extrai: título, conteúdo, data, autor
article = {
    'title': title,
    'content': content,
    'published_at': date,
    'author': author
}
```

### **POTENCIAL: Análise Completa de Sentimento**
```python
def enhanced_news_analysis(articles, niche_keywords):
    """Análise completa de notícias com sentimento e relevância"""
    
    analyzed_articles = []
    for article in articles:
        # 1. Análise de sentimento com BERT pt-BR
        sentiment = analyze_sentiment_bert(article.content)
        
        # 2. Relevância para o nicho
        relevance_score = calculate_niche_relevance(
            article.content, niche_keywords
        )
        
        # 3. Extração de entidades específicas
        entities = extract_business_entities(article.content)
        
        # 4. Classificação de tópicos
        topics = classify_article_topics(article.content)
        
        # 5. Impacto econômico inferido
        economic_impact = infer_economic_impact(article.content)
        
        analyzed_articles.append({
            **article,
            'sentiment': sentiment,
            'relevance_score': relevance_score,
            'entities': entities,
            'topics': topics,
            'economic_impact': economic_impact,
            'market_signals': extract_market_signals(article.content)
        })
    
    return analyzed_articles
```

## 📈 **Agregação de Insights Não Implementada**

### **ATUAL: Lista de Artigos**
```python
# Retorna lista simples
return [article1, article2, article3]
```

### **POTENCIAL: Índices Agregados**
```python
def calculate_market_sentiment_index(analyzed_articles, niche):
    """Calcula índices compostos de sentimento de mercado"""
    
    # 1. Índice de Sentimento Setorial
    sector_sentiment = calculate_weighted_sentiment(
        articles=analyzed_articles,
        weights='relevance_score'
    )
    
    # 2. Índice de Momentum
    momentum_index = calculate_momentum_index(
        articles=analyzed_articles,
        timeframe='last_30_days'
    )
    
    # 3. Índice de Oportunidade
    opportunity_index = calculate_opportunity_signals(
        articles=analyzed_articles,
        keywords=['crescimento', 'investimento', 'expansão']
    )
    
    # 4. Índice de Risco
    risk_index = calculate_risk_signals(
        articles=analyzed_articles,
        keywords=['crise', 'redução', 'dificuldade']
    )
    
    return {
        'sector_sentiment': sector_sentiment,      # -1 a +1
        'momentum_index': momentum_index,          # 0 a 100
        'opportunity_index': opportunity_index,    # 0 a 100
        'risk_index': risk_index,                 # 0 a 100
        'overall_market_score': (
            sector_sentiment * 0.3 +
            momentum_index * 0.25 +
            opportunity_index * 0.25 +
            (100 - risk_index) * 0.2
        )
    }
```

## 🎯 **Implementação para 100% de Utilização**

### **1. Expansão de Fontes (×10 mais artigos)**
```python
ENHANCED_NEWS_SOURCES = {
    'government': [
        'gov.br/agenciabrasil',
        'agenciadenotícias.ibge.gov.br',
        'bcb.gov.br/pre/noticias',
        'fazenda.gov.br/noticias',
        'sebrae.com.br/sites/PortalSebrae/noticias'
    ],
    'regional': [
        'saopaulo.sp.gov.br/noticias',
        'rj.gov.br/noticias', 
        'mg.gov.br/noticias'
    ],
    'sectoral': [
        'mctic.gov.br',
        'gov.br/agricultura/pt-br/assuntos/noticias',
        'saude.gov.br/noticias'
    ]
}

def enhanced_news_scraping(query, max_results=50):
    """Coleta notícias de todas as fontes oficiais"""
    all_articles = []
    
    for category, sources in ENHANCED_NEWS_SOURCES.items():
        for source in sources:
            try:
                articles = scrape_source_specific(source, query)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(f"Erro em {source}: {e}")
    
    return all_articles[:max_results]
```

### **2. Análise de Sentimento Avançada**
```python
from transformers import pipeline

def setup_sentiment_analysis():
    """Configura análise de sentimento para português"""
    return pipeline(
        "sentiment-analysis",
        model="neuralmind/bert-base-portuguese-cased",
        tokenizer="neuralmind/bert-base-portuguese-cased"
    )

def analyze_article_sentiment(article_content):
    """Análise de sentimento específica para notícias de mercado"""
    sentiment_analyzer = setup_sentiment_analysis()
    
    # Divide o artigo em segmentos para análise
    segments = split_article_segments(article_content)
    
    sentiment_scores = []
    for segment in segments:
        result = sentiment_analyzer(segment)
        sentiment_scores.append({
            'segment': segment[:100] + '...',
            'label': result[0]['label'],
            'score': result[0]['score']
        })
    
    # Calcula sentimento agregado
    overall_sentiment = aggregate_sentiment_scores(sentiment_scores)
    
    return {
        'overall_sentiment': overall_sentiment,
        'segment_analysis': sentiment_scores,
        'confidence': calculate_sentiment_confidence(sentiment_scores)
    }
```

### **3. Extração de Sinais de Mercado**
```python
def extract_market_signals(article_content, niche_keywords):
    """Extrai sinais específicos do mercado"""
    
    # Padrões de oportunidade
    opportunity_patterns = [
        r'crescimento\s+de\s+(\d+(?:,\d+)?%)',
        r'investimento\s+de\s+R\$\s*([\d,.]+)',
        r'expansão\s+para\s+(\w+(?:\s+\w+)*)',
        r'nova\s+tecnologia\s+(\w+(?:\s+\w+)*)',
        r'aumento\s+da\s+demanda'
    ]
    
    # Padrões de risco
    risk_patterns = [
        r'redução\s+de\s+(\d+(?:,\d+)?%)',
        r'crise\s+no\s+setor',
        r'dificuldades\s+financeiras',
        r'regulamentação\s+restritiva'
    ]
    
    signals = {
        'opportunities': extract_patterns(article_content, opportunity_patterns),
        'risks': extract_patterns(article_content, risk_patterns),
        'market_size_mentions': extract_market_size_data(article_content),
        'competitor_mentions': extract_competitor_data(article_content),
        'regulatory_changes': extract_regulatory_signals(article_content)
    }
    
    return signals
```

## 📊 **Métricas de Aproveitamento Atual News Scraping**

| Aspecto | Utilização Atual | Potencial Disponível | % Utilizado |
|---------|------------------|---------------------|-------------|
| **Fontes** | 3 | 30+ fontes oficiais | 10% |
| **Artigos/Dia** | 6 | 100+ artigos | 6% |
| **Análise de Sentimento** | Básica | BERT + NLP avançado | 5% |
| **Sinais de Mercado** | Não extrai | Padrões específicos | 0% |
| **Agregação de Insights** | Não agrega | Índices compostos | 0% |
| **Cobertura Regional** | Nacional | Estados + setores | 20% |

## 🚀 **Resultado Esperado com 100% de Utilização**

### **Input Atual**
```json
"news_scraping": {
  "status": "success",
  "sources": ["g1.globo.com", "agenciabrasil.ebc.com.br", "valor.globo.com"],
  "articles_found": 6,
  "quality": "official_news_sources"
}
```

### **Output com 100% de Potencial**
```json
"news_analysis_complete": {
  "status": "success",
  "sources_analyzed": 25,
  "articles_processed": 85,
  "market_sentiment_index": 0.73,
  "opportunity_signals": [
    {"signal": "crescimento 15% setor tecnologia", "confidence": 0.89},
    {"signal": "investimento R$ 2.3bi startups", "confidence": 0.92}
  ],
  "risk_signals": [
    {"signal": "regulamentação LGPD", "confidence": 0.67}
  ],
  "regional_insights": {
    "sp": {"sentiment": 0.81, "articles": 23},
    "rj": {"sentiment": 0.65, "articles": 15}
  },
  "sectoral_analysis": {
    "technology": {"sentiment": 0.78, "momentum": 85},
    "finance": {"sentiment": 0.62, "momentum": 72}
  },
  "economic_indicators": {
    "market_size_mentions": ["mercado R$ 50bi", "crescimento 12%"],
    "investment_flows": ["investimento VC R$ 800mi", "IPO previsto Q2"]
  }
}
```

## 💡 **Próximos Passos Práticos**
1. **Implementar fonte de dados do SEBRAE** (alta relevância para PMEs)
2. **Adicionar análise de sentimento BERT português**
3. **Criar índices compostos de mercado**
4. **Implementar extração de sinais quantitativos**
5. **Adicionar agregação por região e setor**
