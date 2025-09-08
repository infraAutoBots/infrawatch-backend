import asyncio
from typing import List
from check_snmp import check_snmp

async def check_tcp(ip: str, timeout: float = 3) -> bool:
    """
    Verifica se uma conexão TCP pode ser estabelecida com o IP e porta especificados.
    80 (HTTP), 443 (HTTPS), 3306 (MySQL), 5432 (PostgreSQL), 53 (DNS), 161 (SNMP)
    """
    port_list: List[int] = [80, 443, 3306, 5432, 53]
    for port in port_list:
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
            writer.close()
            await writer.wait_closed()
            # print(f"TCP check bem-sucedido para {ip}:{port}")
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # print(f"TCP check falhou para {ip}:{port}: {e}")
            pass
    if (await check_snmp(ip)):
        return True  # Se o SNMP estiver funcionando, consideramos o IP como ativo
    return False

if __name__ == '__main__':
    asyncio.run(check_tcp('127.0.0.1'))