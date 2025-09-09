import os
import uvicorn
import asyncio
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Detecta se está sendo executado diretamente ou como módulo
if __name__ == "__main__":
    # Quando executado diretamente (python api/app.py)
    # Adiciona o diretório pai ao PYTHONPATH
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from api.auth_routes import auth_router
    from api.monitor_routes import monitor_router
    from api.users_routes import users_router
    from api.alert_routes import alert_router
    from api.config_routes import config_router
    from api.sla_routes import sla_router
    from api.monitor import OptimizedMonitor
else:
    # Quando importado como módulo (uvicorn api.app:app)
    try:
        # Tenta imports absolutos primeiro
        from api.auth_routes import auth_router
        from api.monitor_routes import monitor_router
        from api.users_routes import users_router
        from api.alert_routes import alert_router
        from api.config_routes import config_router
        from api.sla_routes import sla_router
        from api.monitor import OptimizedMonitor
    except ImportError:
        # Fallback para imports relativos se absolutos falharem
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
    
    # Inicializar banco de dados
    try:
        print("🗄️ Inicializando banco de dados...")
        from .models import Base, db, get_database_url
        
        db_url = get_database_url()
        print(f"📊 Conectando ao banco: {db_url[:50]}...")
        
        # Criar todas as tabelas
        Base.metadata.create_all(bind=db)
        print("✅ Tabelas do banco de dados criadas/verificadas com sucesso!")
        
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco de dados: {e}")
        print("📡 API pode funcionar com funcionalidade limitada")
    
    monitoring_task = None
    try:
        print("🚀 Tentando inicializar monitoramento...")
        # Inicializar o monitor de forma segura
        monitor = OptimizedMonitor(logger=False)
        
        # Criar uma task em background para o monitoramento
        monitoring_task = asyncio.create_task(monitor.run_monitoring(interval=90.0))
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


@app.get("/db-status")
async def database_status():
    """Verifica o status da conexão com o banco de dados."""
    try:
        from .models import get_database_url, db
        import os
        
        db_url = get_database_url()
        
        # Testar conexão
        with db.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            
        return {
            "status": "connected",
            "database_type": "postgresql" if "postgres" in db_url else "sqlite",
            "database_url": db_url[:50] + "..." if len(db_url) > 50 else db_url,
            "connection_test": "successful",
            "environment": {
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
                "DATABASE_URL_SET": bool(os.getenv("DATABASE_URL"))
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_url": "unknown"
        }


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
