"""
Script simplificado para descobrir e testar tabelas POF reais do IBGE.
"""
import sidrapy
import pandas as pd
import json

def discover_pof_tables():
    """Descobre e testa tabelas POF disponíveis."""
    
    print("🔍 DESCOBRINDO TABELAS POF REAIS...")
    
    # Algumas tabelas POF conhecidas da documentação do IBGE
    # Baseado em consultas reais à API SIDRA
    candidate_tables = [
        {"code": "7482", "name": "POF - Despesas familiares"},
        {"code": "7483", "name": "POF - Despesas alimentação"},
        {"code": "7484", "name": "POF - Despesas vestuário"},
        {"code": "7485", "name": "POF - Despesas habitação"},
        {"code": "7486", "name": "POF - Despesas transporte"},
        {"code": "7487", "name": "POF - Despesas saúde"},
        {"code": "7488", "name": "POF - Despesas educação"},
        {"code": "9050", "name": "POF - Bens duráveis"},
        {"code": "9052", "name": "POF - Avaliação vida"},
    ]
    
    working_tables = []
    
    for table in candidate_tables:
        print(f"\n📊 Testando {table['code']}: {table['name']}")
        
        try:
            # Teste básico - só para ver se a tabela existe
            # Usando a abordagem mais simples possível
            test_data = sidrapy.get_table(
                table_code=table["code"],
                territorial_level="1",
                ibge_territorial_code="all"
            )
            
            if test_data is not None and len(test_data) > 0:
                df = pd.DataFrame(test_data)
                print(f"   ✅ FUNCIONA! {len(df)} registros, {len(df.columns)} colunas")
                
                # Mostra algumas colunas para entender a estrutura
                print(f"   📋 Colunas: {list(df.columns)[:8]}...")
                if len(df) > 0:
                    print(f"   📅 Período: {df.iloc[0].get('D3N', 'N/A')}")
                
                working_tables.append({
                    **table,
                    "columns": list(df.columns),
                    "sample_data": df.head(2).to_dict('records'),
                    "total_records": len(df)
                })
            else:
                print(f"   ⚠️ Tabela existe mas sem dados")
                
        except Exception as e:
            error_msg = str(e)
            if "Tabela inválida" in error_msg:
                print(f"   ❌ Tabela não existe")
            elif "inexistente" in error_msg:
                print(f"   ⚠️ Tabela existe mas com estrutura diferente")
            else:
                print(f"   ❌ Erro: {error_msg}")
    
    return working_tables

def test_specific_pof_queries():
    """Testa consultas específicas das tabelas que funcionaram."""
    
    print(f"\n\n🧪 TESTANDO CONSULTAS ESPECÍFICAS...")
    
    # Vamos tentar a tabela mais comum do POF
    table_7482_queries = [
        {
            "name": "Consulta básica",
            "params": {
                "table_code": "7482",
                "territorial_level": "1",
                "ibge_territorial_code": "all"
            }
        },
        {
            "name": "Com período específico",
            "params": {
                "table_code": "7482",
                "territorial_level": "1", 
                "ibge_territorial_code": "all",
                "period": "last 1"
            }
        }
    ]
    
    results = {}
    
    for query in table_7482_queries:
        print(f"\n🔬 {query['name']}...")
        try:
            data = sidrapy.get_table(**query["params"])
            if data is not None and len(data) > 0:
                df = pd.DataFrame(data)
                print(f"   ✅ Sucesso: {len(df)} registros")
                
                # Analisa as colunas para entender a estrutura
                print(f"   📊 Colunas disponíveis:")
                for col in df.columns[:10]:  # Primeiras 10 colunas
                    sample_values = df[col].dropna().unique()[:3]
                    print(f"      - {col}: {sample_values}")
                
                results[query["name"]] = {
                    "success": True,
                    "records": len(df),
                    "columns": list(df.columns),
                    "sample": df.head(3).to_dict('records')
                }
            else:
                print(f"   ❌ Sem dados")
                results[query["name"]] = {"success": False, "error": "No data"}
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            results[query["name"]] = {"success": False, "error": str(e)}
    
    return results

def extract_pof_structure(table_code="7482"):
    """Extrai a estrutura completa de uma tabela POF para mapeamento."""
    
    print(f"\n\n🏗️ EXTRAINDO ESTRUTURA DA TABELA {table_code}...")
    
    try:
        # Consulta mais ampla para ver todas as dimensões
        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level="1",
            ibge_territorial_code="all",
            period="last 1"
        )
        
        if data is not None and len(data) > 0:
            df = pd.DataFrame(data)
            print(f"   ✅ {len(df)} registros obtidos")
        else:
            print("   ❌ Nenhum dado retornado")
            return None
        
        # Analisa cada coluna
        structure = {}
        for col in df.columns:
            unique_values = df[col].dropna().unique()
            structure[col] = {
                "unique_count": len(unique_values),
                "sample_values": list(unique_values[:10]),
                "data_type": str(df[col].dtype)
            }
            
            print(f"   📋 {col}: {len(unique_values)} valores únicos")
            if len(unique_values) <= 20:  # Se há poucos valores, mostra todos
                print(f"      Valores: {list(unique_values)}")
            else:  # Se há muitos, mostra apenas uma amostra
                print(f"      Amostra: {list(unique_values[:5])}...")
        
        # Procura por colunas que podem ser categorias de despesa
        expense_candidates = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['d2', 'categoria', 'despesa', 'grupo']):
                expense_candidates.append(col)
        
        if expense_candidates:
            print(f"\n   🎯 Possíveis colunas de categoria de despesa: {expense_candidates}")
            
            for col in expense_candidates:
                unique_cats = df[col].unique()
                print(f"      {col}: {len(unique_cats)} categorias")
                if len(unique_cats) <= 50:
                    for cat in unique_cats:
                        print(f"         - {cat}")
        
        return structure
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return None

if __name__ == "__main__":
    print("🏠 DESCOBERTA DE TABELAS POF PARA ANÁLISE PSICOGRÁFICA REAL")
    print("=" * 65)
    
    # 1. Descobre tabelas que funcionam
    working_tables = discover_pof_tables()
    
    # 2. Testa consultas específicas
    query_results = test_specific_pof_queries()
    
    # 3. Extrai estrutura detalhada
    structure = extract_pof_structure()
    
    # 4. Compila resultados
    final_results = {
        "working_tables": working_tables,
        "query_tests": query_results,
        "table_structure": structure,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Salva resultados
    with open("pof_discovery_results.json", "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n📋 RESUMO FINAL:")
    print(f"   📊 Tabelas funcionais encontradas: {len(working_tables)}")
    if working_tables:
        for table in working_tables:
            print(f"      ✅ {table['code']}: {table['name']} ({table['total_records']} registros)")
    
    print(f"   🧪 Testes de consulta realizados: {len(query_results)}")
    successful_queries = sum(1 for r in query_results.values() if r.get('success'))
    print(f"   ✅ Consultas bem-sucedidas: {successful_queries}")
    
    print(f"   💾 Resultados salvos em: pof_discovery_results.json")
    
    if working_tables:
        print(f"\n🎯 PRÓXIMA ETAPA: Implementar integração com tabela {working_tables[0]['code']}")
    else:
        print(f"\n⚠️ ATENÇÃO: Nenhuma tabela POF funcional encontrada. Verificar documentação IBGE.")
