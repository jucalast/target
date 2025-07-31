"""
Configuração e conexão com o PostgreSQL.

Este módulo fornece uma classe para gerenciar a conexão com o PostgreSQL,
utilizando SQLAlchemy para ORM e gerenciamento de sessões.
"""
import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.engine.reflection import Inspector
import logging

from shared.utils.config import settings

logger = logging.getLogger(__name__)

# Base para os modelos SQLAlchemy
Base = declarative_base()

# Configuração inicial do engine (será sobrescrita pela classe PostgreSQLConnection)
engine = None
SessionLocal = None

class PostgreSQLConnection:
    """
    Classe para gerenciar a conexão com o PostgreSQL.
    
    Implementa o padrão Singleton para garantir uma única instância de conexão.
    """
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgreSQLConnection, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance
    
    def _initialize_connection(self):
        """Inicializa a conexão com o banco de dados PostgreSQL."""
        try:
            # Obter a URL de conexão das configurações
            db_url = settings.POSTGRESQL_URL
            
            # Obter configurações do pool de conexão
            engine_kwargs = settings.get_postgres_engine_kwargs()
            
            # Configurar o engine do SQLAlchemy
            self._engine = create_engine(db_url, **engine_kwargs)
            
            # Configurar a fábrica de sessões
            self._session_factory = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine,
                    expire_on_commit=False
                )
            )
            
            # Atualizar as variáveis globais
            global engine, SessionLocal
            engine = self._engine
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            logger.info("Conexão com o PostgreSQL inicializada com sucesso")
            logger.debug(f"Configurações do pool: {engine_kwargs}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar conexão com o PostgreSQL: {str(e)}")
            raise
    
    @property
    def engine(self) -> Engine:
        """Retorna a instância do engine SQLAlchemy."""
        if self._engine is None:
            self._initialize_connection()
        return self._engine
    
    @property
    def session(self) -> Session:
        """Retorna uma nova sessão do banco de dados."""
        if self._session_factory is None:
            self._initialize_connection()
        return self._session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Gerenciador de contexto para sessões do banco de dados.
        
        Exemplo de uso:
            with postgres_conn.get_session() as session:
                # Usar a sessão aqui
                result = session.query(Model).all()
        """
        session = self.session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na sessão do banco de dados: {str(e)}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """
        Verifica a saúde da conexão com o banco de dados.
        
        Returns:
            bool: True se a conexão estiver saudável, False caso contrário
        """
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Falha na verificação de saúde do PostgreSQL: {str(e)}")
            return False
    
    def get_table_names(self) -> list:
        """Retorna uma lista com os nomes de todas as tabelas no banco de dados."""
        try:
            return Inspector.from_engine(self.engine).get_table_names()
        except Exception as e:
            logger.error(f"Erro ao listar tabelas do banco de dados: {str(e)}")
            return []
    
    def close(self):
        """Fecha a conexão com o banco de dados."""
        try:
            if self._session_factory:
                self._session_factory.remove()
            if self._engine:
                self._engine.dispose()
            logger.info("Conexão com o PostgreSQL fechada com sucesso")
        except Exception as e:
            logger.error(f"Erro ao fechar conexão com o PostgreSQL: {str(e)}")

# Instância global para ser usada em toda a aplicação
postgres_conn = PostgreSQLConnection()

def get_postgres() -> PostgreSQLConnection:
    """
    Função de dependência para injeção em rotas FastAPI.
    
    Returns:
        Instância do gerenciador de conexão PostgreSQL
    """
    return postgres_conn

# Função de compatibilidade para injeção de dependência do FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Função de dependência para injeção de sessão do banco de dados em rotas FastAPI.
    
    Yields:
        Session: Sessão do banco de dados SQLAlchemy
    """
    with postgres_conn.get_session() as session:
        yield session
