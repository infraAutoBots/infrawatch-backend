import asyncio
import logging
from typing import Dict
from icmplib import async_multiping
from check_by_service import check_by_service
from snmp_get_data import get_snmp_data
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
    '127.0.0.1': {'status': False, 'data': {}, 'last_updated': None},
    '127.0.0.2': {'status': False, 'data': {}, 'last_updated': None}
}
lock = asyncio.Lock()

none_data = {'sysDescr': None, 'cpu': None, 'disk': None, 'uptime': None, 'storage': None}

async def ping_ips(ips):
    """Pinga uma lista de IPs e retorna os que estão ativos.

    Args:
        ips (list): Lista de endereços IP a serem verificados.

    Returns:
        list: Lista de hosts ativos.
    """

    try:
        hosts = await async_multiping(ips, count=3, timeout=1.5, interval=0.05)
    except Exception as e:
        hosts = []
    return hosts


async def monitoring_loop(interval: int = 1):
    # Loop infinito para monitoramento periódico
    while True:
        try:
            async with lock:
                if not ips_status:
                    # await asyncio.sleep(interval)
                    continue
                ips = list(ips_status.keys())

            if ips:
                hosts = await ping_ips(ips)
                async with lock:
                    for host in hosts:
                        is_alive = host.avg_rtt > 0 or host.packets_received > 0
                        if not is_alive:
                            is_alive = await check_by_service(host.address)

                        if host.address in ips_status and is_alive:
                            ips_status[host.address]['status'] = is_alive
                            # verificar se o snmp esta ativo
                            try:
                                snmp_data = await get_snmp_data([host.address])
                                ips_status[host.address]['data'] = snmp_data[host.address]
                            except Exception:
                                ips_status[host.address]['data'] = none_data
                        else:
                            ips_status[host.address]['data'] = none_data
                        ips_status[host.address]['last_updated'] = datetime.now(timezone.utc)
                        print(f"{host.address} : {is_alive} : {ips_status[host.address]['data']}")



        except Exception as e:
            # logger.error(f"Erro no loop de monitoramento: {str(e)}")
            pass
        # await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(monitoring_loop())
