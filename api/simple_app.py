"""
Versão simplificada da aplicação InfraWatch para debugging no Railway
"""
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Aplicação FastAPI simples
app = FastAPI(
    title="InfraWatch API (Simple Mode)",
    description="API de Monitoramento SNMP - Modo Simplificado para Debug",
    version="2.0.1"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """Health check básico."""
    return {
        "status": "ok", 
        "service": "infrawatch-api",
        "mode": "simple",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def detailed_health():
    """Health check detalhado."""
    return {
        "status": "healthy",
        "message": "InfraWatch API está rodando em modo simplificado",
        "version": "2.0.1",
        "mode": "simple",
        "environment": {
            "port": os.getenv("PORT", "8000"),
            "host": "0.0.0.0"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/info")
async def app_info():
    """Informações da aplicação."""
    return {
        "name": "InfraWatch API",
        "version": "2.0.1",
        "status": "running",
        "mode": "simple",
        "description": "API de Monitoramento SNMP em modo simplificado"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
