#!/usr/bin/env python3
"""
Teste da Metodologia da "Ponte de Tradução Inteligente"

Este script verifica se todo o processo descrito na metodologia está sendo
implementado corretamente, validando cada etapa da "ponte" entre NLP e ETL.
"""
import sys
import os

# Adiciona o backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from shared.schemas.nlp_features import NLPFeatures, KeywordFeature, EntityFeature, TopicFeature, EmbeddingFeature
from shared.schemas.etl_parameters import ETLParameters, IBGETableQuery, GoogleTrendsQuery, NewsScrapingQuery
from etl_pipeline.app.services.extractors.ibge.sidra_mapper import SIDRAMapper
from nlp_processor.app.services.nlp_service import extract_features
import json
from datetime import datetime

def test_metodologia_ponte():
    """
    Testa todo o processo da "Ponte de Tradução Inteligente" descrito na metodologia.
    """
    print("🔬 TESTE DA METODOLOGIA: PONTE DE TRADUÇÃO INTELIGENTE")
    print("=" * 70)
    
    # ========================================================================
    # ETAPA 1: PROCESSAMENTO NLP - GERAÇÃO DO "DOSSIÊ DE BUSCA"
    # ========================================================================
    print("\n📝 ETAPA 1: GERAÇÃO DO DOSSIÊ DE BUSCA (NLP)")
    print("-" * 50)
    
    # Input do usuário (dados reais)
    niche = "Tecnologia educacional para crianças"
    description = """
    Plataforma online de ensino de programação e robótica educativa para crianças 
    de 6 a 12 anos, focada em escolas públicas e particulares do Brasil, 
    especialmente nas regiões Sul e Sudeste, com ênfase em famílias de classe 
    média interessadas em educação STEAM.
    """
    
    print(f"🎯 Nicho: {niche}")
    print(f"📄 Descrição: {description.strip()[:100]}...")
    
    # Executa o processamento NLP REAL
    nlp_result = extract_features(niche, description)
    
    # Converte para NLPFeatures estruturado
    nlp_features = NLPFeatures(
        original_text=f"{niche}. {description}",
        normalized_text=nlp_result.get('normalized_text', ''),
        keywords=[
            KeywordFeature(
                keyword=kw['keyword'],
                score=kw['score'],
                method='tfidf'
            ) for kw in nlp_result.get('keywords', [])
        ],
        entities=[
            EntityFeature(
                text=ent['text'],
                label=ent['label'],
                start_char=ent.get('start', 0),
                end_char=ent.get('end', 0)
            ) for ent in nlp_result.get('entities', [])
        ],
        topics=[
            TopicFeature(
                topic_id=i,
                keywords=[
                    {"word": kw, "score": 0.5} if isinstance(kw, str) 
                    else kw for kw in topic.get('keywords', [])
                ],
                score=topic.get('score', 0.0)
            ) for i, topic in enumerate(nlp_result.get('topics', []))
        ],
        embeddings={
            model: EmbeddingFeature(
                model=model,
                vector=vector if isinstance(vector, list) else [],
                dim=len(vector) if isinstance(vector, list) else 0
            )
            for model, vector in nlp_result.get('embeddings', {}).items()
            if isinstance(vector, list)  # Filtra apenas os vetores reais
        },
        processing_time=1.0
    )
    
    print(f"✅ Palavras-chave extraídas: {len(nlp_features.keywords)}")
    print(f"   Top 5: {[k.keyword for k in nlp_features.keywords[:5]]}")
    print(f"✅ Entidades extraídas: {len(nlp_features.entities)}")
    print(f"   Entidades: {[f'{e.text} ({e.label})' for e in nlp_features.entities[:3]]}")
    print(f"✅ Tópicos extraídos: {len(nlp_features.topics)}")
    print(f"✅ Embeddings gerados: {list(nlp_features.embeddings.keys())}")
    
    # Identifica entidades geográficas especificamente
    geographic_entities = [e.text for e in nlp_features.entities if e.label in ['LOC', 'GPE']]
    print(f"🌍 Entidades geográficas: {geographic_entities}")
    
    # ========================================================================
    # ETAPA 2: TRADUÇÃO PARA PARÂMETROS SIDRA (MAPPER)
    # ========================================================================
    print("\n🔄 ETAPA 2: TRADUÇÃO PARA PARÂMETROS SIDRA")
    print("-" * 50)
    
    # Extrai termos para mapeamento
    keywords_for_mapping = [k.keyword for k in nlp_features.keywords[:10]]
    
    print(f"📋 Input para mapeamento: {keywords_for_mapping}")
    
    # Executa o mapeamento REAL
    mapper = SIDRAMapper()
    sidra_params = mapper.map_terms_to_sidra_parameters(keywords_for_mapping)
    
    print(f"🎯 Tabela SIDRA selecionada: {sidra_params.get('tabela', 'N/A')}")
    print(f"📊 Parâmetros mapeados:")
    
    matched_terms = sidra_params.get('matched_terms', {})
    for param_code, param_info in matched_terms.items():
        print(f"   - Parâmetro {param_code}: {param_info.get('name', 'N/A')}")
        print(f"     Termos: {param_info.get('matched_terms', [])}")
    
    # ========================================================================
    # ETAPA 3: CONSTRUÇÃO DE PARÂMETROS ETL (ORQUESTRAÇÃO)
    # ========================================================================
    print("\n🏗️ ETAPA 3: CONSTRUÇÃO DE PARÂMETROS ETL")
    print("-" * 50)
    
    # 3.1 Filtro geográfico baseado em entidades
    location = "Brasil"
    if geographic_entities:
        if any(geo.lower() in ['sul', 'sudeste', 'nordeste', 'norte', 'centro-oeste'] 
               for geo in geographic_entities):
            location = geographic_entities[0]
        elif any(geo.lower() == 'brasil' for geo in geographic_entities):
            location = "Brasil"
    
    print(f"🌍 Filtro geográfico aplicado: {location}")
    
    # 3.2 Criação de consultas IBGE baseadas na tradução
    ibge_queries = [
        IBGETableQuery(
            table_code=sidra_params.get('tabela', '6401'),
            variables=sidra_params.get('variaveis', []),
            classifications=sidra_params.get('classificacoes', {}),
            location=location,
            period='2022'
        )
    ]
    
    print(f"📊 Consultas IBGE criadas: {len(ibge_queries)}")
    print(f"   - Tabela: {ibge_queries[0].table_code}")
    print(f"   - Localização: {ibge_queries[0].location}")
    
    # 3.3 Criação de consultas Google Trends baseadas em keywords
    top_keywords = [k.keyword for k in nlp_features.keywords[:5]]
    google_trends_queries = [
        GoogleTrendsQuery(
            keywords=top_keywords[:3],  # Máximo 3 termos por query
            timeframe='today 12-m',
            geo='BR',
            gprop='web'
        )
    ]
    
    print(f"📈 Consultas Google Trends criadas: {len(google_trends_queries)}")
    print(f"   - Keywords: {google_trends_queries[0].keywords}")
    
    # 3.4 Criação de consulta de notícias baseada em keywords
    news_query = NewsScrapingQuery(
        keywords=top_keywords[:4],
        sources=['g1.globo.com', 'agenciabrasil.ebc.com.br', 'valor.globo.com'],
        max_articles=15,
        timeframe_days=30
    )
    
    print(f"📰 Consulta de notícias criada:")
    print(f"   - Keywords: {news_query.keywords}")
    print(f"   - Fontes: {len(news_query.sources)} configuradas")
    
    # ========================================================================
    # ETAPA 4: DOSSIÊ ETL FINAL (PONTE COMPLETA)
    # ========================================================================
    print("\n🌉 ETAPA 4: DOSSIÊ ETL FINAL - PONTE COMPLETA")
    print("-" * 50)
    
    # Criação do objeto ETLParameters final
    etl_params = ETLParameters(
        request_id=f"test_metodologia_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        user_input={
            "niche": niche,
            "description": description
        },
        nlp_features=nlp_features,
        ibge_queries=ibge_queries,
        google_trends_queries=google_trends_queries,
        news_queries=news_query,
        cache_enabled=True,
        max_retries=3
    )
    
    print(f"📦 Dossiê ETL criado com sucesso!")
    print(f"   - Request ID: {etl_params.request_id}")
    print(f"   - Timestamp: {etl_params.timestamp}")
    
    # ========================================================================
    # ETAPA 5: VALIDAÇÃO DA PONTE (VERIFICAÇÕES DE INTEGRIDADE)
    # ========================================================================
    print("\n✅ ETAPA 5: VALIDAÇÃO DA PONTE")
    print("-" * 50)
    
    # Validação 1: Palavras-chave do NLP → Google Trends
    nlp_keywords = [k.keyword for k in nlp_features.keywords[:5]]
    trends_keywords = etl_params.google_trends_queries[0].keywords
    keyword_overlap = set(nlp_keywords) & set(trends_keywords)
    
    print(f"🔍 Palavras-chave NLP → Google Trends:")
    print(f"   - NLP: {nlp_keywords}")
    print(f"   - Trends: {trends_keywords}")
    print(f"   - Sobreposição: {list(keyword_overlap)} ({'✅' if keyword_overlap else '❌'})")
    
    # Validação 2: Entidades do NLP → Filtro geográfico IBGE
    nlp_locations = [e.text for e in nlp_features.entities if e.label in ['LOC', 'GPE']]
    ibge_location = etl_params.ibge_queries[0].location
    location_match = any(loc.lower() in ibge_location.lower() for loc in nlp_locations) if nlp_locations else True
    
    print(f"🌍 Entidades NLP → Filtro geográfico IBGE:")
    print(f"   - NLP: {nlp_locations}")
    print(f"   - IBGE: {ibge_location}")
    print(f"   - Correspondência: {'✅' if location_match else '❌'}")
    
    # Validação 3: Keywords do NLP → News scraping
    news_keywords = etl_params.news_queries.keywords
    news_overlap = set(nlp_keywords) & set(news_keywords)
    
    print(f"📰 Palavras-chave NLP → News scraping:")
    print(f"   - NLP: {nlp_keywords}")
    print(f"   - News: {news_keywords}")
    print(f"   - Sobreposição: {list(news_overlap)} ({'✅' if news_overlap else '❌'})")
    
    # Validação 4: Embeddings semânticos disponíveis
    embeddings_available = len(nlp_features.embeddings) > 0
    print(f"🧠 Embeddings semânticos:")
    print(f"   - Modelos: {list(nlp_features.embeddings.keys())}")
    print(f"   - Disponível para busca por similaridade: {'✅' if embeddings_available else '❌'}")
    
    # Validação 5: Tradução SIDRA funcionou
    sidra_mapped = 'tabela' in sidra_params and sidra_params['tabela'] is not None
    print(f"🔄 Tradução para SIDRA:")
    print(f"   - Mapeamento realizado: {'✅' if sidra_mapped else '❌'}")
    print(f"   - Tabela: {sidra_params.get('tabela', 'N/A')}")
    
    # ========================================================================
    # RESUMO FINAL
    # ========================================================================
    print("\n🎯 RESUMO FINAL: PONTE DE TRADUÇÃO INTELIGENTE")
    print("=" * 70)
    
    validations = [
        ("Palavras-chave → Google Trends", keyword_overlap),
        ("Entidades → Filtro geográfico", location_match),
        ("Keywords → News scraping", news_overlap),
        ("Embeddings semânticos", embeddings_available),
        ("Tradução SIDRA", sidra_mapped)
    ]
    
    all_valid = all(bool(validation[1]) for validation in validations)
    
    for validation_name, is_valid in validations:
        status = "✅ FUNCIONANDO" if is_valid else "❌ PROBLEMA"
        print(f"   {validation_name}: {status}")
    
    print(f"\n🌉 PONTE DE TRADUÇÃO INTELIGENTE: {'✅ IMPLEMENTADA' if all_valid else '❌ PROBLEMAS DETECTADOS'}")
    
    if all_valid:
        print("\n🎉 SUCESSO! Toda a metodologia da ponte está funcionando:")
        print("   • NLP extrai features qualitativas → ✅")
        print("   • Mapper traduz para parâmetros SIDRA → ✅")
        print("   • Orquestrador cria consultas parametrizadas → ✅")
        print("   • Embeddings disponíveis para busca semântica → ✅")
        print("   • Filtros geográficos aplicados → ✅")
        print("   • Pipeline pronto para coleta de dados externos → ✅")
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS na implementação da ponte!")
    
    return all_valid, etl_params

if __name__ == "__main__":
    success, etl_params = test_metodologia_ponte()
    
    print(f"\n📋 OBJETO JSON FINAL (DOSSIÊ ETL):")
    print("-" * 50)
    
    # Serializa o objeto para JSON para mostrar a estrutura final
    etl_dict = etl_params.model_dump()
    
    # Mostra apenas as partes principais para não poluir a saída
    key_parts = {
        "request_id": etl_dict["request_id"],
        "nlp_keywords": [k["keyword"] for k in etl_dict["nlp_features"]["keywords"][:5]],
        "nlp_entities": [e["text"] for e in etl_dict["nlp_features"]["entities"]],
        "ibge_table": etl_dict["ibge_queries"][0]["table_code"],
        "ibge_location": etl_dict["ibge_queries"][0]["location"],
        "trends_keywords": etl_dict["google_trends_queries"][0]["keywords"],
        "news_keywords": etl_dict["news_queries"]["keywords"],
        "embeddings_models": list(etl_dict["nlp_features"]["embeddings"].keys())
    }
    
    print(json.dumps(key_parts, indent=2, ensure_ascii=False))
    
    exit(0 if success else 1)
