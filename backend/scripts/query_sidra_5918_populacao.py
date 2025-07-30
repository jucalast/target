"""
Script para consultar a tabela 5918 (População, por grupo de idade) do SIDRA/IBGE.

Este script demonstra como fazer uma consulta à tabela 5918 usando a biblioteca sidrapy.
"""
import sidrapy
import pandas as pd

def query_populacao_por_idade():
    """
    Consulta a tabela 5918 (População, por grupo de idade) do SIDRA/IBGE.
    
    Retorna:
        DataFrame com os dados da consulta
    """
    try:
        print("Consultando a tabela 5918 (População, por grupo de idade) do SIDRA/IBGE...")
        
        # Parâmetros da consulta
        table_code = "5918"  # Tabela de População por Grupo de Idade
        territorial_level = "1"  # 1 = Brasil
        ibge_territorial_code = "all"  # Todos os códigos territoriais do nível especificado
        variable = "93"  # População residente
        period = "last"  # Último período disponível
        
        # Classificação por grupo de idade (C1)
        # Valores baseados na documentação do SIDRA para a tabela 5918
        # Cada número representa um grupo etário específico
        classifications = {
            "1": "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17"
        }
        
        print(f"\nConsultando tabela {table_code} com os seguintes parâmetros:")
        print(f"- Nível territorial: {territorial_level}")
        print(f"- Código territorial: {ibge_territorial_code}")
        print(f"- Variável: {variable}")
        print(f"- Período: {period}")
        print(f"- Classificações: {classifications}")
        
        # Fazer a consulta
        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level=territorial_level,
            ibge_territorial_code=ibge_territorial_code,
            variable=variable,
            period=period,
            classifications=classifications
        )
        
        # Converter para DataFrame
        df = pd.DataFrame(data)
        
        # Exibir as primeiras linhas do resultado
        print("\nPrimeiras linhas do resultado:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Erro ao consultar a tabela: {str(e)}")
        return None

if __name__ == "__main__":
    print("Iniciando consulta à tabela de população por grupo de idade...")
    df = query_populacao_por_idade()
    
    if df is not None and not df.empty:
        print("\nConsulta concluída com sucesso!")
        print("\nColunas disponíveis no resultado:")
        print(df.columns.tolist())
        print(f"\nTotal de registros retornados: {len(df)}")
    else:
        print("\nNão foi possível obter os dados da tabela.")
    
    print("\nDica: Consulte a documentação da API SIDRA para obter mais informações sobre os parâmetros disponíveis:")
    print("https://sidra.ibge.gov.br/tabela/5918")
