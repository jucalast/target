"""
Script para descobrir tabelas PNAD disponíveis na API SIDRA do IBGE.

A PNAD (Pesquisa Nacional por Amostra de Domicílios) complementa os dados da POF
com informações sobre educação, trabalho, rendimento e características demográficas.
"""
import sidrapy
import pandas as pd
import logging
import json
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def discover_pnad_tables() -> Dict[str, Any]:
    """
    Descobre e testa tabelas PNAD disponíveis na API SIDRA.
    
    Returns:
        Dicionário com tabelas PNAD funcionais e seus metadados
    """
    # Tabelas PNAD conhecidas por categoria
    pnad_tables = {
        'educacao': [
            '2511',  # Pessoas de 4 anos ou mais de idade por grupos de idade e nível de instrução
            '2512',  # Pessoas de 25 anos ou mais de idade por grupos de idade e nível de instrução
            '2513',  # Taxa de analfabetismo das pessoas de 15 anos ou mais de idade
        ],
        'trabalho_renda': [
            '4093',  # Pessoas de 14 anos ou mais de idade por condição na força de trabalho
            '4094',  # Pessoas de 14 anos ou mais de idade ocupadas por posição na ocupação
            '4095',  # Rendimento médio real habitualmente recebido do trabalho principal
        ],
        'domicilios': [
            '2094',  # Domicílios particulares permanentes por situação do domicílio
            '2095',  # Domicílios particulares permanentes por tipo de domicílio
            '2096',  # Domicílios particulares permanentes por material predominante na construção
        ],
        'caracteristicas_demograficas': [
            '2093',  # População residente por cor ou raça
            '200',   # População residente por sexo e grupos de idade
            '201',   # População residente urbana e rural por sexo
        ]
    }
    
    working_tables = {}
    failed_tables = {}
    
    logger.info("🔍 Descobrindo tabelas PNAD na API SIDRA...")
    
    for category, table_codes in pnad_tables.items():
        logger.info(f"\n📊 Testando categoria: {category}")
        working_tables[category] = []
        
        for table_code in table_codes:
            try:
                logger.info(f"   🔗 Testando tabela {table_code}...")
                
                # Tenta consultar a tabela
                data = sidrapy.get_table(
                    table_code=table_code,
                    territorial_level="1",  # Brasil
                    ibge_territorial_code="all",
                    period="last"  # Último período disponível
                )
                
                if data and len(data) > 1:
                    df = pd.DataFrame(data)
                    
                    # Remove linhas de cabeçalho
                    data_df = df[df['V'] != 'Valor'].copy()
                    
                    table_info = {
                        'code': table_code,
                        'total_rows': len(data_df),
                        'columns': list(df.columns),
                        'sample_data': data_df.head(3).to_dict('records') if len(data_df) > 0 else [],
                        'status': 'working'
                    }
                    
                    working_tables[category].append(table_info)
                    logger.info(f"   ✅ Tabela {table_code}: {len(data_df)} registros")
                    
                else:
                    failed_tables[table_code] = "Dados vazios ou inválidos"
                    logger.warning(f"   ⚠️ Tabela {table_code}: sem dados válidos")
                    
            except Exception as e:
                failed_tables[table_code] = str(e)
                logger.error(f"   ❌ Tabela {table_code}: {str(e)}")
    
    # Summary
    total_working = sum(len(tables) for tables in working_tables.values())
    total_failed = len(failed_tables)
    
    logger.info(f"\n📈 RESULTADO DA DESCOBERTA PNAD:")
    logger.info(f"   ✅ Tabelas funcionais: {total_working}")
    logger.info(f"   ❌ Tabelas com erro: {total_failed}")
    
    for category, tables in working_tables.items():
        if tables:
            logger.info(f"   📊 {category}: {len(tables)} tabelas")
            for table in tables:
                logger.info(f"      - {table['code']}: {table['total_rows']} registros")
    
    return {
        'working_tables': working_tables,
        'failed_tables': failed_tables,
        'summary': {
            'total_working': total_working,
            'total_failed': total_failed,
            'categories': list(working_tables.keys())
        }
    }

def save_pnad_discovery_results(results: Dict[str, Any]) -> str:
    """Salva os resultados da descoberta em arquivo JSON."""
    filename = "pnad_discovery_results.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"💾 Resultados salvos em: {filename}")
    return filename

if __name__ == "__main__":
    try:
        logger.info("🚀 Iniciando descoberta de tabelas PNAD...")
        results = discover_pnad_tables()
        
        # Salva resultados
        save_pnad_discovery_results(results)
        
        logger.info("✅ Descoberta PNAD concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro na descoberta PNAD: {str(e)}")
        raise
