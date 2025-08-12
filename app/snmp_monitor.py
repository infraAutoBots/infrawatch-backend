# - Usa pysnmp com asyncio para get async de OIDs.
# - OIDs exemplos: Genéricos (sysUpTime .1.3.6.1.2.1.1.3.0),
#     CPU para Cisco (.1.3.6.1.4.1.9.9.109.1.1.1.1.5),
#     Mikrotik (.1.3.6.1.4.1.14988.1.1.3.10.0),
#     tráfego (ifInOctets .1.3.6.1.2.1.2.2.1.10),
#     temperatura (ex: para Cisco .1.3.6.1.4.1.9.9.13.1.3.1.3),
#     status portas (ifOperStatus .1.3.6.1.2.1.2.2.1.8).
# - Suporta v1, v2c, v3.
# - Retorna dict com dados.

from typing import Dict
from pysnmp.hlapi.asyncio import (ObjectIdentity, CommunityData, UsmUserData, 
                                  SnmpEngine, UdpTransportTarget, ContextData, 
                                  ObjectType, get_cmd, usmHMACMD5AuthProtocol, 
                                  usmDESPrivProtocol)


OIDS = {
    "uptime": ObjectIdentity('1.3.6.1.2.1.1.3.0'),  # noqa: F405
    "cpu_cisco": ObjectIdentity('1.3.6.1.4.1.9.9.109.1.1.1.1.5.1'),  # Exemplo Cisco  # noqa: F405
    "cpu_mikrotik": ObjectIdentity('1.3.6.1.4.1.14988.1.1.3.10.0'),
    "traffic_in": ObjectIdentity('1.3.6.1.2.1.2.2.1.10.1'),  # ifInOctets interface 1
    "temp_cisco": ObjectIdentity('1.3.6.1.4.1.9.9.13.1.3.1.3.1'),  # Exemplo
    "port_status": ObjectIdentity('1.3.6.1.2.1.2.2.1.8.1'),  # ifOperStatus port 1
    # Adicione mais OIDs genéricos/específicos
}


async def get_snmp_data(ip: str, config: Dict) -> Dict:
    data = {}
    auth = None
    if config["snmp_version"] == "v1":
        auth = CommunityData(config["snmp_community"], mpModel=0)
    elif config["snmp_version"] == "v2c":
        auth = CommunityData(config["snmp_community"])
    elif config["snmp_version"] == "v3":
        auth = UsmUserData(
            config["snmp_user"],
            authProtocol=getattr(usmHMACMD5AuthProtocol, config["snmp_auth_protocol"], None),
            authPassword=config["snmp_auth_password"],
            privProtocol=getattr(usmDESPrivProtocol, config["snmp_priv_protocol"], None),
            privPassword=config["snmp_priv_password"]
        )
    else:
        return {"error": "Invalid SNMP version"}

    engine = SnmpEngine()
    for name, oid in OIDS.items():
        try:
            # em caso de erro no get_cmd.
            # Mude get_cmd para getCmd e a importacao para from pysnmp.hlapi.asyncio import *
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(  # noqa: F405
                engine,
                auth,
                UdpTransportTarget((ip, 161)),
                ContextData(),
                ObjectType(oid)
            )
            if errorIndication:
                continue
            for varBind in varBinds:
                data[name] = str(varBind[1])
        except Exception:
            pass
    return data
