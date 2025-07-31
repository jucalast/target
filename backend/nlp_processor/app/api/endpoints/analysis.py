# backend/nlp_processor/app/endpoints/analysis.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.schemas import analysis as analysis_schema
from nlp_processor.app.services import analysis_service
from shared.db.database import get_db
# Supondo que a autenticação será adicionada futuramente
# from app.api.deps import get_current_user
# from app.models.user import User

# ==============================================================================
# Roteador da API para Análises
# ==============================================================================
router = APIRouter()

@router.post(
    "/",
    response_model=analysis_schema.AnalysisRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cria e processa uma nova análise de negócio",
    description="Recebe o nicho e a descrição de um negócio, extrai características via NLP e retorna o resultado estruturado."
)


def create_analysis(
    analysis_input: analysis_schema.AnalysisCreate,
    db: Session = Depends(get_db),
    # Descomentar quando a autenticação estiver implementada
    # current_user: User = Depends(get_current_user) 
):
    """
    Endpoint para criar uma nova análise de público-alvo.

    - **analysis_input**: Corpo da requisição, validado pelo schema `AnalysisCreate`.
    - **db**: Sessão do banco de dados, injetada pela dependência `get_db`.
    - **response_model**: Garante que a resposta seja formatada pelo schema `AnalysisRead`.
    - **status_code**: Define o código de status HTTP para uma criação bem-sucedida.
    """
    # A lógica de negócio complexa é delegada para a camada de serviço.
    # O endpoint apenas orquestra a chamada.
    # O user_id seria obtido do usuário autenticado (ex: current_user.id)
    # Por enquanto, usaremos um ID fixo para fins de desenvolvimento.
    user_id_placeholder = 1 

    return analysis_service.create_and_extract_features(
        db=db, 
        user_id=user_id_placeholder, 
        analysis_input=analysis_input
    )
