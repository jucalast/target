# Shared Components Documentation

## Visão Geral
Os componentes compartilhados são a espinha dorsal do sistema, fornecendo funcionalidades essenciais e modelos de dados reutilizáveis em todos os módulos.

## Estrutura de Diretórios

```
shared/
├── models/           # Modelos de banco de dados
├── schemas/          # Esquemas Pydantic para validação
├── utils/            # Utilitários comuns
└── config.py         # Configurações globais
```

## Modelos de Dados Principais

### 1. Usuário (`models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 2. Análise (`models/analysis.py`)
```python
class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    niche = Column(String)
    description = Column(Text)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="analyses")
    results = relationship("AnalysisResult", back_populates="analysis")
```

## Esquemas de Validação

### 1. Usuário (`schemas/user.py`)
```python
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    
    class Config:
        orm_mode = True
```

### 2. Análise (`schemas/analysis.py`)
```python
class AnalysisBase(BaseModel):
    niche: str
    description: str

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisInDB(AnalysisBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True
```

## Utilitários Compartilhados

### 1. Banco de Dados (`utils/database.py`)
- Gerenciamento de sessões do SQLAlchemy
- Configuração de conexão com o banco de dados
- Funções auxiliares para transações

### 2. Segurança (`utils/security.py`)
- Geração e verificação de hash de senha
- Funções JWT (JSON Web Tokens)
- Middleware de autenticação

### 3. Logging (`utils/logger.py`)
- Configuração centralizada de logs
- Formatação consistente
- Níveis de log configuráveis

## Configurações Globais (`config.py`)

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Identificação de Público-Alvo"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Segurança
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    
    # Banco de Dados
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Padrões de Código

1. **Nomenclatura**
   - Classes: `PascalCase`
   - Variáveis e funções: `snake_case`
   - Constantes: `UPPER_SNAKE_CASE`

2. **Documentação**
   - Docstrings em inglês
   - Tipagem explícita
   - Exemplos de uso

3. **Tratamento de Erros**
   - Exceções específicas por domínio
   - Mensagens de erro claras e úteis
   - Logs detalhados

## Próximos Passos
1. Adicionar mais modelos de dados conforme necessário
2. Implementar migrações de banco de dados
3. Adicionar testes unitários para utilitários
4. Melhorar documentação de código
5. Implementar cache distribuído
