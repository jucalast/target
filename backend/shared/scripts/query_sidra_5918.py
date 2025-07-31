"""
Script de exemplo para consultar a API SIDRA do IBGE usando a biblioteca sidrapy.

Este script demonstra como fazer uma consulta simples à API SIDRA.
"""

def query_sidra_example():
"""
    Exemplo de consulta à API SIDRA usando a biblioteca sidrapy.
    Retorna:
    DataFrame com os dados da consulta
    """
    try:
    print("Exemplo de consulta à API SIDRA usando a biblioteca sidrapy...")
        print("Este exemplo consulta a tabela do IPCA (\
            1419) sem classificações.")
        print("Para ver um exemplo com classificações, \
            descomente o código no script.")
        print("Para consultar a tabela 5918, \
            você precisará obter os códigos corretos de classificação.")

        table_code = "1419"
        territorial_level = "1"
        ibge_territorial_code =\
            "all"
        variable = "63"
        period = "last 12"
        print(f"\nConsultando tabela {table_code} (\
            IPCA) com os seguintes parâmetros:")
        print(f"- Nível territorial: {territorial_level}")
        print(f"- Código territorial: {ibge_territorial_code}")
        print(f"- Variável: {variable}")
        print(f"- Período: {period}")

        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level=territorial_level,
            ibge_territorial_code=ibge_territorial_code,
            variable=variable,
            period=period
        )

        df = pd.DataFrame(data)

        print("\nPrimeiras linhas do resultado:")
        print(df.head())
        return df
    except Exception as e:
    print(f"Erro ao consultar a tabela: {str(e)}")
        return None
if __name__ == "__main__":
print("Iniciando consulta à API SIDRA...")
    df = query_sidra_example()
    if df is not None and not df.empty:
    print("\nConsulta concluída com sucesso!")
        print("\nPrimeiras linhas do resultado:")
        print(df.head())
        print(f"\nTotal de registros retornados: {len(df)}")
    else:
    print("\nNão foi possível obter os dados da tabela.")
    print(\
        "\nDica: Consulte a documentação da API SIDRA para obter mais informações sobre os parâmetros disponíveis:")
    print("https://sidra.ibge.gov.br/home/ajuda")
