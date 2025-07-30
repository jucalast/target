import spacy
from typing import Dict, Any, List

# Carregando o modelo de linguagem do spaCy para português
# É esperado que este modelo seja baixado durante a configuração do ambiente
try:
    nlp = spacy.load("pt_core_news_lg")
except OSError:
    print("Modelo 'pt_core_news_lg' não encontrado. Execute 'python -m spacy download pt_core_news_lg'")
    nlp = None

def normalize_text(text: str) -> str:
    """Converte o texto para minúsculas и remove espaços extras."""
    return " ".join(text.lower().split())

def extract_features(niche: str, description: str) -> Dict[str, Any]:
    """
    Processa o nicho e a descrição para extrair características de PLN.
    Retorna um dicionário estruturado com texto normalizado, palavras-chave e entidades.
    """
    if not nlp:
        raise RuntimeError("Modelo spaCy 'pt_core_news_lg' não está disponível.")

    # 1. Normalização
    normalized_niche = normalize_text(niche)
    normalized_description = normalize_text(description)
    full_text = f"{normalized_niche}. {normalized_description}"

    doc = nlp(full_text)

    # 2. Extração de Palavras-chave (Lematização e Remoção de Stopwords)
    keywords = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "PROPN", "ADJ"]
    ]
    # Dando maior peso para as palavras do nicho
    niche_keywords = [token.lemma_ for token in nlp(normalized_niche) if not token.is_stop and not token.is_punct]
    final_keywords = list(dict.fromkeys(niche_keywords + keywords)) # Remove duplicatas mantendo a ordem

    # 3. Reconhecimento de Entidades Nomeadas (NER)
    entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    # 4. Geração de Embedding (vetor da sentença inteira)
    embedding = doc.vector.tolist()

    # 5. Montagem do resultado
    result = {
        "normalized_text": full_text,
        "keywords": final_keywords[:20],  # Limita para as 20 mais relevantes
        "entities": entities,
        "embedding": embedding
    }

    return result
