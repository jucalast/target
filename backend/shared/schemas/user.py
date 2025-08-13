# backend/app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# ==============================================================================
# Schema Base
# ==============================================================================

class UserBase(BaseModel):
    """
    Schema base para a entidade User.
    Contém os campos que são comuns a todos os outros schemas de usuário.
    Isso evita a repetição de código (princípio DRY).
    """
    email: EmailStr  # Utiliza EmailStr para validação automática do formato do e-mail.
    name: str
    role: str = "user"
    avatar: Optional[str] = None

# ==============================================================================
# Schema para Criação de Usuário
# ==============================================================================

class UserCreate(UserBase):
    """
    Schema usado para criar um novo usuário.
    Herda os campos de UserBase e adiciona o campo 'password'.
    Este é o modelo de dados que a API esperará receber no corpo da requisição
    para o endpoint de criação de usuário.
    """
    password: str

# ==============================================================================
# Schema para Leitura de Usuário (Resposta da API)
# ==============================================================================

class UserRead(UserBase):
    """
    Schema usado para retornar os dados de um usuário pela API.
    Herda os campos de UserBase e adiciona os campos que são seguros
    para serem expostos ao cliente.

    Criticamente, este schema NÃO inclui o campo 'password', garantindo que
    o hash da senha nunca seja enviado em uma resposta da API.
    """
    id: int
    created_at: datetime

    class Config:
        """
        Configuração do Pydantic para o schema.
        'from_attributes = True' (anteriormente 'orm_mode = True') permite que o
        Pydantic leia os dados diretamente de um objeto de modelo ORM
        (como um objeto SQLAlchemy), em vez de apenas de um dicionário.
        Isso é essencial para mapear o modelo do banco de dados para este schema
        de resposta.
        """
        from_attributes = True