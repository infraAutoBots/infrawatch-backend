import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
from icmplib import async_multiping
from typing import Dict, List
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, SnmpEngine, CommunityData, UdpTransportTarget,
                                         ContextData, ObjectType, ObjectIdentity)


# Estado compartilhado: dict de IPs e status (True: alive, False: dead)
ips_status: Dict[str, Dict[str, bool]] = {
    '192.168.8.159': {'status': False, 'data': []},
    '192.168.8.146': {'status': False, 'data': []},
    '192.168.8.121': {'status': False, 'data': []}
}
lock = asyncio.Lock()

def get_version(version:str) -> int:
    """
    Get the SNMP version number.

    Args:
        version (str): The SNMP version as a string (e.g., '1', '2c', '3').

    Raises:
        ValueError: If the SNMP version is unsupported.

    Returns:
        int: The SNMP version number.
    """
    if version == '1':
        return 0
    if version == '2c':
        return 1
    elif version == '3':
        return 2
    raise ValueError(f"Unsupported SNMP version: {version}")

async def check_snmp(ip: str, community: str = 'public', port: int = 161, version: str = '2c') -> bool:
    """
    Test SNMP connectivity and retrieve system description.
    """
    iterator = get_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=get_version(version)),  # mpModel=1 → SNMPv2c
        await UdpTransportTarget.create((ip, port),
                                         timeout=1, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0))
    )
    errorIndication, errorStatus, errorIndex, _ = await iterator
    if errorIndication or errorIndex or errorStatus:
        return False
    return True

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

async def monitoring_loop(interval: int = 5):
    while True:
        try:
            async with lock:
                if not ips_status:
                    # print("Nenhum IP para monitorar")
                    await asyncio.sleep(interval)
                    continue
                ips = list(ips_status.keys())
            if ips:
                # print(f"Pingando IPs: {ips}")
                try:
                    hosts = await async_multiping(ips, count=3, timeout=3)
                except Exception:
                    # print(f"Erro no async_multiping: {e}")
                    hosts = []
                async with lock:
                    for host in hosts:
                        is_alive = host.avg_rtt > 0 or host.packets_received > 0
                        if not is_alive:
                            is_alive = await check_tcp(host.address)
                        if host.address in ips_status:  # Verifica se IP ainda existe
                            ips_status[host.address]['status'] = is_alive
                    print(f"Status atualizado: {ips_status}")
        except Exception:
            # print(f"Erro no loop de monitoramento: {e}")
            pass
        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(monitoring_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/add/{ip}")
async def add_ip(ip: str):
    async with lock:
        if ip in ips_status:
            raise HTTPException(status_code=400, detail="IP já existe")
        ips_status[ip] = {'status': False, 'data': []}
    return {"message": f"IP {ip} adicionado"}

@app.delete("/remove/{ip}")
async def remove_ip(ip: str):
    async with lock:
        if ip not in ips_status:
            raise HTTPException(status_code=404, detail="IP não encontrado")
        del ips_status[ip]
    return {"message": f"IP {ip} removido"}

@app.get("/status")
async def get_status():
    async with lock:
        return ips_status.copy()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)