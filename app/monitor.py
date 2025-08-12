# 4. monitor.py
# - Lógica principal do loop de monitoramento assíncrono.
# - Para cada IP: Loop infinito com sleep(interval).
# - Primeiro tenta ping; se falhar, verifica serviços confirmados.
# - Se online, verifica todos serviços e atualiza confirmados.
# - Então, faz SNMP get.
# - Loga status no DB.
# - Se mudança de status, envia webhook.

import asyncio
from icmplib import async_ping
from services import check_services
from snmp_monitor import get_snmp_data
from webhook import send_webhook
from app.database import log_status, get_confirmed_services, update_confirmed_services
from typing import Dict


async def start_monitoring_loop(ip: str, config: Dict):
    last_online = False
    while True:
        # Passo 1: Verificar online
        is_online = await check_online(ip, config)
        services = []
        snmp_data = {}
        if is_online:
            # Passo 1.1: Verificar serviços
            services = await check_services(ip)
            await update_confirmed_services(ip, services)
            # Passo 2: SNMP
            snmp_data = await get_snmp_data(ip, config)

        # Log status
        await log_status(ip, is_online, services, snmp_data)

        # Webhook se mudança
        if is_online != last_online and config.get("webhook_url"):
            message = f"IP {ip} changed to {'online' if is_online else 'offline'}"
            await send_webhook(config["webhook_url"], {"message": message, "services": services, "snmp": snmp_data})
        last_online = is_online

        await asyncio.sleep(config["interval_seconds"])


async def check_online(ip: str, config: Dict) -> bool:
    # Tenta ping
    ping_result = await async_ping(ip, count=1, timeout=2)
    if ping_result.is_alive:
        return True
    # Se falhar, verifica serviços confirmados
    confirmed = await get_confirmed_services(ip)
    if confirmed:
        active_services = await check_services(ip, only_these=confirmed)
        return bool(active_services)
    return False

