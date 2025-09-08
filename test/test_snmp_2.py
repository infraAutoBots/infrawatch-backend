import asyncio
from pprint import pprint
from puresnmp import Client, V2C

OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
}

async def puresnmp_get(ip, community):
    client = Client(ip, V2C(community), port=161, timeout=10)  # Adicionado port e timeout maior
    results = {}
    for key, oid in OIDS.items():
        try:
            value = await client.get(oid)
            results[key] = str(value)
        except Exception as e:
            results[key] = None
            print(f"Erro ao consultar OID {oid}: {type(e).__name__} - {str(e)}")  # Imprime o erro para diagnóstico
    return results

async def main():
    ip = "127.0.0.1"
    community = "public"
    data = await puresnmp_get(ip, community)
    pprint(f"Resultado {ip}: {data}")

if __name__ == "__main__":
    asyncio.run(main())