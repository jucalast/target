"""
Script para encontrar as tabelas POF REAIS corretas baseado na documentação oficial do IBGE.

Baseado na POF 2017-2018 que é a mais recente disponível.
"""
import sidrapy
import pandas as pd
import json

def find_real_pof_tables():
    """Encontra as tabelas POF reais baseadas na documentação oficial."""
    
    print("🔍 PROCURANDO TABELAS POF OFICIAIS (2017-2018)...")
    
    # Baseado na documentação oficial da POF 2017-2018
    # Fonte: https://sidra.ibge.gov.br/pesquisa/pof/quadros/brasil/2017
    official_pof_tables = [
        {"code": "9050", "name": "Aquisição de bens duráveis", "period": "2017-2018"},
        {"code": "9051", "name": "Inventário de bens duráveis", "period": "2017-2018"},
        {"code": "9052", "name": "Avaliação das condições de vida", "period": "2017-2018"},
        {"code": "9053", "name": "Características gerais dos domicílios", "period": "2017-2018"},
        {"code": "9054", "name": "Características dos moradores", "period": "2017-2018"},
        {"code": "9055", "name": "Despesas monetárias e não monetárias", "period": "2017-2018"},
        {"code": "9056", "name": "Rendimentos monetários", "period": "2017-2018"},
        {"code": "9057", "name": "Rendimentos não monetários", "period": "2017-2018"},
        {"code": "9058", "name": "Variação patrimonial", "period": "2017-2018"},
    ]
    
    working_pof_tables = []
    
    for table in official_pof_tables:
        print(f"\n📊 Testando {table['code']}: {table['name']}")
        
        try:
            # Teste básico
            test_data = sidrapy.get_table(
                table_code=table["code"],
                territorial_level="1",
                ibge_territorial_code="all"
            )
            
            if test_data is not None and len(test_data) > 0:
                df = pd.DataFrame(test_data)
                print(f"   ✅ ENCONTRADA! {len(df)} registros, {len(df.columns)} colunas")
                
                # Verifica se tem dados reais (não só headers)
                actual_data_rows = df[df['V'] != 'Valor']  # Remove header row
                if len(actual_data_rows) > 0:
                    print(f"   📊 Dados reais: {len(actual_data_rows)} registros")
                    
                    # Mostra amostra dos dados
                    sample_values = actual_data_rows['V'].dropna().head(3).tolist()
                    print(f"   💰 Amostra valores: {sample_values}")
                    
                    working_pof_tables.append({
                        **table,
                        "columns": list(df.columns),
                        "total_records": len(df),
                        "data_records": len(actual_data_rows),
                        "sample_values": sample_values
                    })
                else:
                    print(f"   ⚠️ Apenas headers, sem dados")
            else:
                print(f"   ❌ Sem dados retornados")
                
        except Exception as e:
            error_msg = str(e)
            if "Tabela inválida" in error_msg or "inválida" in error_msg:
                print(f"   ❌ Tabela não existe na API")
            else:
                print(f"   ❌ Erro: {error_msg}")
    
    return working_pof_tables

def analyze_pof_expense_structure(table_code="9055"):
    """Analisa a estrutura da tabela de despesas POF."""
    
    print(f"\n\n🔬 ANALISANDO ESTRUTURA DE DESPESAS - TABELA {table_code}...")
    
    try:
        # Consulta com todas as variáveis disponíveis
        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level="1",
            ibge_territorial_code="all"
        )
        
        if data is not None and len(data) > 0:
            df = pd.DataFrame(data)
            print(f"   ✅ {len(df)} registros obtidos")
            
            # Remove linha de cabeçalho
            data_df = df[df['V'] != 'Valor'].copy()
            if len(data_df) == 0:
                print("   ⚠️ Apenas headers encontrados")
                return None
            
            print(f"   📊 Dados reais: {len(data_df)} registros")
            
            # Analisa variáveis disponíveis
            if 'D3N' in data_df.columns:
                variables = data_df['D3N'].unique()
                print(f"   📋 Variáveis disponíveis ({len(variables)}):")
                for var in variables[:10]:  # Primeiras 10
                    print(f"      - {var}")
                if len(variables) > 10:
                    print(f"      ... e mais {len(variables) - 10} variáveis")
            
            # Analisa classificações (possíveis categorias de despesa)
            for col in data_df.columns:
                if col.startswith('D') and col.endswith('N') and col != 'D3N':  # Outras dimensões
                    categories = data_df[col].unique()
                    if len(categories) > 1 and len(categories) < 50:  # Número razoável de categorias
                        print(f"   🏷️ {col} ({len(categories)} categorias):")
                        for cat in categories[:15]:
                            print(f"      - {cat}")
                        if len(categories) > 15:
                            print(f"      ... e mais {len(categories) - 15} categorias")
            
            # Procura por dados de valores monetários
            numeric_values = []
            for val in data_df['V'].dropna():
                try:
                    if val != '..' and val != '-':
                        numeric_values.append(float(val))
                except:
                    pass
            
            if numeric_values:
                print(f"   💰 Valores numéricos encontrados: {len(numeric_values)}")
                print(f"   💰 Amostra: {numeric_values[:5]}")
                print(f"   💰 Faixa: {min(numeric_values):.2f} - {max(numeric_values):.2f}")
            
            return {
                "total_records": len(data_df),
                "numeric_values": len(numeric_values),
                "columns": list(data_df.columns),
                "sample_data": data_df.head(5).to_dict('records')
            }
        else:
            print("   ❌ Nenhum dado retornado")
            return None
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return None

def test_pof_classifications(table_code="9055"):
    """Testa diferentes classificações na tabela POF para encontrar categorias de despesa."""
    
    print(f"\n\n🎯 TESTANDO CLASSIFICAÇÕES POF - TABELA {table_code}...")
    
    # Possíveis códigos de classificação baseados na documentação POF
    classification_tests = [
        {"code": "315", "name": "Grupos de despesa"},
        {"code": "12086", "name": "Tipos de despesa"},
        {"code": "12087", "name": "Subitens de despesa"},
        {"code": "12088", "name": "Categorias POF"},
    ]
    
    successful_classifications = []
    
    for class_test in classification_tests:
        print(f"\n🔍 Testando classificação {class_test['code']}: {class_test['name']}")
        
        try:
            # Testa com a classificação
            data = sidrapy.get_table(
                table_code=table_code,
                territorial_level="1",
                ibge_territorial_code="all",
                classifications={class_test["code"]: "all"}
            )
            
            if data is not None and len(data) > 0:
                df = pd.DataFrame(data)
                data_df = df[df['V'] != 'Valor']
                
                if len(data_df) > 0:
                    print(f"   ✅ Sucesso! {len(data_df)} registros com classificação")
                    
                    # Procura pela coluna da classificação
                    class_columns = [col for col in df.columns if col.endswith('N') and not col.startswith('D3')]
                    for col in class_columns:
                        categories = data_df[col].unique()
                        if len(categories) > 1:
                            print(f"      📋 {col}: {len(categories)} categorias")
                            # Mostra algumas categorias
                            for cat in categories[:8]:
                                print(f"         - {cat}")
                            if len(categories) > 8:
                                print(f"         ... mais {len(categories) - 8}")
                    
                    successful_classifications.append({
                        **class_test,
                        "records": len(data_df),
                        "columns": list(df.columns)
                    })
                else:
                    print(f"   ⚠️ Apenas headers")
            else:
                print(f"   ❌ Sem dados")
                
        except Exception as e:
            error_msg = str(e)
            if "incompatível" in error_msg or "inexistente" in error_msg:
                print(f"   ❌ Classificação não existe nesta tabela")
            else:
                print(f"   ❌ Erro: {error_msg}")
    
    return successful_classifications

if __name__ == "__main__":
    print("🏠 BUSCA POR TABELAS POF OFICIAIS REAIS")
    print("=" * 50)
    
    # 1. Encontra tabelas POF oficiais
    pof_tables = find_real_pof_tables()
    
    # 2. Analisa estrutura da tabela de despesas (se encontrada)
    expense_analysis = None
    if any(t["code"] == "9055" for t in pof_tables):
        expense_analysis = analyze_pof_expense_structure("9055")
    
    # 3. Testa classificações
    classifications = []
    if any(t["code"] == "9055" for t in pof_tables):
        classifications = test_pof_classifications("9055")
    
    # 4. Compila resultados
    results = {
        "official_pof_tables": pof_tables,
        "expense_structure": expense_analysis,
        "successful_classifications": classifications,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Salva resultados
    with open("official_pof_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n📋 RESUMO FINAL:")
    print(f"   📊 Tabelas POF oficiais encontradas: {len(pof_tables)}")
    if pof_tables:
        for table in pof_tables:
            print(f"      ✅ {table['code']}: {table['name']} ({table.get('data_records', 0)} registros)")
    
    print(f"   🔬 Análise de estrutura: {'✅ Concluída' if expense_analysis else '❌ N/A'}")
    print(f"   🎯 Classificações testadas: {len(classifications)} funcionais")
    
    print(f"   💾 Resultados detalhados salvos em: official_pof_results.json")
    
    if pof_tables:
        print(f"\n🎯 PRÓXIMO PASSO: Implementar integração com dados POF reais!")
