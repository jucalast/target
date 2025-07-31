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
        print("Para ver um exemplo com classificações,\
            descomente o código no script.")
        print("Para consultar a tabela 5918,\
            você precisará obter os códigos corretos de classificação.")
        # Exemplo de consulta à tabela 1419 (IPCA - Índice de Preços ao Consumidor Amplo)
        # Este é um exemplo da documentação oficial que sabemos que funciona
        table_code = "1419"  # IPCA
        territorial_level = "1"  # 1 = Brasil
        ibge_territorial_code =\
            "all"  # Todos os códigos territoriais do nível especificado
        variable = "63"  # Índice geral
        period = "last 12"  # Últimos 12 meses
        print(f"\nConsultando tabela {table_code} (\
            IPCA) com os seguintes parâmetros:")
        print(f"- Nível territorial: {territorial_level}")
        print(f"- Código territorial: {ibge_territorial_code}")
        print(f"- Variável: {variable}")
        print(f"- Período: {period}")
        # Fazer a consulta sem classificações para simplificar
        data = sidrapy.get_table(
            table_code=table_code,
            territorial_level=territorial_level,
            ibge_territorial_code=ibge_territorial_code,
            variable=variable,
            period=period
        )
        # Exemplo de como adicionar classificações (descomente para usar)
        # classifications = {
        #     "315": "7169,7170,7171,7172,7173,7174,7175,7176,7177,7178,7179,7180,7181,7445,7486,7487,7558,7625,7660,7712,7766,7786,7817,7846,7935,7941"
        # }
        #
        # data_with_classifications = sidrapy.get_table(
        #     table_code=table_code,
        #     territorial_level=territorial_level,
        #     ibge_territorial_code=ibge_territorial_code,
        #     variable=variable,
        #     period=period,
        #     classifications=classifications
        # )
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
