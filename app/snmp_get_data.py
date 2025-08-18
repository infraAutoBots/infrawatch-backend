import asyncio
import logging
from typing import Dict, Any, Optional, List
from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd, SnmpEngine, UdpTransportTarget,
    CommunityData, ContextData, ObjectType, ObjectIdentity, UsmUserData
)
from ipaddress import ip_address
from contextlib import asynccontextmanager
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


# ----------------------------------------
# Dicionário de OIDs: padrões + fabricantes
# ----------------------------------------
OIDS = {
    "sysDescr": [
        "1.3.6.1.2.1.1.1.0",  # padrão
    ],
    "cpu": [
        "1.3.6.1.4.1.2021.11.9.0",   # UCD-SNMP CPU idle
        "1.3.6.1.4.1.9.2.1.57.0",    # Cisco CPU
        "1.3.6.1.4.1.2636.3.1.13.1.8.0",  # Juniper CPU
        "1.3.6.1.4.1.2021.11.50.0",  # Linux CPU system
        "1.3.6.1.4.1.2021.11.52.0",  # Linux CPU user
    ],
    "disk": [
        "1.3.6.1.4.1.2021.9.1.6.1",   # UCD-SNMP disk
        "1.3.6.1.4.1.9.9.305.1.1.1.0", # Cisco Disk
        "1.3.6.1.4.1.2636.3.1.13.1.11.0", # Juniper Disk
    ],
    "uptime": [
        "1.3.6.1.2.1.1.3.0",  # padrão sysUpTime
    ],
    "storage": [
        "1.3.6.1.4.1.2021.4.6.0",   # UCD-SNMP memory free
        "1.3.6.1.4.1.9.2.1.8.0",    # Cisco memory
        "1.3.6.1.4.1.2636.3.1.13.1.15.0", # Juniper memory
        "1.3.6.1.4.1.2021.4.5.0",   # Linux total RAM
    ]
}


# ----------------------------------------
# Gerenciador de contexto para SnmpEngine
# ----------------------------------------
@asynccontextmanager
async def snmp_engine_manager():
    snmp_engine = SnmpEngine()
    try:
        yield snmp_engine
    finally:
        snmp_engine.transport_dispatcher.close_dispatcher()


# ----------------------------------------
# Função unificada para SNMP v1/v2c/v3 (PySNMP)
# ----------------------------------------
async def snmp_get(ip: str, version: str, community: str, user: str, auth_key: str, priv_key: str, 
                  port: int, key: str, timeout: float = float(os.getenv("SNMP_TIMEOUT", 10.0)), 
                  retries: int = int(os.getenv("SNMP_RETRIES", 2))) -> Optional[str]:
    async with snmp_engine_manager() as snmp_engine:
        for oid in OIDS[key]:
            try:
                if version not in ("1", "2c", "3"):
                    logger.error(f"Versão SNMP inválida: {version}")
                    return None

                if version in ("1", "2c"):
                    auth_data = CommunityData(community, mpModel=0 if version == "1" else 1)
                else:
                    auth_data = UsmUserData(user, auth_key, priv_key)

                error_indication, error_status, error_index, var_binds = await get_cmd(
                    snmp_engine,
                    auth_data,
                    await UdpTransportTarget.create((ip, port), timeout=timeout, retries=retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid))
                )

                if error_indication:
                    logger.debug(f"Falha no OID {oid} para {ip}: {error_indication}")
                    continue
                elif error_status:
                    logger.debug(f"Falha no OID {oid} para {ip}: {error_status.prettyPrint()} at {error_index and var_binds[int(error_index) - 1][0] or '?'}")
                    continue
                else:
                    return str(var_binds[0][1])

            except Exception as e:
                logger.debug(f"Exceção no OID {oid} para {ip}: {type(e).__name__} - {str(e)}")
                continue
        return None


# ----------------------------------------
# Função principal para coletar dados de múltiplos IPs
# ----------------------------------------
async def get_snmp_info(
    ips: List[str], version: str = os.getenv("SNMP_VERSION", "2c"),
    community: str = os.getenv("SNMP_COMMUNITY", "public"),
    user: str = os.getenv("SNMP_USER", ""),
    auth_key: str = os.getenv("SNMP_AUTH_KEY", ""),
    priv_key: str = os.getenv("SNMP_PRIV_KEY", ""),
    port: int = int(os.getenv("SNMP_PORT", 161)),
    timeout: float = float(os.getenv("SNMP_TIMEOUT", 10.0)),
    retries: int = int(os.getenv("SNMP_RETRIES", 2))) -> Dict[str, Dict[str, Any]]:
    """
    Coleta informações via SNMP (sysDescr, cpu, disk, uptime, storage) para múltiplos IPs.
    Usa PySNMP para v1, v2c e v3.
    """
    # Validação de IPs
    for ip in ips:
        try:
            ip_address(ip)
        except ValueError:
            logger.error(f"IP inválido: {ip}")
            return {ip: {"error": f"IP inválido: {ip}"}}

    results = {}
    tasks = []
    
    for ip in ips:
        result = {key: None for key in OIDS.keys()}
        for key in OIDS.keys():
            tasks.append(snmp_get(ip, version, community, user, auth_key, priv_key, port, key, timeout, retries))
        results[ip] = result

    # Executa consultas em paralelo
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Atribui resultados aos IPs
    task_index = 0
    for ip in ips:
        for key in OIDS.keys():
            result = responses[task_index]
            if isinstance(result, Exception):
                results[ip][key] = f"Error: {str(result)}"
            else:
                results[ip][key] = result
            task_index += 1

    return results


# ---------------------------
# Teste
# ---------------------------
if __name__ == "__main__":
    async def main():
        ips = ["127.0.0.1"]
        result = await get_snmp_info(ips)
        for ip, data in result.items():
            logger.info(f"Resultado {ip}: {data}")

    asyncio.run(main())
