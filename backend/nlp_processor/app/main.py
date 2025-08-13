from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Constrói o caminho absoluto para o arquivo .env.development na raiz do projeto
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env.development')
load_dotenv(dotenv_path=env_path)
from fastapi.middleware.cors import CORSMiddleware

# Import shared modules
from shared.db.database import Base, engine
from shared.db.models import user, analysis

# Import API endpoints
from nlp_processor.app.api.endpoints import analysis as analysis_api
from nlp_processor.app.api.endpoints import ibge as ibge_api
from nlp_processor.app.api.endpoints import intelligent_chat as chat_api

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
    try:
        print("📊 Tentando conectar ao banco de dados...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas do banco de dados criadas/verificadas com sucesso!")
    except Exception as e:
        print(f"⚠️  Aviso: Não foi possível conectar ao banco de dados: {e}")
        print("🔄 O servidor continuará funcionando, mas funcionalidades de BD estarão limitadas")

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


# Inclui o roteador do chat inteligente (apenas no prefixo correto)
app.include_router(chat_api.router, prefix="/api/v1/intelligent_chat", tags=["Intelligent Chat"])

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API do Sistema de Identificação de Público-Alvo"}
