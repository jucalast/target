from fastapi import FastAPI
from app.api.endpoints import users, analysis

app = FastAPI(
    title="Sistema de Identificação de Público-Alvo",
    description="API para o sistema de identificação de público-alvo baseado no TCC de João Luccas Ferreira Moura.",
    version="0.1.0"
)

# Incluir os roteadores dos diferentes módulos
app.include_router(users.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Sistema de Identificação de Público-Alvo"}
