import asyncio
from icmplib import async_multiping
from check_by_service import check_by_service
from snmp_get_data import get_snmp_info
from datetime import datetime
import os

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

