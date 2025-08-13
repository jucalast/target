#!/usr/bin/env python3
"""
Script para debug da inconsistência psicográfica.
Identifica o problema onde arquétipo 'Experiencialista' tem experience_seeking=False.
"""

import logging
import sys
import os

# Configuração do logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Adiciona o caminho do backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from etl_pipeline.app.services.analyzers.psychographic_analyzer import PsychographicAnalyzer

def main():
    print("🔍 DEBUG: Inconsistência Psicográfica - Experiencialista vs experience_seeking")
    print("="*80)
    
    # Inicializa o analisador
    analyzer = PsychographicAnalyzer()
    
    # Analisa um segmento de teste
    segment_name = "Debug_tecnologia_mercado"
    keywords = ["tecnologia", "mercado", "analise", "jovens"]
    
    print(f"📊 Analisando segmento: {segment_name}")
    print(f"🔑 Keywords: {keywords}")
    print()
    
    try:
        # Executa a análise
        profile = analyzer.analyze_segment(segment_name, keywords)
        
        print("✅ ANÁLISE CONCLUÍDA")
        print("="*50)
        print(f"🎯 Arquétipo: {profile.archetype}")
        print(f"😊 Sentimento: {profile.sentiment_index}")
        print(f"💰 Total gastos: R$ {profile.spending_pattern['total']:.2f}")
        print()
        
        print("📊 PERCENTUAIS POR CATEGORIA:")
        categories = profile.spending_pattern['categories']
        for code, percentage in sorted(categories.items()):
            category_name = {
                '114023': 'Habitação', 
                '114024': 'Alimentação', 
                '114025': 'Saúde',
                '114027': 'Recreação/Cultura', 
                '114031': 'Transporte'
            }.get(code, f'Categoria {code}')
            print(f"   {code} ({category_name}): {percentage:.2f}%")
        
        print()
        print("🔍 INDICADORES COMPORTAMENTAIS:")
        behavior = profile.spending_pattern['behavior_indicators']
        for indicator, value in behavior.items():
            status = "✅" if value else "❌"
            print(f"   {status} {indicator}: {value}")
        
        print()
        print("🚨 DETECÇÃO DE INCONSISTÊNCIA:")
        is_experiencialista = profile.archetype == "Experiencialista"
        experience_seeking = behavior.get('experience_seeking', False)
        
        if is_experiencialista and not experience_seeking:
            recreacao_pct = categories.get('114027', 0)
            print(f"❌ INCONSISTÊNCIA DETECTADA!")
            print(f"   - Arquétipo: {profile.archetype}")
            print(f"   - experience_seeking: {experience_seeking}")
            print(f"   - Recreação/Cultura: {recreacao_pct:.2f}% (limite: 5%)")
            print(f"   - CAUSA: Gastos com recreação abaixo do limite!")
        else:
            print(f"✅ Consistência OK")
        
        print()
        print("💡 RECOMENDAÇÃO:")
        if is_experiencialista and not experience_seeking:
            print("   O algoritmo deve considerar outros fatores além dos gastos POF")
            print("   para determinar experience_seeking em perfis Experiencialistas,")
            print("   como keywords ('tecnologia', 'inovacao') e lifestyle indicators.")
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        logger.exception("Erro detalhado:")

if __name__ == "__main__":
    main()
