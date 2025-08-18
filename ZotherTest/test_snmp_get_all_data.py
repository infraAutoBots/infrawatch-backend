import asyncio
from puresnmp import Client, V2C, PyWrapper
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, UdpTransportTarget, ContextData,
    CommunityData, ObjectType, ObjectIdentity,
    bulk_cmd
)

# ---------------------------
# SNMP v1 / v2c (PureSNMP)
# ---------------------------
async def fetch_all_v1_v2c(ip: str, community: str = "public", port: int = 161):
    try:
        client = PyWrapper(Client(ip, V2C(community), port=port))
        # Caminho mais comum é iniciar em 1.3.6 (MIB-2)
        async for oid, value in client.walk("1.3.6"):
            print(f"[{ip}] {oid} = {value}")
        return True
    except Exception as e:
        print(f"[PureSNMP v2c/v1] Erro {ip}: {e}")
        return False

# ---------------------------
# SNMP v3 (PySNMP)
# ---------------------------
async def fetch_all_v3(ip: str, community: str = "public", port: int = 161):
    try:
        # Aqui estou a usar CommunityData para simplificar, mas o correto em v3 é UsmUserData
        iterator = bulk_cmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),  # v2c-like, mas pode trocar para UsmUserData p/ v3 real
            await UdpTransportTarget.create((ip, port), timeout=1, retries=0),
            ContextData(),
            0,   # non-repeaters
            25,  # max-repetitions
            ObjectType(ObjectIdentity("1.3.6"))  # começa na MIB-2
        )

        while True:
            errorIndication, errorStatus, errorIndex, varBinds = await iterator
            if errorIndication or errorStatus:
                print(f"[PySNMP v3] Erro {ip}: {errorIndication or errorStatus.prettyPrint()}")
                break

            for oid, val in varBinds:
                print(f"[{ip}] {oid.prettyPrint()} = {val.prettyPrint()}")

            if not varBinds:
                break

        return True
    except Exception as e:
        print(f"[PySNMP v3] Erro {ip}: {e}")
        return False

# ---------------------------
# Função genérica
# ---------------------------
async def fetch_all(ip: str, version: str = "2c", community: str = "public", port: int = 161):
    if version in ["1", "2c"]:
        return await fetch_all_v1_v2c(ip, community, port)
    elif version == "3":
        return await fetch_all_v3(ip, community, port)
    else:
        raise ValueError(f"Versão SNMP não suportada: {version}")

# ---------------------------
# Exemplo de uso
# ---------------------------
if __name__ == "__main__":
    # Puxa tudo do SNMPv2c
    ips:list = ["127.0.0.1", "127.0.0.2", "127.0.0.3", 
                "127.0.0.4", "127.0.0.5", "127.0.0.6",
                "127.0.0.7", "127.0.0.8", "127.0.0.9",
                "127.0.0.10", "127.0.0.11", "127.0.0.12"]
    for ip in ips:
        asyncio.run(fetch_all(ip, version="2c", community="public"))

    # Se quiser puxar em SNMPv3 (com credenciais reais deveria trocar para UsmUserData)
    # asyncio.run(fetch_all("demo.pysnmp.com", version="3"))
