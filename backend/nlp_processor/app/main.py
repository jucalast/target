from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import shared modules
from shared.db.postgres import Base, engine
from shared.db.models import user, analysis

# Import API endpoints
from nlp_processor.app.api.endpoints import analysis as analysis_api
from nlp_processor.app.api.endpoints import ibge as ibge_api

# Import API Gateway routes
from api_gateway.app.routes import auth, users

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

# Inclui os roteadores de autenticação e usuários do api_gateway
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# Inclui o roteador de análises
app.include_router(analysis_api.router, prefix="/api/v1/analysis", tags=["Analysis"])

# Inclui o roteador de dados do IBGE
app.include_router(ibge_api.router, prefix="/api/v1/ibge", tags=["IBGE Data"])

@app.get("/")


def read_root():
    return {"message": "Bem-vindo à API do Sistema de Identificação de Público-Alvo"}
