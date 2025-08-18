import logging
from check_tcp import check_tcp
from check_snmp import check_snmp


# Configuração de logging
logger = logging.getLogger(__name__)


async def check_by_service(ip: str) -> bool:
    """
    VERIFICAR SE UM IP ESTA ATIVO VIA SEUS SERVIÇOS
    """

    if await check_tcp(ip):
        logger.debug(f"IP {ip} ativo via TCP")
        return True
    # verificar se tem o snmp como requisito 
    is_snmp_alive = await check_snmp(ip)
    if is_snmp_alive:
        logger.debug(f"IP {ip} ativo via SNMP")
    return is_snmp_alive
