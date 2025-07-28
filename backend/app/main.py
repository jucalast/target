from fastapi import FastAPI

from app.api.endpoints import users, analysis

app = FastAPI(
    title="Sistema de Identificação de Público-Alvo",
    description="API para o sistema de identificação de público-alvo baseado no TCC de João Luccas Ferreira Moura.",
    version="0.1.0"
)

# Incluir os roteadores dos diferentes módulos

# Inclui o roteador de usuários na aplicação principal.
# Todas as rotas definidas em 'users.router' serão prefixadas com '/api/v1/users'.
# Por exemplo, a rota "/" em users.py se torna "/api/v1/users/".
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

# Inclui o roteador de análises (exemplo para futuras implementações).
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Sistema de Identificação de Público-Alvo"}
