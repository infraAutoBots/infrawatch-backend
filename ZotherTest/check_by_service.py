from check_tcp import check_tcp
from check_snmp import check_snmp

async def check_by_service(ip: str) -> bool:
    """
    VERIFICAR SE UM IP ESTA ATIVO VIA SEUS SERVIÇOS
    """
    if await check_tcp(ip):
        return True
    # verificar se tem o snmp como requisito
    return await check_snmp(ip)
