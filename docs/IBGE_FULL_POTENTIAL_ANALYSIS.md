# IBGE SIDRA - Potencial Completo de Dados

## 📊 Tabelas Atualmente Utilizadas vs. Disponível

### ✅ **EM USO ATUAL (2 de ~8.000 tabelas)**
| Tabela | Nome | Uso no Sistema |
|--------|------|----------------|
| 6407 | População PNAD | Cálculo de market size |
| 6401 | PNAD Contínua | Dados demográficos base |

### 🚀 **POTENCIAL INEXPLORADO (Alto Impacto)**

#### **POF - Pesquisa de Orçamentos Familiares (2017-2018)**
| Tabela | Categoria | Insight Disponível | Status |
|--------|-----------|-------------------|---------|
| **7482** | Recreação/Cultura | Gastos com lazer, livros, cinema, clubes | 🔄 Parcial |
| **7483** | Vestuário | Prioridades estéticas vs. práticas | ❌ Não usado |
| **7484** | Alimentação Fora | Hábitos sociais (restaurantes vs. casa) | 🔄 Parcial |
| **7485** | Transporte | Mobilidade (carro, transporte público) | ❌ Não usado |
| **7486** | Habitação | Prioridades habitacionais | ❌ Não usado |
| **7487** | Saúde | Gastos com saúde e bem-estar | ❌ Não usado |
| **7488** | Educação | Investimento em conhecimento | ❌ Não usado |
| **7489** | Comunicação | Gastos com internet, telefone, TV | ❌ Não usado |
| **7493** | Bens Duráveis | Posse de tecnologia e conforto | 🔄 Parcial |
| **7501** | Bem-estar Subjetivo | Sentimento e satisfação de vida | 🔄 Parcial |

#### **PNAD Contínua (Dados Trimestrais)**
| Tabela | Categoria | Insight Disponível | Status |
|--------|-----------|-------------------|---------|
| **6403** | Trabalho | Situação ocupacional por setor | ❌ Não usado |
| **6408** | Rendimento | Distribuição de renda detalhada | ❌ Não usado |
| **6409** | Educação | Nível educacional da população | ❌ Não usado |
| **6410** | TIC | Acesso à tecnologia e internet | ❌ Não usado |

#### **Censo Demográfico 2022**
| Tabela | Categoria | Insight Disponível | Status |
|--------|-----------|-------------------|---------|
| **9514** | População | Dados censitários mais recentes | ❌ Não usado |
| **3175** | Domicílios | Características habitacionais | ❌ Não usado |

#### **Pesquisas Setoriais**
| Tabela | Categoria | Insight Disponível | Status |
|--------|-----------|-------------------|---------|
| **1612** | Agricultura | PIB Agropecuário por região | ❌ Não usado |
| **5932** | PIB Municipal | Economia local detalhada | ❌ Não usado |
| **6468** | Indicadores | Índices econômicos regionais | ❌ Não usado |

## 🎯 **Como Usar 100% do Potencial IBGE**

### **1. Análise Psicográfica Multidimensional**
```python
# Implementar análise completa POF
pof_tables = {
    'lifestyle': [7482, 7483, 7484],  # Lazer, vestuário, alimentação
    'values': [7487, 7488],           # Saúde, educação  
    'technology': [7489, 7493],       # Comunicação, bens duráveis
    'sentiment': [7501]               # Bem-estar subjetivo
}

def get_complete_psychographic_profile(segment_keywords):
    profile = {}
    for category, tables in pof_tables.items():
        for table in tables:
            data = sidra_client.get_table(table, keywords=segment_keywords)
            profile[category] = process_pof_data(data)
    return profile
```

### **2. Market Size Granular por Região**
```python
# Usar Censo 2022 + PNAD para precisão máxima
def calculate_precise_market_size(niche_keywords, target_demographics):
    census_data = sidra_client.get_table("9514", location="all_states")
    pnad_data = sidra_client.get_table("6401", filters=target_demographics)
    
    # Combina dados censitários com características PNAD
    market_size = cross_reference_census_pnad(census_data, pnad_data)
    return market_size
```

### **3. Índice de Oportunidade Econômica**
```python
# Combinar PIB Municipal + Demografia + POF
def calculate_opportunity_index(location):
    pib_data = sidra_client.get_table("5932", location=location)
    pop_data = sidra_client.get_table("9514", location=location)
    spending_data = sidra_client.get_table("7482", location=location)
    
    opportunity_score = (pib_per_capita * population * spending_propensity)
    return opportunity_score
```

## 📈 **Métricas de Aproveitamento Atual**
- **Tabelas Utilizadas**: 2 de ~8.000 (0.025%)
- **Variáveis Utilizadas**: ~10 de ~50.000 (0.02%)  
- **Potencial Psicográfico**: 15% utilizado
- **Potencial Demográfico**: 30% utilizado
- **Potencial Econômico**: 5% utilizado

## 🚀 **Próximos Passos para 100% de Utilização**
1. Implementar POF completa (8 tabelas restantes)
2. Integrar Censo 2022 (dados mais recentes)
3. Adicionar indicadores econômicos regionais
4. Criar índices compostos (oportunidade, receptividade, competitividade)
5. Implementar análise temporal (PNAD trimestral)
