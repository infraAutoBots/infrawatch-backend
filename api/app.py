import os
import uvicorn
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth_routes import auth_router
from .monitor_routes import monitor_router
from .users_routes import users_router
from .alert_routes import alert_router
from .config_routes import config_router
from .sla_routes import sla_router

from .monitor import OptimizedMonitor




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código executado ANTES da API iniciar
    print("⚡ Iniciando InfraWatch API...")
    
    monitoring_task = None
    try:
        print("🚀 Tentando inicializar monitoramento...")
        # Inicializar o monitor de forma segura
        monitor = OptimizedMonitor(logger=False)
        
        # Criar uma task em background para o monitoramento
        monitoring_task = asyncio.create_task(monitor.run_monitoring(interval=30.0))
        print("✅ Monitoramento iniciado em background!")
        
    except Exception as e:
        print(f"⚠️ Não foi possível inicializar o monitoramento: {e}")
        print("📡 API funcionando sem monitoramento automático")
    
    yield  # A API roda aqui
    
    # Código executado APÓS a API encerrar
    if monitoring_task:
        print("🔄 Encerrando monitoramento...")
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            print("✅ Monitoramento encerrado com sucesso!")
    print("👋 API encerrada!")


app = FastAPI(
    title="API de Monitoramento SNMP",
    description="API que gerencia dispositivos SNMP e coleta métricas em tempo real.",
    version="2.0.1",
    lifespan=lifespan
)


# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Rota de health check simples - deve responder rapidamente
@app.get("/")
async def health_check():
    """Endpoint de health check básico."""
    return {"status": "ok", "service": "infrawatch-api"}


@app.get("/health")
async def detailed_health_check():
    """Endpoint de health check detalhado."""
    try:
        return {
            "status": "healthy",
            "message": "InfraWatch API está funcionando!",
            "version": "2.0.1",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


app.include_router(auth_router)
app.include_router(monitor_router)
app.include_router(users_router)
app.include_router(alert_router)
app.include_router(config_router)
app.include_router(sla_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
