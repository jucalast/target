"""
Repositório base para operações de persistência.

Este módulo define uma classe base abstrata para repositórios, fornecendo
operações CRUD comuns que podem ser estendidas por repositórios específicos.
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type, Union


from pydantic import BaseModel
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId

from ..mongodb import db_connection

# Tipos genéricos para o repositório
T = TypeVar('T', bound=BaseModel)
T_ID = TypeVar('T_ID')  # Tipo do ID (str, int, ObjectId, etc.)


class BaseRepository(ABC, Generic[T, T_ID]):
    """
    Classe base abstrata para repositórios de persistência.
    Esta classe fornece operações CRUD básicas que podem ser estendidas por
    repositórios específicos para cada entidade do domínio.
    """

    def __init__(self, collection_name: str, model_class: Type[T]):
        """
        Inicializa o repositório com o nome da coleção e a classe do modelo.
        Args:
            collection_name: Nome da coleção no banco de dados
            model_class: Classe do modelo Pydantic para validação
        """
        self.collection_name = collection_name
        self.model_class = model_class
        self._collection = None
    @property

    def db(self) -> Database:
        """Retorna a instância do banco de dados."""
        return db_connection.db
    @property

    def collection(self) -> Collection:
        """Retorna a coleção do MongoDB."""
        if self._collection is None:
            self._collection = self.db[self.collection_name]
        return self._collection

    def _convert_to_model(self, data: Dict[str, Any]) -> T:
        """
        Converte um dicionário do MongoDB para o modelo Pydantic.
        Args:
            data: Dicionário com os dados do documento
        Returns:
            Instância do modelo Pydantic
        """
        if not data:
            return None
        # Converte ObjectId para string
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        return self.model_class(**data)

    def _convert_to_dict(self, model: T,\
        exclude_unset: bool = False) -> Dict[str, Any]:
        """
        Converte um modelo Pydantic para um dicionário compatível com o MongoDB.
        Args:
            model: Instância do modelo Pydantic
            exclude_unset: Se True, exclui campos não definidos
        Returns:
            Dicionário com os dados do modelo
        """
        if model is None:
            return None
        data = model.dict(exclude_unset=exclude_unset)
        # Remove o campo 'id' se existir e converter para _id se for um ObjectId
        if 'id' in data and data['id'] is not None:
            data['_id'] = ObjectId(data.pop('id'))
        return data
    async def create(self, item: T) -> T:
        """
        Cria um novo documento no banco de dados.
        Args:
            item: Instância do modelo a ser criada
        Returns:
            Instância do modelo com o ID gerado
        """
        data = self._convert_to_dict(item)
        # Insere o documento
        result = await self.collection.insert_one(data)
        # Retorna o documento criado
        created = await self.collection.find_one({'_id': result.inserted_id})
        return self._convert_to_model(created)
    async def get_by_id(self, item_id: T_ID) -> Optional[T]:
        """
        Obtém um documento pelo ID.
        Args:
            item_id: ID do documento
        Returns:
            Instância do modelo ou None se não encontrado
        """
        # Converte string para ObjectId se necessário
        if isinstance(item_id, str):
            try:
                item_id = ObjectId(item_id)
            except:
                pass

        document = await self.collection.find_one({'_id': item_id})
        return self._convert_to_model(document)

    async def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        """
        Encontra um único documento que corresponda à consulta.
        Args:
            query: Dicionário com os critérios de busca
        Returns:
            Primeiro documento que corresponde à consulta ou None
        """
        document = await self.collection.find_one(query)
        return self._convert_to_model(document)
    async def find(
        self,
        query: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[T]:
        """
        Encontra vários documentos que correspondam à consulta.
        Args:
            query: Dicionário com os critérios de busca
            skip: Número de documentos a pular
            limit: Número máximo de documentos a retornar
            sort: Lista de tuplas (campo, direção) para ordenação
        Returns:
            Lista de documentos que correspondem à consulta
        """
        if query is None:
            query = {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return [self._convert_to_model(doc) for doc in await cursor.to_list(\
            length=limit)]
    async def update(self, item_id: T_ID, item: T) -> bool:
        """
        Atualiza um documento existente.
        Args:
            item_id: ID do documento a ser atualizado
            item: Instância do modelo com os dados atualizados
        Returns:
            True se o documento foi atualizado, False caso contrário
        """
        data = self._convert_to_dict(item, exclude_unset=True)
        # Remove o _id dos dados para evitar atualização
        data.pop('_id', None)
        # Converte string para ObjectId se necessário
        if isinstance(item_id, str):
            try:
                item_id = ObjectId(item_id)
            except:
                pass

        # Atualiza o documento
        result = await self.collection.update_one(
            {'_id': item_id},
            {'$set': data, '$currentDate': {'updated_at': True}}
        )

        return result.modified_count > 0

    async def delete(self, item_id: T_ID) -> bool:
        """
        Remove um documento do banco de dados.
        Args:
            item_id: ID do documento a ser removido
        Returns:
            True se o documento foi removido, False caso contrário
        """
        # Converte string para ObjectId se necessário
        if isinstance(item_id, str):
            try:
                item_id = ObjectId(item_id)
            except:
                pass

        result = await self.collection.delete_one({'_id': item_id})
        return result.deleted_count > 0

    async def count(self, query: Dict[str, Any] = None) -> int:
        """
        Conta o número de documentos que correspondem à consulta.
        Args:
            query: Dicionário com os critérios de busca
        Returns:
            Número de documentos que correspondem à consulta
        """
        if query is None:
            query = {}
        return await self.collection.count_documents(query)
    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Verifica se existe pelo menos um documento que corresponda à consulta.
        Args:
            query: Dicionário com os critérios de busca
        Returns:
            True se existir pelo menos um documento, False caso contrário
        """
        return await self.collection.count_documents(query, limit=1) > 0
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str,\
        Any]]:
        """
        Executa uma operação de agregação no MongoDB.
        Args:
            pipeline: Lista de estágios de agregação
        Returns:
            Lista de documentos resultantes da agregação
        """
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
    async def create_indexes(self) -> None:
        """
        Cria índices para otimização de consultas.
        Este método deve ser sobrescrito por classes filhas para definir índices específicos.
        """
        pass
