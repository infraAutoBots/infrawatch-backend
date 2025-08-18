import uvicorn
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import Dict
from icmplib import async_multiping
from check_by_service import check_by_service
from snmp_get_data import get_snmp_info
from ipaddress import ip_address
from datetime import datetime
from dotenv import load_dotenv
import os


# Carrega configurações do .env
load_dotenv()


# Configuração de logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Estado compartilhado: dict de IPs e status (True: alive, False: dead)
ips_status: Dict[str, Dict[str, bool]] = {
    '192.168.8.159': {'status': False, 'data': {}, 'last_updated': None},
    '192.168.8.146': {'status': False, 'data': {}, 'last_updated': None},
    '192.168.8.121': {'status': False, 'data': {}, 'last_updated': None},
    '127.0.0.1': {'status': False, 'data': {}, 'last_updated': None}
}
lock = asyncio.Lock()


async def monitoring_loop(interval: int = int(os.getenv("MONITORING_INTERVAL", 60))):
    # Loop infinito para monitoramento periódico
    while True:
        try:
            async with lock:
                if not ips_status:
                    logger.debug("Nenhum IP para monitoramento. Aguardando...")
                    await asyncio.sleep(interval)
                    continue
                ips = list(ips_status.keys())
            if ips:
                try:
                    # Verifica conectividade via ping
                    hosts = await async_multiping(ips, count=3, timeout=float(os.getenv("TCP_TIMEOUT", 3)))
                    logger.debug(f"Ping concluído para {len(ips)} IPs")
                except Exception as e:
                    logger.error(f"Erro no ping: {str(e)}")
                    hosts = []
                async with lock:
                    for host in hosts:
                        is_alive = host.avg_rtt > 0 or host.packets_received > 0
                        if not is_alive:
                            # Verifica serviços (TCP/SNMP) se o ping falhar
                            is_alive = await check_by_service(host.address)
                        if host.address in ips_status:
                            ips_status[host.address]['status'] = is_alive
                            # Verificar se tem o snmp como requisito
                            if is_alive:
                                try:
                                    # Aguarda o resultado do SNMP
                                    snmp_data = await get_snmp_info(
                                        [host.address],
                                        version=os.getenv("SNMP_VERSION", "2c"),
                                        community=os.getenv("SNMP_COMMUNITY", "public"),
                                        port=int(os.getenv("SNMP_PORT", 161)),
                                        timeout=float(os.getenv("SNMP_TIMEOUT", 10.0)),
                                        retries=int(os.getenv("SNMP_RETRIES", 2))
                                    )
                                    ips_status[host.address]['data'] = snmp_data[host.address]
                                    logger.info(f"SNMP atualizado para {host.address}: {snmp_data[host.address]}")
                                except Exception as e:
                                    logger.error(f"Erro ao obter dados SNMP para {host.address}: {str(e)}")
                                    ips_status[host.address]['data'] = {"error": str(e)}
                            else:
                                ips_status[host.address]['data'] = {"error": "Host não está ativo"}
                            ips_status[host.address]['last_updated'] = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Erro no loop de monitoramento: {str(e)}")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o loop de monitoramento ao iniciar a API
    task = asyncio.create_task(monitoring_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.post("/add/{ip}")
async def add_ip(ip: str):
    # Valida o IP
    try:
        ip_address(ip)
    except ValueError:
        logger.error(f"Tentativa de adicionar IP inválido: {ip}")
        raise HTTPException(status_code=400, detail="IP inválido")
    async with lock:
        if ip in ips_status:
            logger.warning(f"Tentativa de adicionar IP já existente: {ip}")
            raise HTTPException(status_code=400, detail="IP já existe")
        ips_status[ip] = {'status': False, 'data': {}, 'last_updated': None}
        logger.info(f"IP {ip} adicionado")
    return {"message": f"IP {ip} adicionado"}


@app.delete("/remove/{ip}")
async def remove_ip(ip: str):
    async with lock:
        if ip not in ips_status:
            logger.warning(f"Tentativa de remover IP não encontrado: {ip}")
            raise HTTPException(status_code=404, detail="IP não encontrado")
        del ips_status[ip]
        logger.info(f"IP {ip} removido")
    return {"message": f"IP {ip} removido"}


@app.get("/status")
async def get_status():
    async with lock:
        logger.info("Consulta de status realizada")
        return ips_status.copy()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
