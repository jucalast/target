# backend/app/services/user_service.py

from sqlalchemy.orm import Session
from shared.db.models import user as user_model
from shared.schemas import user as user_schema
from shared.utils.security import get_password_hash
    
# ==============================================================================
# Funções de Serviço para a Entidade User
# ==============================================================================

def get_user_by_email(db: Session, email: str) -> user_model.User | None:
    """
    Busca um usuário no banco de dados pelo seu endereço de e-mail.

    Args:
        db (Session): A sessão do banco de dados SQLAlchemy.
        email (str): O e-mail do usuário a ser buscado.

    Returns:
        user_model.User | None: O objeto do usuário se encontrado, caso contrário None.
    """
    # Executa uma consulta que filtra a tabela 'users' pelo campo 'email'.
    # '.first()' retorna o primeiro resultado correspondente ou None se nada for encontrado.
    return db.query(user_model.User).filter(user_model.User.email == email).first()


def create_user(db: Session, user: user_schema.UserCreate) -> user_model.User:
    """
    Cria um novo usuário no banco de dados.

    Args:
        db (Session): A sessão do banco de dados SQLAlchemy.
        user (user_schema.UserCreate): O objeto Pydantic com os dados do usuário
                                       a ser criado (email e senha).

    Returns:
        user_model.User: O objeto SQLAlchemy do usuário recém-criado.
    """
    # Passo 1: Hashear a senha recebida.
    # A senha em texto plano (user.password) é passada para a função de segurança,
    # que retorna o hash seguro.
    hashed_password = get_password_hash(user.password)

    # Passo 2: Criar uma instância do modelo SQLAlchemy.
    # Note que o campo 'password' do schema é mapeado para o campo
    # 'hashed_password' do modelo.
    # O Pydantic v2 introduziu a capacidade de excluir campos durante a conversão
    # para dicionário, o que torna este passo mais limpo.
    db_user = user_model.User(
        email=user.email,
        name=user.name,
        role=user.role,
        avatar=user.avatar,
        hashed_password=hashed_password
    )

    # Passo 3: Adicionar a nova instância à sessão do banco de dados.
    # Neste ponto, a mudança está pendente e ainda não foi salva no banco.
    db.add(db_user)

    # Passo 4: Comitar a transação.
    # 'db.commit()' efetivamente executa a instrução INSERT no banco de dados,
    # salvando o novo usuário.
    db.commit()

    # Passo 5: Refrescar a instância.
    # 'db.refresh()' atualiza o objeto 'db_user' com os dados que foram
    # gerados pelo banco de dados durante o INSERT, como o 'id' (autoincremento)
    # e 'created_at' (server default).
    db.refresh(db_user)

    # Passo 6: Retornar o objeto de usuário completo.
    return db_user