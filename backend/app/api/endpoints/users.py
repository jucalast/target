# backend/app/api/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import user as user_schema
from app.services import user_service
from app.db.database import get_db

# ==============================================================================
# Roteador da API para Usuários
# ==============================================================================

# Cria uma instância de APIRouter. Os endpoints definidos neste roteador
# serão incluídos na aplicação principal do FastAPI.
router = APIRouter()

@router.post(
    "/",
    response_model=user_schema.UserRead,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user: user_schema.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para criar um novo usuário no sistema.

    - **user**: Corpo da requisição, validado pelo schema `UserCreate`.
    - **db**: Sessão do banco de dados, injetada pela dependência `get_db`.
    - **response_model**: Garante que a resposta seja formatada pelo schema `UserRead`.
    - **status_code**: Define o código de status HTTP para uma criação bem-sucedida.
    """
    # Verifica se um usuário com o e-mail fornecido já existe no banco de dados.
    # Esta é uma verificação de regra de negócio.
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        # Se o usuário já existir, levanta uma exceção HTTP.
        # O FastAPI a converterá em uma resposta HTTP 409 Conflict.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um usuário com este e-mail já está cadastrado no sistema."
        )

    # Se o e-mail for único, delega a criação do usuário para a camada de serviço.
    # A função de serviço lida com o hashing da senha e a interação com o banco.
    return user_service.create_user(db=db, user=user)