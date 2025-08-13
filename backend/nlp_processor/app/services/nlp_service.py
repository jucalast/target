import spacy
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from collections import Counter

# Bibliotecas para TF-IDF e LDA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction import text 
from sklearn.metrics.pairwise import cosine_similarity

# Carregando o modelo de linguagem do spaCy para português
try:
    nlp = spacy.load("pt_core_news_lg")
except OSError:
    print("Modelo 'pt_core_news_lg' não encontrado. Execute 'python -m spacy download pt_core_news_lg'")
    nlp = None

# Carregando o modelo de embeddings BERT
try:
    from sentence_transformers import SentenceTransformer
    BERT_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    BERT_DIM = 384  # Dimensão dos embeddings do modelo
    BERT_AVAILABLE = True
except ImportError:
    print("Aviso: sentence-transformers não está instalado. Recursos de BERT desativados.")
    BERT_AVAILABLE = False
    BERT_DIM = 0

# Configuração de stop words personalizadas
PORTUGUESE_STOP_WORDS = list(text.ENGLISH_STOP_WORDS.union({
    'a', 'o', 'e', 'é', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com',
    'não', 'se', 'que', 'por', 'como', 'mais', 'mas', 'ao', 'das', 'dos',
    'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'nos', 'já', 'eu',
    'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'depois',
    'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem', 'nos', 'está', 'você',
    'lhe', 'deles', 'essa', 'num', 'nem', 'suas', 'meu', 'às', 'qual', 'nós',
    'lhe', 'deles', 'essas', 'esses', 'pelos', 'elas', 'qual', 'nós', 'lhe',
    'deles', 'vocês', 'vocês', 'lhes', 'meus', 'minha', 'teu', 'tua', 'teus',
    'tuas', 'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta',
    'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'aquilo'
}))

def normalize_text(text: str) -> str:
    """
    Normaliza o texto para minúsculas, remove acentos e caracteres especiais.
    
    Args:
        text: Texto a ser normalizado
        
    Returns:
        Texto normalizado
    """
    import unicodedata
    import re
    
    # Converte para minúsculas
    text = text.lower()
    
    # Remove acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove caracteres especiais, mantendo apenas letras, números e espaços
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove espaços extras
    text = ' '.join(text.split())
    
    return text

def extract_keywords_tfidf(
    texts: List[str], 
    max_features: int = 20,
    ngram_range: Tuple[int, int] = (1, 2)
) -> Tuple[List[str], List[float]]:
    """
    Extrai palavras-chave usando TF-IDF.
    
    Args:
        texts: Lista de textos para análise
        max_features: Número máximo de palavras-chave a retornar
        ngram_range: Faixa de n-gramas a serem considerados
        
    Returns:
        Tupla com (palavras-chave, escores TF-IDF)
    """
    # Cria o vetorizador TF-IDF
    tfidf = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words=PORTUGUESE_STOP_WORDS,
        max_features=max_features * 2  # Pega mais features para filtrar depois
    )
    
    # Ajusta e transforma os textos
    tfidf_matrix = tfidf.fit_transform(texts)
    
    # Obtém as palavras (features)
    feature_names = tfidf.get_feature_names_out()
    
    # Soma os escores TF-IDF para cada palavra entre todos os documentos
    scores = tfidf_matrix.sum(axis=0).A1
    
    # Ordena as palavras por score
    top_indices = scores.argsort()[::-1][:max_features]
    
    # Retorna as palavras-chave e seus escores
    keywords = [feature_names[i] for i in top_indices]
    keyword_scores = [float(scores[i]) for i in top_indices]
    
    return keywords, keyword_scores

def extract_topics_lda(
    texts: List[str],
    n_topics: int = 3,
    n_top_words: int = 5,
    max_iter: int = 10
) -> List[Dict[str, Any]]:
    """
    Extrai tópicos usando LDA (Latent Dirichlet Allocation).
    
    Args:
        texts: Lista de textos para análise
        n_topics: Número de tópicos a serem extraídos
        n_top_words: Número de palavras por tópico
        max_iter: Número máximo de iterações do algoritmo LDA
        
    Returns:
        Lista de dicionários, cada um representando um tópico com suas palavras-chave
    """
    # Cria o vetorizador de contagem de termos
    tf_vectorizer = TfidfVectorizer(
        max_df=1.0,  # Ajustado para funcionar com poucos documentos
        min_df=1,    # Ajustado para funcionar com poucos documentos
        stop_words=PORTUGUESE_STOP_WORDS,
        ngram_range=(1, 2)
    )
    
    # Ajusta e transforma os textos
    tf = tf_vectorizer.fit_transform(texts)
    
    # Treina o modelo LDA
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        max_iter=max_iter,
        learning_method='online',
        learning_offset=50.,
        random_state=42
    )
    
    lda.fit(tf)
    
    # Obtém as palavras (features)
    feature_names = tf_vectorizer.get_feature_names_out()
    
    # Extrai as palavras mais importantes de cada tópico
    topics = []
    for topic_idx, topic in enumerate(lda.components_):
        # Pega os índices das palavras mais importantes
        top_indices = topic.argsort()[:-n_top_words - 1:-1]
        
        # Cria um dicionário para o tópico no formato correto
        keywords_with_scores = []
        for i, idx in enumerate(top_indices):
            keywords_with_scores.append({
                'keyword': feature_names[idx],
                'score': float(topic[idx])
            })
        
        topic_data = {
            'topic_id': topic_idx,
            'keywords': keywords_with_scores,
            'score': float(max(topic[i] for i in top_indices))  # Score do tópico é o maior score das keywords
        }
        topics.append(topic_data)
    
    return topics

def extract_features(niche: str, description: str) -> Dict[str, Any]:
    """
    Processa o nicho e a descrição para extrair características de PLN.
    
    Esta função combina várias técnicas de PLN para extrair informações úteis:
    - Normalização de texto
    - Extração de palavras-chave com TF-IDF
    - Modelagem de tópicos com LDA
    - Reconhecimento de entidades nomeadas
    - Geração de embeddings
    
    Args:
        niche: O nicho de negócio
        description: A descrição detalhada
        
    Returns:
        Dicionário com as características extraídas
    """
    import time
    start_time = time.time()
    
    if not nlp:
        raise RuntimeError("Modelo spaCy 'pt_core_news_lg' não está disponível.")

    # Texto original para preservar
    original_text = f"{niche}. {description}"
    
    # 1. Normalização
    normalized_niche = normalize_text(niche)
    normalized_description = normalize_text(description)
    full_text = f"{normalized_niche}. {normalized_description}"
    
    # 2. Processamento com spaCy
    doc = nlp(full_text)
    
    # 3. Extração de palavras-chave com TF-IDF
    # Usamos tanto o nicho quanto a descrição como documentos separados
    texts_for_tfidf = [normalized_niche, normalized_description]
    
    # Extrai palavras-chave do nicho (com maior peso)
    niche_keywords, niche_scores = extract_keywords_tfidf(
        [normalized_niche], 
        max_features=10
    )
    
    # Extrai palavras-chave da descrição
    desc_keywords, desc_scores = extract_keywords_tfidf(
        [normalized_description],
        max_features=15
    )
    
    # Combina as palavras-chave, dando prioridade às do nicho
    keywords = []
    seen = set()
    
    # Adiciona palavras-chave do nicho primeiro (com peso maior)
    for kw, score in zip(niche_keywords, niche_scores):
        if kw not in seen:
            keywords.append({
                'keyword': kw, 
                'score': score * 1.5,  # Aumenta o peso do nicho
                'method': 'tfidf_niche'
            })
            seen.add(kw)
    
    # Adiciona palavras-chave da descrição
    for kw, score in zip(desc_keywords, desc_scores):
        if kw not in seen and len(keywords) < 20:  # Limita ao total de 20 palavras-chave
            keywords.append({
                'keyword': kw, 
                'score': score,
                'method': 'tfidf_description'
            })
            seen.add(kw)
    
    # Ordena as palavras-chave por score
    keywords = sorted(keywords, key=lambda x: x['score'], reverse=True)
    
    # 4. Extração de tópicos com LDA
    # Usamos frases da descrição como documentos separados
    sentences = [sent.text for sent in nlp(normalized_description).sents]
    if len(sentences) < 3:  # Se não houver frases suficientes, usa a descrição inteira
        sentences = [normalized_description]
    
    topics = extract_topics_lda(
        sentences,
        n_topics=min(3, len(sentences)),  # No máximo 3 tópicos
        n_top_words=5
    )
    
    # 5. Reconhecimento de Entidades Nomeadas (NER)
    entities = [
        {
            'text': ent.text, 
            'label': ent.label_, 
            'start_char': ent.start_char, 
            'end_char': ent.end_char
        }
        for ent in doc.ents
    ]
    
    # 6. Geração de Embeddings
    # 6.1 Embedding do texto completo com BERT
    if BERT_AVAILABLE:
        # Gera embedding BERT para o texto completo
        bert_embedding = BERT_MODEL.encode(
            full_text,
            convert_to_tensor=False,
            show_progress_bar=False
        ).tolist()
        
        # Gera embeddings para cada tópico
        topic_embeddings = []
        for topic in topics:
            # Extrai as palavras-chave do tópico (agora são objetos dict)
            topic_keywords = [kw.get('keyword', str(kw)) if isinstance(kw, dict) else str(kw) for kw in topic.get('keywords', [])]
            topic_text = ' '.join(topic_keywords)
            topic_embedding = BERT_MODEL.encode(
                topic_text,
                convert_to_tensor=False,
                show_progress_bar=False
            ).tolist()
            topic_embeddings.append(topic_embedding)
        
        # Calcula similaridade entre tópicos e o texto completo
        if len(topic_embeddings) > 0:
            similarities = cosine_similarity(
                [bert_embedding],
                topic_embeddings
            )[0]
            
            # Adiciona a similaridade a cada tópico
            for i, sim in enumerate(similarities):
                topics[i]['similarity_to_main_text'] = float(sim)
    else:
        # Fallback para embeddings do spaCy se BERT não estiver disponível
        bert_embedding = doc.vector.tolist()
    
    # 7. Montagem do resultado no formato correto para NLPFeatures
    processing_time = time.time() - start_time
    
    result = {
        'original_text': original_text,
        'normalized_text': full_text,
        'keywords': keywords,  # Já no formato correto com keyword, score, method
        'topics': topics,
        'entities': entities,  # Já no formato correto com start_char, end_char
        'embeddings': {
            'bert': {
                'model': 'sentence-transformers/all-MiniLM-L6-v2',
                'vector': bert_embedding if BERT_AVAILABLE else [],
                'dim': BERT_DIM if BERT_AVAILABLE else 0
            },
            'spacy': {
                'model': 'pt_core_news_lg',
                'vector': doc.vector.tolist(),
                'dim': len(doc.vector)
            }
        },
        'language': 'pt-BR',
        'processing_time': processing_time
    }
    
    return result
