"""
Repositório base para operações com PostgreSQL.

Este módulo fornece uma classe base para implementação de repositórios
que utilizam o PostgreSQL como banco de dados.
"""
from typing import TypeVar, Type, Generic, List, Optional, Dict, Any, Union
from datetime import datetime
import logging

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..postgres import get_postgres
from ...utils.exceptions import DatabaseError, NotFoundError, ValidationError

# Tipo genérico para o modelo SQLAlchemy
ModelType = TypeVar("ModelType")
# Tipo genérico para o esquema Pydantic
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = logging.getLogger(__name__)


class BasePostgresRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Classe base para repositórios que utilizam PostgreSQL.

    Esta classe fornece operações CRUD básicas que podem ser estendidas por
    repositórios específicos de domínio.
    """

    def __init__(self, model: Type[ModelType], db_session: Optional[Session] = None):
        """
        Inicializa o repositório com o modelo e a sessão do banco de dados.

        Args:
            model: Classe do modelo SQLAlchemy
            db_session: Sessão do SQLAlchemy (opcional, usa a conexão padrão se não fornecido)
        """
        self.model = model
        self.postgres = get_postgres()
        self._db = db_session

    @property
    def db(self) -> Session:
        """Retorna a sessão ativa do banco de dados."""
        if self._db is None:
            self._db = self.postgres.session
        return self._db

    def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Cria um novo registro no banco de dados.

        Args:
            obj_in: Dados para criação do registro
            **kwargs: Argumentos adicionais para sobrescrever os dados de entrada

        Returns:
            O registro criado

        Raises:
            DatabaseError: Em caso de erro no banco de dados
            ValidationError: Em caso de erro de validação
        """
        try:
            # Converte o schema Pydantic para dicionário
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else (obj_in.dict() if hasattr(obj_in, 'dict') else dict(obj_in))
            # Atualiza com argumentos adicionais
            obj_data.update(kwargs)

            # Cria a instância do modelo
            db_obj = self.model(**obj_data)

            # Adiciona ao banco de dados
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)

            return db_obj

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Erro de integridade ao criar registro: {str(e)}")
            raise ValidationError("Erro de integridade nos dados fornecidos") from e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao criar registro no banco de dados: {str(e)}")
            raise DatabaseError("Erro ao criar registro") from e

    def get(self, id: Any) -> Optional[ModelType]:
        """
        Obtém um registro pelo ID.

        Args:
            id: ID do registro a ser recuperado

        Returns:
            O registro encontrado ou None se não existir
        """
        try:
            return self.db.query(self.model).get(id)
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar registro com ID {id}: {str(e)}")
            raise DatabaseError(f"Erro ao buscar registro com ID {id}") from e

    def get_or_404(self, id: Any) -> ModelType:
        """
        Obtém um registro pelo ID ou levanta uma exceção se não for encontrado.

        Args:
            id: ID do registro a ser recuperado

        Returns:
            O registro encontrado

        Raises:
            NotFoundError: Se o registro não for encontrado
        """
        obj = self.get(id)
        if not obj:
            raise NotFoundError(f"Registro com ID {id} não encontrado")
        return obj

    def list(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """
        Lista registros com suporte a paginação e filtros.

        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            **filters: Filtros a serem aplicados na consulta

        Returns:
            Lista de registros que correspondem aos filtros
        """
        try:
            query = self.db.query(self.model)

            # Aplica os filtros
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, (list, tuple)):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)

            return query.offset(skip).limit(limit).all()

        except SQLAlchemyError as e:
            logger.error(f"Erro ao listar registros: {str(e)}")
            raise DatabaseError("Erro ao listar registros") from e

    def update(
        self, 
        id: Any, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        exclude_unset: bool = True
    ) -> ModelType:
        """
        Atualiza um registro existente.

        Args:
            id: ID do registro a ser atualizado
            obj_in: Dados para atualização (pode ser um dicionário ou um schema Pydantic)
            exclude_unset: Se True, ignora campos não fornecidos (padrão: True)

        Returns:
            O registro atualizado

        Raises:
            NotFoundError: Se o registro não for encontrado
            DatabaseError: Em caso de erro no banco de dados
        """
        try:
            # Obtém o objeto existente
            db_obj = self.get_or_404(id)

            # Converte para dicionário se for um modelo Pydantic
            if hasattr(obj_in, 'dict'):
                update_data = obj_in.model_dump(exclude_unset=exclude_unset) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=exclude_unset)
            else:
                update_data = dict(obj_in)

            # Atualiza os campos do objeto
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            # Atualiza a data de atualização se o campo existir
            if hasattr(db_obj, 'updated_at'):
                db_obj.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(db_obj)

            return db_obj

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao atualizar registro com ID {id}: {str(e)}")
            raise DatabaseError(f"Erro ao atualizar registro com ID {id}") from e

    def delete(self, id: Any) -> bool:
        """
        Remove um registro do banco de dados.

        Args:
            id: ID do registro a ser removido

        Returns:
            True se o registro foi removido com sucesso, False caso contrário

        Raises:
            DatabaseError: Em caso de erro no banco de dados
        """
        try:
            obj = self.get_or_404(id)
            self.db.delete(obj)
            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao remover registro com ID {id}: {str(e)}")
            raise DatabaseError(f"Erro ao remover registro com ID {id}") from e

    def count(self, **filters) -> int:
        """
        Conta o número de registros que correspondem aos filtros.

        Args:
            **filters: Filtros a serem aplicados na contagem

        Returns:
            Número total de registros que correspondem aos filtros
        """
        try:
            query = self.db.query(self.model)

            # Aplica os filtros
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, (list, tuple)):
                        query = query.filter(getattr(self.model, field).in_(value))
                    else:
                        query = query.filter(getattr(self.model, field) == value)

            return query.count()

        except SQLAlchemyError as e:
            logger.error(f"Erro ao contar registros: {str(e)}")
            raise DatabaseError("Erro ao contar registros") from e

    def exists(self, **filters) -> bool:
        """
        Verifica se existe pelo menos um registro que corresponde aos filtros.

        Args:
            **filters: Filtros a serem aplicados na verificação

        Returns:
            True se existir pelo menos um registro, False caso contrário
        """
        return self.count(**filters) > 0

    def execute_raw(self, sql: str, params: Optional[Dict] = None) -> Any:
        """
        Executa uma consulta SQL bruta.

        Args:
            sql: Consulta SQL a ser executada
            params: Parâmetros para a consulta SQL

        Returns:
            Resultado da execução da consulta
        """
        try:
            result = self.db.execute(text(sql), params or {})
            self.db.commit()
            return result
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Erro ao executar consulta SQL: {str(e)}\nSQL: {sql}")
            raise DatabaseError("Erro ao executar consulta SQL") from e

    def health_check(self) -> bool:
        """
        Verifica a saúde da conexão com o banco de dados.

        Returns:
            bool: True se a conexão estiver saudável, False caso contrário
        """
        return self.postgres.health_check()
