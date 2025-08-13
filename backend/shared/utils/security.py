# shared/utils/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import from the config in the API Gateway module
from api_gateway.app.core.config import settings

# ==============================================================================
# Configuração do Contexto de Criptografia
# ==============================================================================

# Cria uma instância de CryptContext. Esta é a maneira recomendada de usar passlib.
# O CryptContext gerencia os algoritmos de hash (schemes) que a aplicação irá suportar.
#
# schemes=["bcrypt"]: Especifica que o bcrypt será o algoritmo padrão e único
# para hashear novas senhas. Bcrypt é uma escolha forte e padrão da indústria
# por ser lento e adaptativo.
#
# deprecated="auto": Instruiria o passlib a marcar automaticamente como obsoletos
# quaisquer algoritmos que não sejam o padrão. Neste caso, como só temos um,
# não é estritamente necessário, mas é uma boa prática para o futuro.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme para extrair token do header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ==============================================================================
# Funções de Manuseio de Senha
# ==============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash existente.

    Args:
        plain_password (str): A senha fornecida pelo usuário durante o login.
        hashed_password (str): A senha hasheada armazenada no banco de dados.

    Returns:
        bool: True se a senha corresponder ao hash, False caso contrário.
    """
    # A função 'verify' do CryptContext lida com todo o processo de forma segura.
    # Ela extrai o "sal" do hash armazenado, hasheia a senha em texto plano
    # com o mesmo "sal" e os mesmos parâmetros, e compara os resultados.
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera o hash de uma senha em texto plano.

    Args:
        password (str): A senha em texto plano a ser hasheada.

    Returns:
        str: O hash da senha, incluindo o "sal" e os metadados do algoritmo.
    """
    # A função 'hash' do CryptContext gera um "sal" aleatório, combina-o com a
    # senha e aplica o algoritmo de hash padrão (bcrypt). O resultado é uma
    # string única que contém todas as informações necessárias para a verificação.
    return pwd_context.hash(password)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decodifica um token JWT e retorna o email do usuário.
    
    Args:
        token (str): O token JWT a ser decodificado.
        
    Returns:
        Optional[str]: O email do usuário se o token for válido, None caso contrário.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None


def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependência para obter o email do usuário atual a partir do token JWT.
    
    Args:
        token (str): Token JWT extraído do header Authorization.
        
    Returns:
        str: Email do usuário atual.
        
    Raises:
        HTTPException: Se o token for inválido ou não contiver credenciais válidas.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception
    
    return email