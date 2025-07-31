"""
Testes para o serviço de Processamento de Linguagem Natural (PLN).
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.nlp_service import (
    normalize_text,
    extract_keywords_tfidf,
    extract_topics_lda,
    extract_features
)

# Dados de teste
TEST_NICHE = "Moda sustentável"
TEST_DESCRIPTION = """
    Loja de roupas e acessórios feitos com materiais reciclados e orgânicos.
    Focamos em peças atemporais, produção ética e comércio justo.
    Nossos produtos são feitos por cooperativas locais de artesãs.
"""

class TestNormalizeText:
    """Testes para a função de normalização de texto."""
    
    def test_normalize_text_lowercase(self):
        """Testa a conversão para minúsculas."""
        result = normalize_text("TEXTO EM MAIÚSCULAS")
        assert result == "texto em maiusculas"
    
    def test_normalize_text_remove_accents(self):
        """Testa a remoção de acentos."""
        result = normalize_text("coração, ação, pão de queijo")
        assert result == "coracao acao pao de queijo"
    
    def test_normalize_text_remove_special_chars(self):
        """Testa a remoção de caracteres especiais."""
        result = normalize_text("Texto com @#$%^&*()_+{}[]|\\:;\"'<>,.?/!~`")
        assert result == "texto com"
    
    def test_normalize_text_extra_spaces(self):
        """Testa a remoção de espaços extras."""
        result = normalize_text("  texto  com    muitos     espaços    ")
        assert result == "texto com muitos espacos"

class TestExtractKeywordsTfidf:
    """Testes para a extração de palavras-chave com TF-IDF."""
    
    def test_extract_keywords_basic(self):
        """Testa a extração básica de palavras-chave."""
        texts = ["moda sustentável", "roupas feitas com materiais reciclados"]
        keywords, scores = extract_keywords_tfidf(texts, max_features=5)
        
        assert len(keywords) <= 5
        assert len(keywords) == len(scores)
        assert all(isinstance(kw, str) for kw in keywords)
        assert all(isinstance(score, float) for score in scores)
        
        # Verifica se palavras-chave esperadas estão presentes
        expected_keywords = ["moda", "sustentavel", "roupas", "materiais", "reciclados"]
        assert any(kw in expected_keywords for kw in keywords)

class TestExtractTopicsLda:
    """Testes para a extração de tópicos com LDA."""
    
    def test_extract_topics_basic(self):
        """Testa a extração básica de tópicos."""
        texts = [
            "moda sustentável e roupas ecológicas",
            "acessórios feitos de materiais reciclados",
            "produção ética e comércio justo",
            "moda consciente e responsável"
        ]
        
        topics = extract_topics_lda(
            texts,
            n_topics=2,
            n_top_words=3,
            max_iter=5  # Usar menos iterações para testes
        )
        
        assert len(topics) == 2
        for topic in topics:
            assert 'topic_id' in topic
            assert 'keywords' in topic
            assert 'scores' in topic
            assert len(topic['keywords']) == 3
            assert len(topic['scores']) == 3

class TestExtractFeatures:
    """Testes para a função principal de extração de características."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuração para os testes."""
        # Garante que o modelo spaCy está carregado
        from app.services.nlp_service import nlp
        if nlp is None:
            pytest.skip("Modelo spaCy não está disponível")
    
    def test_extract_features_basic(self):
        """Testa a extração básica de características."""
        features = extract_features(TEST_NICHE, TEST_DESCRIPTION)
        
        # Verifica a estrutura básica do resultado
        assert isinstance(features, dict)
        assert 'normalized_text' in features
        assert 'keywords' in features
        assert 'topics' in features
        assert 'entities' in features
        assert 'embeddings' in features
        assert 'metadata' in features
        
        # Verifica a estrutura de embeddings
        assert 'bert' in features['embeddings']
        assert 'spacy' in features['embeddings']
        assert 'dimension_bert' in features['embeddings']
        assert 'dimension_spacy' in features['embeddings']
        
        # Verifica o texto normalizado
        assert isinstance(features['normalized_text'], str)
        assert len(features['normalized_text']) > 0
        
        # Verifica as palavras-chave
        assert isinstance(features['keywords'], list)
        assert len(features['keywords']) > 0
        for kw in features['keywords']:
            assert 'keyword' in kw
            assert 'score' in kw
            assert isinstance(kw['keyword'], str)
            assert isinstance(kw['score'], float)
        
        # Verifica os tópicos
        assert isinstance(features['topics'], list)
        assert len(features['topics']) > 0
        for topic in features['topics']:
            assert 'topic_id' in topic
            assert 'keywords' in topic
            assert 'scores' in topic
            assert len(topic['keywords']) > 0
            assert len(topic['scores']) == len(topic['keywords'])
        
        # Verifica as entidades
        assert isinstance(features['entities'], list)
        
        # Verifica os embeddings
        assert isinstance(features['embeddings']['spacy'], list)
        assert len(features['embeddings']['spacy']) > 100  # Garante que é um vetor de tamanho razoável
        
        # Verifica se o embedding BERT está presente quando disponível
        if features['embeddings']['bert'] is not None:
            assert isinstance(features['embeddings']['bert'], list)
            assert len(features['embeddings']['bert']) == features['embeddings']['dimension_bert']
            
            # Verifica similaridade entre tópicos
            for topic in features['topics']:
                assert 'similarity_to_main_text' in topic
                assert 0 <= topic['similarity_to_main_text'] <= 1.0
        
        # Verifica os metadados
        assert features['metadata']['language'] == 'portuguese'
        assert 'model' in features['metadata']
        assert 'processing_steps' in features['metadata']
    
    def test_extract_features_empty_input(self):
        """Testa o comportamento com entrada vazia."""
        with pytest.raises(ValueError):
            extract_features("", "")
    
    def test_extract_features_stopwords(self):
        """Testa se palavras de parada são removidas corretamente."""
        features = extract_features("o a um uma com para", "texto de teste com palavras de parada")
        
        # Verifica se as palavras de parada não estão nas palavras-chave
        stopwords = ['o', 'a', 'um', 'uma', 'com', 'para', 'de']
        keywords = [kw['keyword'] for kw in features['keywords']]
        
        for stopword in stopwords:
            assert stopword not in keywords
