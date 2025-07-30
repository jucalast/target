# backend/app/services/analysis_service.py
import re
from collections import Counter
import spacy
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisCreate
from app.models.analysis import Analysis as AnalysisModel

# ==============================================================================
# Carregamento dos modelos de NLP (carregados uma vez na inicialização)
# ==============================================================================
try:
    # Carrega o pipeline do spaCy para português
    nlp_spacy = spacy.load("pt_core_news_sm")
except OSError:
    print("Baixando o modelo 'pt_core_news_sm' do spaCy...")
    spacy.cli.download("pt_core_news_sm")
    nlp_spacy = spacy.load("pt_core_news_sm")

# Carrega o modelo de sentence-transformers
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# ==============================================================================
# Funções Auxiliares de NLP
# ==============================================================================
def _normalize_text(text: str) -> str:
    """
    Limpa e normaliza o texto de entrada.
    - Converte para minúsculas.
    - Remove caracteres especiais, exceto hífens.
    - Remove espaços extras.
    """
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text) # Mantém palavras, espaços e hífens
    text = " ".join(text.split())
    return text

# ==============================================================================
# Serviço Principal de Análise
# ==============================================================================
def create_and_extract_features(db: Session, user_id: int, analysis_input: AnalysisCreate) -> AnalysisModel:
    """
    Orquestra o processo completo de extração de características e persistência.
    1. Normaliza o texto de entrada.
    2. Extrai palavras-chave e entidades com spaCy.
    3. Gera o embedding semântico com sentence-transformers.
    4. Salva o resultado no banco de dados.
    5. Retorna o registro da análise completa.
    """
    # Etapa 1: Normalização (conforme Figura 2 do TCC)
    normalized_text = _normalize_text(analysis_input.description)

    # Etapa 2: Processamento com spaCy
    doc = nlp_spacy(normalized_text)

    # Etapa 3: Extração de Palavras-chave (baseado em frequência de lemas)
    lemmas = [
        token.lemma_ for token in doc 
        if not token.is_stop and not token.is_punct and not token.is_space
    ]
    keyword_counts = Counter(lemmas)
    keywords = [keyword for keyword, _ in keyword_counts.most_common(10)]

    # Etapa 4: Extração de Entidades Nomeadas (NER)
    entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    # Etapa 5: Geração de Embedding Semântico
    embedding = embedding_model.encode(normalized_text).tolist()

    # Etapa 6: Criação do objeto do modelo de dados para persistência
    db_analysis = AnalysisModel(
        user_id=user_id,
        niche=analysis_input.niche,
        description=analysis_input.description,
        normalized_text=normalized_text,
        keywords=keywords,
        entities=entities,
        embedding=embedding
    )

    # Etapa 7: Persistência no Banco de Dados
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return db_analysis
