import asyncio
from pprint import pprint
from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity
)

# Configurações SNMP
IPS = ["127.0.0.1"]
PORT = 161
COMMUNITY = "public"

# OIDs padrão da MIB-II (funcionam em qualquer dispositivo SNMP)
OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
}

async def snmp_get(ip):
    results = {}
    for key, oid in OIDS.items():
        try:
            errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                SnmpEngine(),
                CommunityData(COMMUNITY, mpModel=1),  # SNMPv2c
                await UdpTransportTarget.create((ip, PORT)),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            if errorIndication:
                results[key] = f"Erro: {errorIndication}"
            elif errorStatus:
                results[key] = f"Erro SNMP: {errorStatus.prettyPrint()}"
            else:
                for oid_obj, value in varBinds:
                    results[key] = str(value)
        except Exception as e:
            results[key] = f"Exceção: {e}"
    return {ip: results}

async def main():
    tasks = [snmp_get(ip) for ip in IPS]
    results = await asyncio.gather(*tasks)
    for r in results:
        pprint(r)

if __name__ == "__main__":
    asyncio.run(main())
