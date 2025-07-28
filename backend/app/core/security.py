# backend/app/core/security.py

from passlib.context import CryptContext

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
