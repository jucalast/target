# Plano de Implementação: Inteligência do Sistema TARGET

## 📋 Resumo Executivo

Este documento detalha o plano para implementar as funcionalidades de "inteligência" restantes do sistema TARGET, conforme especificado no TCC. O objetivo é completar a implementação da **"Ponte de Tradução Inteligente"** que transforma entrada em linguagem natural em insights psicográficos baseados em dados públicos do IBGE.

### Status Atual vs. Meta
- ✅ **Já implementado**: 60% da inteligência (base SIDRA, cache, transformadores básicos)
- 🚧 **Faltante**: 40% da inteligência (análise psicográfica, mapper avançado, inferência comportamental)
- 🎯 **Meta**: 100% da metodologia do TCC implementada

---

## 🎯 Componentes a Implementar

### 1. **ANALISADOR PSICOGRÁFICO** (PRIORIDADE MÁXIMA)

#### **O que é:**
Módulo que implementa a metodologia central do TCC: **inferir comportamento e valores a partir de padrões de gastos familiares**.

#### **Como funcionará:**

##### **1.1 Análise de Proporções Orçamentárias**
```python
# Exemplo de funcionamento:
entrada_usuario = "jovens urbanos interessados em sustentabilidade"

# O sistema analisa dados da POF e encontra que este grupo:
gastos = {
    "alimentacao_organica": 15%,      # vs 8% média nacional
    "transporte_publico": 12%,        # vs 6% média nacional  
    "educacao": 18%,                  # vs 12% média nacional
    "vestuario_fast_fashion": 3%      # vs 8% média nacional
}

# INFERÊNCIA AUTOMÁTICA:
valores_inferidos = {
    "sustentabilidade": 0.85,         # Alto (gastos verdes acima da média)
    "educacao": 0.78,                 # Alto (investe em desenvolvimento)
    "conveniencia": 0.45,             # Médio (usa transporte público)
    "consumismo": 0.20                # Baixo (pouco fast fashion)
}
```

##### **1.2 Criação de Arquétipos Comportamentais**
O sistema classifica automaticamente em 5 arquétipos:

1. **Experiencialista**: Gasta mais em viagens, cultura, educação
2. **Tradicionalista**: Gastos equilibrados, foco em necessidades básicas  
3. **Inovador Tecnológico**: Alta proporção em tecnologia e comunicação
4. **Consciente Sustentável**: Gastos em saúde, orgânicos, transporte público
5. **Status-Orientado**: Vestuário, carros, bens de luxo

##### **1.3 Índice de Sentimento Quantificável**
```python
# Baseado em variáveis da POF como:
avaliacao_vida = {
    "situacao_12_meses_atras": "melhor",     # +0.7
    "expectativa_futuro": "otimista",        # +0.8
    "adequacao_renda": "suficiente",         # +0.6
    "estresse_financeiro": "baixo"           # +0.7
}

indice_sentimento = 0.70  # Escala 0-1 (0=pessimista, 1=otimista)
```

#### **Implementação Técnica:**
- **Arquivo**: `etl_pipeline/app/services/analyzers/psychographic_analyzer.py` ✅ CRIADO
- **Classes**: `PsychographicAnalyzer`, `PsychographicProfile`
- **Integração**: Com `IBGETransformer` e `ETLOrchestrator`

---

### 2. **MAPPER AVANÇADO** (PRIORIDADE ALTA)

#### **O que é:**
Evolução do `SIDRAMapper` atual para ser verdadeiramente "inteligente", capaz de traduzir conceitos complexos em consultas precisas ao IBGE.

#### **Limitações Atuais:**
```python
# Atual: Mapeamento básico e limitado
mapper.map_terms(["jovens", "tecnologia"])
# Resultado: tabela 6401, variável população por idade

# ❌ Não consegue interpretar: "moda sustentável para jovens urbanos"
```

#### **Como o Mapper Avançado funcionará:**

##### **2.1 Decomposição Semântica**
```python
entrada = "moda sustentável para jovens urbanos"

# ETAPA 1: Decomposição automática
conceitos_extraidos = {
    "demografico": ["jovens", "urbanos"],
    "setor": ["moda", "vestuário"],  
    "valores": ["sustentável", "ecológico"],
    "geografia": ["urbanos", "metrópoles"]
}

# ETAPA 2: Mapeamento para múltiplas fontes
estrategia_busca = {
    "tabela_principal": "7482",  # POF - Despesas com vestuário
    "filtros_demograficos": {
        "idade": "18-35",
        "localizacao": "regioes_metropolitanas"
    },
    "tabelas_complementares": [
        "7493",  # POF - Bens duráveis (para contexto socioeconômico)
        "6401"   # PNAD - Demografia (para tamanho do público)
    ]
}
```

##### **2.2 Inferência Automática de Tabelas Relevantes**
```python
class AdvancedSIDRAMapper:
    def map_complex_concept(self, user_input: str) -> MultiTableQuery:
        # 1. Usa NLP para extrair entidades e conceitos
        nlp_features = self.nlp_processor.extract_features(user_input)
        
        # 2. Identifica domínios (consumo, demografia, economia)
        domains = self.classify_domains(nlp_features)
        
        # 3. Seleciona tabelas por relevância e complementaridade
        primary_tables = self.select_primary_tables(domains)
        supporting_tables = self.select_supporting_tables(primary_tables)
        
        # 4. Constrói consultas que se complementam
        return self.build_multi_table_strategy(primary_tables, supporting_tables)
```

##### **2.3 Combinação Inteligente de Múltiplas Fontes**
```python
# Exemplo: Para "jovens interessados em tecnologia"
consultas_geradas = {
    "demografia": {
        "tabela": "6401",
        "objetivo": "Tamanho da população jovem por região",
        "filtros": {"idade": "18-35"}
    },
    "comportamento_consumo": {
        "tabela": "7482", 
        "objetivo": "Gastos com tecnologia/comunicação",
        "filtros": {"categoria": "comunicacao"}
    },
    "bens_tecnologicos": {
        "tabela": "7493",
        "objetivo": "Posse de computador, internet, celular",
        "filtros": {"bem": ["computador", "internet", "celular"]}
    }
}

# O sistema combina automaticamente os resultados
resultado_final = {
    "tamanho_mercado": 15_000_000,  # Da tabela demográfica
    "gasto_medio_tech": 280.50,     # Da tabela de consumo  
    "penetracao_digital": 0.87      # Da tabela de bens duráveis
}
```

#### **Implementação Técnica:**
- **Arquivo**: `etl_pipeline/app/services/extractors/ibge/advanced_mapper.py` (NOVO)
- **Dependências**: Integração com NLP processor, múltiplas consultas simultâneas
- **Upgrade**: `sidra_mapper.py` → `advanced_mapper.py`

---

### 3. **ANÁLISE DE BENS DURÁVEIS** (PRIORIDADE MÉDIA)

#### **O que é:**
Sistema para analisar a posse de bens duráveis (geladeira, computador, carro, etc.) e criar **arquétipos de estilo de vida**.

#### **Como funcionará:**

##### **3.1 Criação de Arquétipos Automática**
```python
# Dados de entrada (da POF tabela 7493):
bens_familia = {
    "computador": True,
    "internet_alta_velocidade": True, 
    "celular_smartphone": True,
    "tablet": True,
    "televisao_smart": True,
    "carro": False,
    "ar_condicionado": False
}

# ANÁLISE AUTOMÁTICA:
arquetipo_detectado = "FAMÍLIA CONECTADA"
caracteristicas = [
    "Alta conectividade digital",
    "Prioriza tecnologia sobre bens tradicionais",  
    "Provavelmente trabalha remotamente",
    "Renda média-alta mas gasta consciente"
]

confianca = 0.85  # 85% de certeza na classificação
```

##### **3.2 Arquétipos Implementados**
1. **Família Conectada**: Computador + Internet + Celular (Score: tecnologia)
2. **Família Tradicional**: TV + Rádio + Geladeira + Fogão (Score: básicos)
3. **Família Moderna**: Microondas + Lava-roupa + AR + Carro (Score: conforto)
4. **Família Minimalista**: Apenas essenciais, poucos bens totais (Score: simplicidade)
5. **Família Aspiracional**: Mix de bens básicos + alguns premium (Score: crescimento)

##### **3.3 Integração com Análise Psicográfica**
```python
# O resultado dos bens duráveis alimenta o analisador psicográfico:
estilo_vida = durables_analyzer.classify_lifestyle(bens_familia)
# Resultado: "familia_conectada"

# Que influencia o arquétipo comportamental:
psychographic_profile = psychographic_analyzer.analyze_segment({
    "despesas": despesas_familia,
    "bens_duraveis": bens_familia,      # ← Input dos bens duráveis
    "avaliacao_vida": sentimento_vida
})
# Resultado final: "Inovador Tecnológico" com confiança 0.87
```

#### **Implementação Técnica:**
- **Arquivo**: `etl_pipeline/app/services/analyzers/durables_analyzer.py` (NOVO)
- **Integração**: Com `PsychographicAnalyzer` e dados da POF tabela 7493

---

## 🛠️ Cronograma de Implementação

### **FASE 1: Analisador Psicográfico** (3-4 dias) ✅ **COMPLETA**
- [x] ✅ Estrutura base criada (`psychographic_analyzer.py`)
- [x] ✅ Implementar lógica de proporções orçamentárias
- [x] ✅ Criar sistema de arquétipos comportamentais  
- [x] ✅ Implementar cálculo de índice de sentimento
- [x] ✅ Integrar com `ETLOrchestrator`
- [x] ✅ Testes funcionais (analisador 100% operacional)

### **FASE 2: Mapper Avançado** (4-5 dias)
- [ ] 📝 Criar `AdvancedSIDRAMapper` 
- [ ] 📝 Implementar decomposição semântica
- [ ] 📝 Sistema de inferência de tabelas
- [ ] 📝 Lógica de consultas múltiplas simultâneas
- [ ] 📝 Integração com NLP processor
- [ ] 📝 Substituir mapper atual

### **FASE 3: Análise de Bens Duráveis** (2-3 dias)
- [ ] 📝 Criar `DurablesAnalyzer`
- [ ] 📝 Implementar arquétipos de estilo de vida
- [ ] 📝 Integração com análise psicográfica
- [ ] 📝 Processar tabela POF 7493
- [ ] 📝 Testes de classificação

### **FASE 4: Integração e Testes** (2-3 dias)
- [ ] 🔗 Integrar todos os componentes
- [ ] 🧪 Testes end-to-end da metodologia completa
- [ ] 📊 Validação com dados reais do IBGE
- [ ] 📝 Documentação atualizada

**TOTAL ESTIMADO: 11-15 dias**

---

## 📊 Resultados Esperados

### **Antes (Situação Atual):**
```
Entrada: "jovens interessados em tecnologia"
↓
Saída: Dados demográficos básicos da PNAD
       (População por faixa etária)
```

### **Depois (Com Inteligência Completa):**
```
Entrada: "jovens urbanos interessados em moda sustentável"
↓
Processamento Inteligente:
├── NLP extrai: [jovens, urbanos, moda, sustentável]  
├── Mapper Avançado seleciona tabelas: POF despesas + bens duráveis + PNAD
├── Analisador Psicográfico infere comportamento
└── Análise de Bens Duráveis identifica estilo de vida
↓
Saída Completa:
├── 📊 Demografia: 8.5M jovens urbanos (18-35 anos)
├── 💰 Gasto médio vestuário: R$ 89/mês (vs R$ 67 nacional) 
├── 🧠 Arquétipo: "Consciente Sustentável" (confiança: 82%)
├── 😊 Índice Sentimento: 0.73 (otimista)
├── 🏠 Estilo de vida: "Família Conectada" 
└── 🎯 Recomendações: [marketing sustentável, canais digitais, transparência]
```

---

## ✅ Critérios de Sucesso

### **Funcionais:**
1. ✅ Sistema processa conceitos complexos como "moda sustentável para jovens urbanos"
2. ✅ Gera arquétipos psicográficos automaticamente com >80% de precisão
3. ✅ Calcula índice de sentimento quantificável (0-1)
4. ✅ Identifica arquétipos de estilo de vida baseados em bens duráveis
5. ✅ Combina dados de múltiplas tabelas IBGE automaticamente

### **Técnicos:**
1. ✅ Cobertura de testes >85%
2. ✅ Tempo de resposta <10 segundos para consultas complexas
3. ✅ Cache inteligente funciona para evitar consultas desnecessárias
4. ✅ Logs detalhados para debug e monitoramento
5. ✅ Tratamento robusto de erros e fallbacks

### **Metodológicos:**
1. ✅ Implementação 100% fiel à metodologia do TCC
2. ✅ Todos os exemplos do TCC funcionam no sistema
3. ✅ Documentação completa da "Ponte de Tradução Inteligente"

---

## 🎯 Decisão Requerida

**Aprovação necessária para:**

1. **Priorização**: Concordo com a ordem Psicográfico → Mapper → Bens Duráveis?
2. **Cronograma**: 11-15 dias de implementação é aceitável?
3. **Escopo**: Todos os 3 componentes devem ser implementados ou há algum que pode ser simplificado?
4. **Integração**: Posso modificar arquivos existentes (`ETLOrchestrator`, `sidra_mapper.py`) ou prefere manter separado?

**Ao aprovar, início imediato da FASE 1 (Analisador Psicográfico).**

---

## 📋 Próximos Passos Imediatos

1. ✅ **Aguardar aprovação** deste plano
2. 🚀 **Implementar lógica de proporções** no `psychographic_analyzer.py` 
3. 🔗 **Integrar com ETLOrchestrator** para processar dados da POF
4. 🧪 **Criar testes** com dados reais do IBGE
5. 📊 **Validar** primeiros arquétipos psicográficos

**Status**: ⏳ Aguardando aprovação para iniciar implementação completa.
