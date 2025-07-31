from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shared.utils.config import settings

SQLALCHEMY_DATABASE_URL = settings.POSTGRESQL_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

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
