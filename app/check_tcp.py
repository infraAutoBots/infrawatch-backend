import asyncio
import logging
from typing import List
from check_snmp import check_snmp
from ipaddress import ip_address
from dotenv import load_dotenv
import os



# Carrega configurações do .env
load_dotenv()


# Configuração de logging
logger = logging.getLogger(__name__)


async def check_tcp(ip: str, timeout: float = float(os.getenv("TCP_TIMEOUT", 3))) -> bool:
    """
    Verifica se uma conexão TCP pode ser estabelecida com o IP e porta especificados.
    80 (HTTP), 443 (HTTPS), 3306 (MySQL), 5432 (PostgreSQL), 53 (DNS), 161 (SNMP)
    """

    try:
        ip_address(ip)
    except ValueError:
        logger.error(f"IP inválido em check_tcp: {ip}")
        return False

    port_list: List[int] = [int(p) for p in os.getenv("TCP_PORTS", "80,443,3306,5432,53,161").split(",")]
    for port in port_list:
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout)
            writer.close()
            await writer.wait_closed()
            logger.debug(f"TCP check bem-sucedido para {ip}:{port}")
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            logger.debug(f"TCP check falhou para {ip}:{port}: {str(e)}")
            pass
    if (await check_snmp(ip)):
        logger.debug(f"IP {ip} ativo via SNMP")
        return True  # Se o SNMP estiver funcionando, consideramos o IP como ativo
    return False


if __name__ == "__main__":
    async def main():
        ok = await check_tcp("127.0.0.1")
        logger.info("Resultado TCP: %s", ok)

    asyncio.run(main())
