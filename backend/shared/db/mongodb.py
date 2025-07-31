"""
Configuração e conexão com o MongoDB.

Este módulo fornece uma classe para gerenciar a conexão com o MongoDB,
incluindo métodos para obter coleções e gerenciar índices.
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ConfigurationError

from ..utils.config import settings

logger = logging.getLogger(__name__)

class MongoDBConnection:
"""
    Classe para gerenciar a conexão com o MongoDB.
    Implementa o padrão Singleton para garantir uma única instância de conexão.
    """
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
        cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self) -> None:
    """Inicializa a conexão com o MongoDB."""
        try:

            mongo_uri = settings.MONGODB_URL
            db_name = settings.MONGODB_DB_NAME

            client_options = {
            'connectTimeoutMS': 5000,
            'serverSelectionTimeoutMS': 3000,
            'retryWrites': True,
            'w': 'majority'
            }

            self._client = MongoClient(mongo_uri, **client_options)

            self._client.admin.command('ping')

            self._db = self._client[db_name]
            logger.info(f"Conexão com MongoDB estabelecida: {db_name}")
        except (ConnectionFailure, ConfigurationError) as e:
        logger.error(f"Falha ao conectar ao MongoDB: {str(e)}")
            self._client = None
            self._db = None
            raise
    @property

    def db(self) -> Database:
    """Retorna a instância do banco de dados MongoDB."""
        if self._db is None:
        self._initialize_connection()
        return self._db

    def get_collection(self, collection_name: str):
    """
        Retorna uma coleção do MongoDB.
        Args:
        collection_name: Nome da coleção
        Returns:
        Objeto de coleção do MongoDB
        """
        return self.db[collection_name]

    def ensure_indexes(self) -> None:
    """Cria índices para otimização de consultas."""
        try:

            news_collection = self.get_collection('news_articles')
            news_collection.create_index([('title', 'text'), ('content', \
                'text')])
            news_collection.create_index([('published_at', \
                -1)])
            news_collection.create_index([('source.domain', \
                1)])
            news_collection.create_index([('category', \
                1)])
            news_collection.create_index([('sentiment_score', \
                1)])

            metrics_collection = self.get_collection('market_metrics')
            metrics_collection.create_index([('name', 1)], unique=True)
            metrics_collection.create_index([('timestamp', -1)])
            logger.info("Índices do MongoDB criados com sucesso")
        except Exception as e:
        logger.error(f"Erro ao criar índices do MongoDB: {str(e)}")
            raise

    def close_connection(self) -> None:
    """Fecha a conexão com o MongoDB."""
        if self._client:
        self._client.close()
            self._client = None
            self._db = None
            logger.info("Conexão com MongoDB encerrada")

    db_connection = MongoDBConnection()

def get_mongodb() -> Database:
"""
    Função de dependência para injeção em rotas FastAPI.
    Returns:
    Instância do banco de dados MongoDB
    """
        return db_connection.db

def get_collection(collection_name: str):
"""
    Função auxiliar para obter uma coleção do MongoDB.
    Args:
    collection_name: Nome da coleção
    Returns:
    Objeto de coleção do MongoDB
    """
        return db_connection.get_collection(collection_name)
