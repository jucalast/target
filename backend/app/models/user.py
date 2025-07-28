from sqlalchemy import Column, Integer, String
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
# backend/app/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base

# ============================================================================== 
# Modelo SQLAlchemy para a Entidade User
# ============================================================================== 

class User(Base):
    """
    Modelo ORM que representa a tabela 'users' no banco de dados.
    Cada atributo da classe é mapeado para uma coluna na tabela.
    """
    __tablename__ = "users"

    # Define a coluna 'id' como um inteiro, chave primária e indexada.
    # A chave primária identifica unicamente cada registro na tabela.
    id = Column(Integer, primary_key=True, index=True)

    # Define a coluna 'email' como uma string.
    # 'unique=True' impõe uma restrição no nível do banco de dados, garantindo
    # que não possam existir dois usuários com o mesmo e-mail.
    # 'index=True' cria um índice nesta coluna, o que otimiza a velocidade
    # das consultas que filtram por e-mail.
    # 'nullable=False' garante que este campo não pode ser nulo.
    email = Column(String, unique=True, index=True, nullable=False)

    # Define a coluna 'hashed_password' como uma string.
    # O nome 'hashed_password' é uma escolha deliberada para deixar explícito
    # que esta coluna armazena o HASH da senha, e não a senha em texto plano.
    # 'nullable=False' garante que um usuário sempre terá uma senha.
    hashed_password = Column(String, nullable=False)

    # Define a coluna 'created_at' como um DateTime.
    # 'server_default=func.now()' instrui o banco de dados a preencher
    # automaticamente este campo com o timestamp atual no momento da criação
    # do registro. Isso garante a consistência e a integridade do dado,
    # pois a data é gerada pelo servidor do banco de dados, e não pela aplicação.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
