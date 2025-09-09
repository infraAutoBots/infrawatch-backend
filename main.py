#!/usr/bin/env python3
"""
Script principal para rodar a aplicação localmente
"""
import os
import sys
import uvicorn

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",  # String de import em vez do objeto
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True
    )
