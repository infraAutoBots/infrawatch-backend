import asyncio
from puresnmp import Client, V2C, PyWrapper
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, SnmpEngine, UdpTransportTarget,
                                         ContextData, UsmUserData, ObjectType,
                                         ObjectIdentity, usmHMACSHAAuthProtocol,
                                         usmAesCfb128Protocol)

async def check_snmp_v1_v2c(ip: str, community: str, oid: str, port: int) -> bool:
    try:
        client = PyWrapper(Client(ip, V2C(community), port=port))
        await client.get(oid)
        return True
    except Exception:
        return False


async def check_snmp_v3(
    ip: str,
    port: int,
    user: str,
    authKey: str | None,
    privKey: str | None,
) -> bool:
    """
    Verifica conexão SNMPv3.
    Se authKey/privKey forem None → noAuthNoPriv
    Se authKey existir sem privKey → authNoPriv
    Se authKey e privKey existirem → authPriv
    """

    try:
        # 🔑 Configura credenciais dependendo do caso
        if authKey and privKey:
            user_data = UsmUserData(
                userName=user,
                authKey=authKey,
                privKey=privKey,
                authProtocol=usmHMACSHAAuthProtocol,
                privProtocol=usmAesCfb128Protocol,
            )
        elif authKey:  # só autenticação
            user_data = UsmUserData(
                userName=user,
                authKey=authKey,
                authProtocol=usmHMACSHAAuthProtocol,
            )
        else:  # sem autenticação nem privacidade
            user_data = UsmUserData(user)

        iterator = get_cmd(
            SnmpEngine(),
            user_data,
            await UdpTransportTarget.create((ip, port), timeout=1, retries=0),
            ContextData(),
            ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0))
        )

        errorIndication, errorStatus, errorIndex, _ = await iterator
        if errorIndication or errorStatus or errorIndex:
            return False
        return True
    except Exception:
        return False


async def check_snmp(
        ip: str, 
        version: str = "2c",
        community: str = "public",
        port: int = 161,
        user: str = "meuUser",
        authKey: str | None = None,
        privKey: str | None = None) -> bool:

    if version in ["1", "2c"]:
        return await check_snmp_v1_v2c(ip, community, "1.3.6.1.2.1.1.1.0", port)
    elif version == "3":
        return await check_snmp_v3(ip, port=port, user=user, authKey=authKey, privKey=privKey)
    raise ValueError(f"Unsupported SNMP version: {version}")

if __name__ == "__main__":
    # Teste SNMPv2c (via PureSNMP)
    ok = asyncio.run(check_snmp("127.0.0.2", version="2c", community="public", port=161))
    print("Resultado SNMPv2c:", ok)

    # Teste SNMPv3 (via PySNMP) – ajuste para credenciais se quiser autenticação real
    # ok = asyncio.run(check_snmp("demo.pysnmp.com", version="3"))
    # print("Resultado SNMPv3:", ok)
