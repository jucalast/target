# 📊 Melhores Práticas para APIs Externas

## 🎯 Visão Geral

Este documento analisa as três principais fontes externas utilizadas no sistema e implementa as melhores práticas para cada uma:

1. **pytrends** - Google Trends API
2. **sidrapy** - IBGE SIDRA API  
3. **IBGE API Direta** - API REST do IBGE

## 🔍 Análise das APIs Atuais

### 1. Google Trends (pytrends)

#### ❌ Problemas Identificados
- Rate limiting inadequado (código 429 frequente)
- Reconexão desnecessária em cada retry
- Falta de circuit breaker para falhas consecutivas
- Timeouts muito baixos
- Falta de backoff exponencial adequado
- Não usa proxies quando necessário

#### ✅ Melhores Práticas Recomendadas
- **Rate Limiting**: 60s entre requests quando rate limit atingido
- **Backoff Exponential**: `{backoff factor} * (2 ^ ({número de retries} - 1))`
- **Timeouts**: (10, 25) segundos - connect, read
- **Proxies**: HTTPS apenas, com port number
- **Sleep**: Implementar sleep entre requests sucessivos
- **Circuit Breaker**: Para falhas consecutivas

### 2. IBGE SIDRA (sidrapy)

#### ❌ Problemas Identificados
- Cache muito simples sem invalidação inteligente
- Falta de rate limiting específico
- Parâmetros territoriais incompatíveis com certas tabelas
- Validação inadequada de parâmetros
- Falta de metadados de resposta

#### ✅ Melhores Práticas Recomendadas
- **Cache Inteligente**: TTL baseado na natureza dos dados
- **Limite de Consulta**: 100.000 valores por request (limitação oficial)
- **Parâmetros Territoriais**: Validação por tabela
- **Format Optimization**: JSON vs XML baseado no uso
- **Metadata Tracking**: Tracking de origem e qualidade dos dados

### 3. IBGE API Direta

#### ❌ Problemas Identificados
- Rate limiting não implementado
- Falta de cache para metadados
- Validação de caracteres especiais inadequada
- Não usa formato compacto disponível

#### ✅ Melhores Práticas Recomendadas
- **Cache de Metadados**: 24h TTL para estruturas de tabelas
- **Formato Otimizado**: `/f/c` para códigos, `/f/n` para nomes
- **Caracteres Especiais**: Mapeamento adequado (-, .., ..., X)
- **Batch Requests**: Múltiplas dimensões em uma request

## 🚀 Implementações Recomendadas

### Google Trends - Configuração Otimizada

```python
# Configuração robusta com circuit breaker
pytrends = TrendReq(
    hl='pt-BR',
    tz=180,  # Brasília timezone
    timeout=(10, 25),  # (connect, read) 
    proxies=None,  # Adicionar quando necessário
    retries=2,
    backoff_factor=0.1,  # Exponential backoff
    requests_args={'verify': False}
)

# Rate limiting inteligente
RATE_LIMIT_DELAY = 60  # segundos após 429
NORMAL_DELAY = random.uniform(2, 5)  # delay normal
```

### SIDRA - Cache Inteligente

```python
# Cache TTL baseado no tipo de dados
CACHE_TTL = {
    'demographic': 30,      # dados demográficos: 30 dias
    'economic': 7,          # dados econômicos: 7 dias  
    'survey': 90,           # dados de pesquisa: 90 dias
    'census': 365,          # dados do censo: 1 ano
    'metadata': 1           # metadados: 1 dia
}

# Validação de limites oficiais
MAX_VALUES_PER_REQUEST = 100_000
```

### IBGE - Otimização de Parâmetros

```python
# Parâmetros otimizados para performance
params = {
    'h': 'n',        # sem header para economia
    'f': 'c',        # códigos apenas (mais compacto)
    'd': 's',        # decimais padrão
    'formato': 'json'  # JSON mais eficiente que XML
}
```

## 📈 Métricas de Monitoramento

### KPIs Recomendados

1. **Taxa de Sucesso**: % de requests bem-sucedidos
2. **Latência Média**: Tempo médio de resposta
3. **Cache Hit Rate**: % de hits no cache
4. **Rate Limit Events**: Frequência de 429 errors
5. **Data Freshness**: Idade média dos dados em cache

### Alertas Sugeridos

- **Alta Taxa de Falhas**: > 10% em 5 minutos
- **Latência Elevada**: > 30s para Google Trends, > 10s para IBGE
- **Cache Miss Alto**: < 70% hit rate
- **Rate Limit Frequente**: > 5 eventos por hora

## 🔧 Configurações de Produção

### Timeouts Recomendados

```python
TIMEOUTS = {
    'google_trends': {
        'connect': 10,
        'read': 25,
        'total': 60
    },
    'ibge_sidra': {
        'connect': 5,
        'read': 15,
        'total': 30
    },
    'ibge_direct': {
        'connect': 3,
        'read': 10,
        'total': 20
    }
}
```

### Rate Limits

```python
RATE_LIMITS = {
    'google_trends': {
        'requests_per_minute': 1,
        'burst_delay': 60,
        'normal_delay': (2, 5)
    },
    'ibge_sidra': {
        'requests_per_minute': 10,
        'concurrent_requests': 3
    },
    'ibge_direct': {
        'requests_per_minute': 30,
        'concurrent_requests': 5
    }
}
```

## 🛡️ Estratégias de Resiliência

### Circuit Breaker

```python
CIRCUIT_BREAKER = {
    'failure_threshold': 5,     # falhas consecutivas
    'recovery_timeout': 300,    # 5 minutos
    'expected_exception': (RequestException, HTTPError)
}
```

### Retry Policies

```python
RETRY_POLICIES = {
    'google_trends': {
        'max_attempts': 3,
        'backoff_factor': 0.1,
        'max_delay': 60
    },
    'ibge': {
        'max_attempts': 5,
        'backoff_factor': 0.5,
        'max_delay': 30
    }
}
```

## 📋 Checklist de Implementação

### ✅ Google Trends
- [ ] Implementar rate limiting inteligente
- [ ] Adicionar circuit breaker
- [ ] Configurar backoff exponencial  
- [ ] Implementar proxy rotation (se necessário)
- [ ] Adicionar métricas de monitoramento

### ✅ IBGE SIDRA  
- [ ] Cache inteligente com TTL variável
- [ ] Validação de parâmetros territoriais
- [ ] Limite de 100k valores por request
- [ ] Otimização de formato de resposta
- [ ] Tracking de metadados

### ✅ IBGE Direct
- [ ] Cache de metadados com TTL de 24h
- [ ] Mapeamento de caracteres especiais
- [ ] Otimização de parâmetros de formato
- [ ] Implementação de batch requests
- [ ] Monitoramento de performance

## 🎯 Benefícios Esperados

1. **Redução de Falhas**: -80% em rate limit errors
2. **Melhoria de Performance**: -50% latência média
3. **Eficiência de Cache**: +90% hit rate
4. **Confiabilidade**: +99.5% uptime das integrações
5. **Economia de Recursos**: -60% requests desnecessários

---

**Próximos Passos**: Implementar as melhorias uma por vez, começando pelas mais críticas (rate limiting do Google Trends e cache inteligente do SIDRA).
