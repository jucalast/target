"""
Script para identificar e verificar as tabelas POF disponíveis na API SIDRA.

Este script busca tabelas relacionadas à Pesquisa de Orçamentos Familiares (POF)
para usar na análise psicográfica real.
"""
import sidrapy
import pandas as pd
from typing import List, Dict, Any
import json

def check_pof_tables() -> Dict[str, Any]:
    """
    Verifica tabelas POF disponíveis e suas estruturas.
    
    Returns:
        Dicionário com informações das tabelas POF encontradas
    """
    # Tabelas POF conhecidas do IBGE (baseado na documentação oficial)
    pof_tables = {
        "7482": {
            "name": "POF - Despesas monetárias e não monetárias médias mensais familiares",
            "description": "Despesas familiares por categoria",
            "variables": ["214", "1752"],  # Valor e percentual
            "key_classification": "315"  # Grupos de despesa
        },
        "7483": {
            "name": "POF - Despesas com alimentação no domicílio",
            "description": "Despesas específicas com alimentação",
            "variables": ["214"],
            "key_classification": "315"
        },
        "9050": {
            "name": "POF - Aquisição de bens duráveis",
            "description": "Bens duráveis adquiridos pelas famílias",
            "variables": ["2380"],  # Número de famílias
            "key_classification": "638"  # Tipos de bens duráveis
        },
        "9052": {
            "name": "POF - Avaliação das condições de vida",
            "description": "Percepção das famílias sobre suas condições",
            "variables": ["2380"],
            "key_classification": "640"  # Avaliação de aspectos da vida
        }
    }
    
    print("🔍 Verificando disponibilidade das tabelas POF...")
    available_tables = {}
    
    for table_code, table_info in pof_tables.items():
        print(f"\n📊 Testando tabela {table_code}: {table_info['name']}")
        
        try:
            # Teste com consulta simples - Brasil, última pesquisa disponível
            test_data = sidrapy.get_table(
                table_code=table_code,
                territorial_level="1",  # Brasil
                ibge_territorial_code="all",
                variable=table_info["variables"][0],
                period="last 1"  # Último período
            )
            
            if test_data:
                df = pd.DataFrame(test_data)
                print(f"   ✅ Disponível - {len(df)} registros encontrados")
                print(f"   📅 Período: {df['D3N'].iloc[0] if 'D3N' in df.columns else 'N/A'}")
                
                available_tables[table_code] = {
                    **table_info,
                    "status": "available",
                    "sample_data": df.head(3).to_dict('records'),
                    "total_records": len(df),
                    "columns": list(df.columns)
                }
            else:
                print(f"   ❌ Sem dados retornados")
                available_tables[table_code] = {
                    **table_info,
                    "status": "no_data"
                }
                
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            available_tables[table_code] = {
                **table_info,
                "status": "error",
                "error": str(e)
            }
    
    return available_tables

def get_expense_categories(table_code: str = "7482") -> List[Dict[str, Any]]:
    """
    Obtém as categorias de despesa disponíveis na tabela POF.
    
    Args:
        table_code: Código da tabela POF de despesas
        
    Returns:
        Lista com as categorias de despesa e seus códigos
    """
    print(f"\n🏷️ Obtendo categorias de despesa da tabela {table_code}...")
    
    try:
        # Consulta com classificação para ver todas as categorias
        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level="1",
            ibge_territorial_code="all",
            variable="214",  # Valor
            period="last 1",
            classifications={"315": "all"}  # Todas as categorias de despesa
        )
        
        if data:
            df = pd.DataFrame(data)
            
            # Extrai informações das categorias
            categories = []
            if 'D2C' in df.columns and 'D2N' in df.columns:
                category_info = df[['D2C', 'D2N']].drop_duplicates()
                for _, row in category_info.iterrows():
                    categories.append({
                        "code": row['D2C'],
                        "name": row['D2N'],
                        "table": table_code
                    })
            
            print(f"   ✅ {len(categories)} categorias encontradas")
            return categories
        else:
            print(f"   ❌ Nenhuma categoria encontrada")
            return []
            
    except Exception as e:
        print(f"   ❌ Erro ao obter categorias: {str(e)}")
        return []

def test_real_pof_query() -> Dict[str, Any]:
    """
    Testa uma consulta real de dados POF para uso na análise psicográfica.
    
    Returns:
        Dados POF estruturados para análise
    """
    print("\n🧪 Testando consulta POF real para análise psicográfica...")
    
    try:
        # Consulta despesas familiares principais - Brasil
        despesas_data = sidrapy.get_table(
            table_code="7482",
            territorial_level="1",
            ibge_territorial_code="all",
            variable="214",  # Valor em reais
            period="last 1",
            classifications={
                "315": ["114023", "114024", "114025", "114027", "114029", "114030", "114031", "114032"]
                # Habitação, Alimentação, Saúde, Recreação, Educação, Vestuário, Transporte, Comunicação
            }
        )
        
        if despesas_data:
            df_despesas = pd.DataFrame(despesas_data)
            print(f"   ✅ Dados de despesas obtidos: {len(df_despesas)} registros")
            
            # Estrutura os dados para análise psicográfica
            despesas_dict = {}
            for _, row in df_despesas.iterrows():
                if 'D2C' in row and 'V' in row:
                    categoria_code = str(row['D2C'])
                    valor = float(row['V']) if pd.notna(row['V']) else 0.0
                    despesas_dict[categoria_code] = valor
            
            print(f"   📊 Categorias mapeadas: {list(despesas_dict.keys())}")
            
            return {
                "despesas": despesas_dict,
                "periodo": df_despesas['D3N'].iloc[0] if 'D3N' in df_despesas.columns else "N/A",
                "fonte": "POF-IBGE",
                "tabela": "7482",
                "status": "success"
            }
        else:
            return {"status": "no_data", "error": "Nenhum dado retornado"}
            
    except Exception as e:
        print(f"   ❌ Erro na consulta: {str(e)}")
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    print("🏠 VERIFICAÇÃO DE TABELAS POF PARA ANÁLISE PSICOGRÁFICA")
    print("=" * 60)
    
    # 1. Verifica disponibilidade das tabelas
    tables_info = check_pof_tables()
    
    # 2. Obtém categorias de despesa
    categories = get_expense_categories()
    
    # 3. Testa consulta real
    real_data = test_real_pof_query()
    
    # 4. Salva resultados para análise
    results = {
        "tables_availability": tables_info,
        "expense_categories": categories,
        "sample_real_data": real_data,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Salva em arquivo para uso posterior
    with open("pof_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 RESUMO:")
    print(f"   - Tabelas verificadas: {len(tables_info)}")
    print(f"   - Tabelas disponíveis: {sum(1 for t in tables_info.values() if t.get('status') == 'available')}")
    print(f"   - Categorias de despesa: {len(categories)}")
    print(f"   - Dados de teste: {'✅ Sucesso' if real_data.get('status') == 'success' else '❌ Erro'}")
    print(f"   - Resultados salvos em: pof_analysis_results.json")
    
    if real_data.get("status") == "success":
        print(f"\n💰 DADOS REAIS OBTIDOS:")
        despesas = real_data.get("despesas", {})
        for codigo, valor in despesas.items():
            print(f"   - {codigo}: R$ {valor:,.2f}")
