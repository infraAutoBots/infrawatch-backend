import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import asyncio
from icmplib import async_multiping
from typing import Dict
from check_by_service import check_by_service
from snmp_get_data import get_snmp_info


# Estado compartilhado: dict de IPs e status (True: alive, False: dead)
ips_status: Dict[str, Dict[str, bool]] = {
    '192.168.8.159': {'status': False, 'data': {}},
    '192.168.8.146': {'status': False, 'data': {}},
    '192.168.8.121': {'status': False, 'data': {}},
    '127.0.0.1': {'status': False, 'data': {}}
}
lock = asyncio.Lock()

async def monitoring_loop(interval: int = 60):
    while True:
        try:
            async with lock:
                if not ips_status:
                    await asyncio.sleep(interval)
                    continue
                ips = list(ips_status.keys())
            if ips:
                try:
                    hosts = await async_multiping(ips, count=3, timeout=3)
                except Exception:
                    hosts = []
                async with lock:
                    for host in hosts:
                        is_alive = host.avg_rtt > 0 or host.packets_received > 0
                        if not is_alive:
                            is_alive = await check_by_service(host.address)
                        if host.address in ips_status:
                            ips_status[host.address]['status'] = is_alive
                            # verificar se tem o snmp como requisito
                            ips_status[host.address]['data'] = get_snmp_info(host.address)
        except Exception:
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
        ips_status[ip] = {'status': False, 'data': {}}
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