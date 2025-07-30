from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import users, login
from app.api.endpoints import analysis as analysis_api
from app.db.database import Base, engine
from app.models import user, analysis

app = FastAPI(
    title="Sistema de Identificação de Público-Alvo",
    description="API para o sistema de identificação de público-alvo baseado no TCC de João Luccas Ferreira Moura.",
    version="0.1.0"
)

# Set up CORS
origins = [
    "http://localhost:3000",
    # Add other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to create database tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)

# Call the function to create tables when the app starts
create_db_tables()

# Incluir os roteadores dos diferentes módulos

# Inclui o roteador de usuários na aplicação principal.
# Todas as rotas definidas em 'users.router' serão prefixadas com '/api/v1/users'.
# Por exemplo, a rota "/" em users.py se torna "/api/v1/users/".
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

# Inclui o roteador de análises (exemplo para futuras implementações).
app.include_router(analysis_api.router, prefix="/api/v1/analysis", tags=["Analysis"])

# Inclui o roteador de login.
app.include_router(login.router, prefix="/api/v1/login", tags=["Login"])

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Sistema de Identificação de Público-Alvo"}
