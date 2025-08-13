#!/usr/bin/env python3
"""
Script para inicializar o servidor FastAPI de forma robusta.
Este script resolve problemas comuns de importação e configuração.
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configurações do ambiente
os.environ.setdefault('PYTHONPATH', str(backend_path))

if __name__ == "__main__":
    import uvicorn
    
    # Configurações do servidor
    config = {
        "app": "nlp_processor.app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "reload_dirs": [str(backend_path)],
        "log_level": "info"
    }
    
    print(f"🚀 Iniciando servidor FastAPI...")
    print(f"📁 Diretório backend: {backend_path}")
    print(f"🔗 Servidor disponível em: http://localhost:8000")
    print(f"📚 Documentação da API: http://localhost:8000/docs")
    
    uvicorn.run(**config)
