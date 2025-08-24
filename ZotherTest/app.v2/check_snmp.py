import asyncio
import logging
from ipaddress import ip_address
from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd, SnmpEngine, UdpTransportTarget, CommunityData, ContextData,
    ObjectType, ObjectIdentity, UsmUserData, usmHMACSHAAuthProtocol,
    usmAesCfb128Protocol
)
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os


# Carrega configurações do .env
load_dotenv()


# Configuração de logging
logger = logging.getLogger(__name__)


# Gerenciador de contexto para SnmpEngine
@asynccontextmanager
async def snmp_engine_manager():
    snmp_engine = SnmpEngine()
    try:
        yield snmp_engine
    finally:
        snmp_engine.transport_dispatcher.close_dispatcher()


async def check_snmp(
        ip: str, 
        version: str = os.getenv("SNMP_VERSION", "2c"),
        community: str = os.getenv("SNMP_COMMUNITY", "public"),
        port: int = int(os.getenv("SNMP_PORT", 161)),
        user: str = os.getenv("SNMP_USER", "meuUser"),
        authKey: str | None = os.getenv("SNMP_AUTH_KEY", None),
        privKey: str | None = os.getenv("SNMP_PRIV_KEY", None)) -> bool:
    """
    Verifica conexão SNMP para v1, v2c ou v3.
    Para v3: Se authKey/privKey forem None → noAuthNoPriv
             Se authKey existir sem privKey → authNoPriv
             Se authKey e privKey existirem → authPriv
    """
    try:
        ip_address(ip)
    except ValueError:
        logger.error(f"IP inválido em check_snmp: {ip}")
        return False

    async with snmp_engine_manager() as snmp_engine:
        try:
            if version not in ["1", "2c", "3"]:
                logger.error(f"Versão SNMP inválida: {version}")
                raise ValueError(f"Unsupported SNMP version: {version}")

            if version in ["1", "2c"]:
                auth_data = CommunityData(community, mpModel=0 if version == "1" else 1)
            else:
                # Configura credenciais dependendo do caso
                if authKey and privKey:
                    auth_data = UsmUserData(
                        userName=user,
                        authKey=authKey,
                        privKey=privKey,
                        authProtocol=usmHMACSHAAuthProtocol,
                        privProtocol=usmAesCfb128Protocol,
                    )
                elif authKey:
                    auth_data = UsmUserData(
                        userName=user,
                        authKey=authKey,
                        authProtocol=usmHMACSHAAuthProtocol,
                    )
                else:
                    auth_data = UsmUserData(user)

            error_indication, error_status, error_index, _ = await get_cmd(
                snmp_engine,
                auth_data,
                await UdpTransportTarget.create((ip, port), timeout=float(os.getenv("SNMP_TIMEOUT", 1)), retries=int(os.getenv("SNMP_RETRIES", 0))),
                ContextData(),
                ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0))
            )

            if error_indication or error_status or error_index:
                logger.debug(f"Falha SNMP para {ip}: {error_indication or error_status.prettyPrint()}")
                return False
            logger.debug(f"SNMP bem-sucedido para {ip}")
            return True
        except Exception as e:
            logger.debug(f"Exceção em check_snmp para {ip}: {str(e)}")
            return False


if __name__ == "__main__":
    async def main():
        # Teste SNMPv2c (via PySNMP)
        ok = await check_snmp("127.0.0.1", version="2c", community="public", port=161)
        logger.info("Resultado SNMPv2c: %s", ok)

        # Teste SNMPv3 (via PySNMP) – ajuste para credenciais se quiser autenticação real
        # ok = await check_snmp("demo.pysnmp.com", version="3")
        # logger.info("Resultado SNMPv3: %s", ok)

    asyncio.run(main())
