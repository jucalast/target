from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from api_gateway.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, \
    expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
    else:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, \
        algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
"""
    Verifica se uma senha em texto plano corresponde a um hash existente.
    Args:
    plain_password (str): A senha fornecida pelo usuário durante o login.
        hashed_password (str): A senha hasheada armazenada no banco de dados.
    Returns:
    bool: True se a senha corresponder ao hash, False caso contrário.
    """

    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
"""
    Gera o hash de uma senha em texto plano.
    Args:
    password (str): A senha em texto plano a ser hasheada.
    Returns:
    str: O hash da senha, incluindo o "sal" e os metadados do algoritmo.
    """

    return pwd_context.hash(password)
