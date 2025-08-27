import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Adicionar o diretório api ao path para permitir imports locais
sys.path.insert(0, os.path.dirname(__file__))

from auth_routes import auth_router
from monitor_routes import monitor_router
from users_routes import users_router



app = FastAPI(
    title="API de Monitoramento SNMP",
    description="API que gerencia dispositivos SNMP e coleta métricas em tempo real.",
    version="2.0.1"
)


# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(monitor_router)
app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
