import asyncio
import logging
from typing import Dict
from icmplib import async_multiping
from check_by_service import check_by_service
from snmp_get_data import get_snmp_info
from datetime import datetime, timezone
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

# async def monitoring_loop(interval: int = int(os.getenv("MONITORING_INTERVAL", 1))):
async def monitoring_loop(interval: int = 1): # Intervalo em segundos
    # Loop infinito para monitoramento periódico
    while True:
        try:
            async with lock:
                if not ips_status:
                    # logger.debug("Nenhum IP para monitoramento. Aguardando...")
                    await asyncio.sleep(interval)
                    continue
                ips = list(ips_status.keys())



            if ips:

                # Verifica conectividade via ping
                try:
                    # Verifica conectividade via ping
                    hosts = await async_multiping(ips, count=3, timeout=float(os.getenv("TCP_TIMEOUT", 3)))
                    # logger.debug(f"Ping concluído para {len(ips)} IPs")
                except Exception as e:
                    # logger.error(f"Erro no ping: {str(e)}")
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
                                    # logger.info(f"SNMP atualizado para {host.address}: {snmp_data[host.address]}")
                                except Exception as e:
                                    # logger.error(f"Erro ao obter dados SNMP para {host.address}: {str(e)}")
                                    ips_status[host.address]['data'] = {"error": str(e)}
                            else:
                                ips_status[host.address]['data'] = {"error": "Host não está ativo"}
                            ips_status[host.address]['last_updated'] = datetime.now(timezone.utc)



                print("Status atualizado:")
                for ip, status in ips_status.items():
                    print(f" - {ip}: {'ativo' if status['status'] else 'inativo'} -> {status['last_updated']}")



        except Exception as e:
            # logger.error(f"Erro no loop de monitoramento: {str(e)}")
            pass
        # await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(monitoring_loop())
