from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Usando a configuração centralizada
from shared.utils.config import settings

# Importa a Base do postgres.py para garantir que todos os modelos usem a mesma Base
from .postgres import Base

# Usa a URL do PostgreSQL da configuração centralizada
SQLALCHEMY_DATABASE_URL = settings.POSTGRESQL_URL

# Configuração do engine com opções de pool de conexão
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verifica a conexão antes de usá-la
    pool_recycle=3600,   # Recicla conexões a cada hora
    pool_size=5,         # Número de conexões mantidas no pool
    max_overflow=10      # Número máximo de conexões além do pool_size
)

# Configuração da fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Gera uma sessão do banco de dados para uso em dependências do FastAPI.
    
    Yields:
        Session: Sessão do SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()