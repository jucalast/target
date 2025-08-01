"""
Exceções customizadas para o sistema.

Este módulo define as exceções customizadas utilizadas em todo o sistema
para padronizar o tratamento de erros.
"""


class BaseCustomException(Exception):
    """Exceção base para todas as exceções customizadas do sistema."""
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        self.message = message
        self.error_code = error_code
        self.original_error = original_error
        super().__init__(self.message)


class DatabaseError(BaseCustomException):
    """Exceção para erros relacionados ao banco de dados."""
    pass


class NotFoundError(BaseCustomException):
    """Exceção para quando um recurso não é encontrado."""
    pass


class ValidationError(BaseCustomException):
    """Exceção para erros de validação de dados."""
    pass


class AuthenticationError(BaseCustomException):
    """Exceção para erros de autenticação."""
    pass


class AuthorizationError(BaseCustomException):
    """Exceção para erros de autorização."""
    pass


class ExternalAPIError(BaseCustomException):
    """Exceção para erros relacionados a APIs externas."""
    pass


class ProcessingError(BaseCustomException):
    """Exceção para erros durante processamento de dados."""
    pass


class ConfigurationError(BaseCustomException):
    """Exceção para erros de configuração."""
    pass
