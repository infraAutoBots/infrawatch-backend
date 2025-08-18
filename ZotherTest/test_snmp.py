import asyncio
from pysnmp.hlapi.v3arch.asyncio import *

# Configurações do agente SNMP
IP = ['127.0.0.1', '127.0.0.2', '127.0.0.3']
PORT = 161
COMMUNITY = 'public'
OID_CPU_LOAD = '..1.3.6.1.2.1.25.3.2.1.3.1025'  # hrProcessorLoad do seu simulador

async def get_cpu_usage():
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData(COMMUNITY, mpModel=1),  # SNMPv2c
        await UdpTransportTarget.create((IP[1], PORT)),
        ContextData(),
        ObjectType(ObjectIdentity(OID_CPU_LOAD))
    )

    if errorIndication:
        print(f"Erro: {errorIndication}")
        return

    if errorStatus:
        print(f"Erro SNMP: {errorStatus.prettyPrint()} no índice {errorIndex}")
        return

    if varBinds:
        oid, value = varBinds[0]
        try:
            cpu_usage = int(value)  # Já retorna o uso em %
            print(f"CPU Usage: {cpu_usage}%")
        except ValueError:
            print(f"O valor retornado não é numérico: {value}")
    else:
        print("Nenhum valor retornado.")

if __name__ == '__main__':
    asyncio.run(get_cpu_usage())
