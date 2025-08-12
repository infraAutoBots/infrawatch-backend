# - Este é o arquivo principal que inicia a API FastAPI.
# - Define endpoints para adicionar/modificar/listar/remover monitors.
# - Gerencia um dicionário de tarefas asyncio para cada IP (loop de monitoramento em background).
# - Ao adicionar um IP, inicia a tarefa de monitoramento.
# - Ao modificar (ex: PUT para intervalo), cancela e reinicia a tarefa.
# - Fornece dados de uptime via GET.

import asyncio
from fastapi import FastAPI, HTTPException, Body
import uvicorn
from typing import Dict
from models import MonitorConfig, MonitorStatus, UptimeData
from database import init_db, add_monitor, get_monitor, update_monitor, delete_monitor, get_all_monitors, log_status, get_uptime_data
from monitor import start_monitoring_loop

app = FastAPI()

# Dicionário para tarefas de background (uma por IP)
monitoring_tasks: Dict[str, asyncio.Task] = {}


@app.on_event("startup")
async def startup_event():
    await init_db()
    # Carregar monitors existentes do DB e iniciar tarefas
    monitors = await get_all_monitors()
    for ip, config in monitors.items():
        task = asyncio.create_task(start_monitoring_loop(ip, config))
        monitoring_tasks[ip] = task


@app.on_event("shutdown")
async def shutdown_event():
    for task in monitoring_tasks.values():
        task.cancel()


@app.post("/monitor")
async def add_monitor_endpoint(config: MonitorConfig):
    if config.ip in monitoring_tasks:
        raise HTTPException(status_code=400, detail="IP already monitored")
    await add_monitor(config)
    task = asyncio.create_task(start_monitoring_loop(config.ip, config.dict()))
    monitoring_tasks[config.ip] = task
    return {"message": "Monitor added and started"}


@app.get("/monitors", response_model=Dict[str, MonitorStatus])
async def get_monitors():
    monitors = await get_all_monitors()
    statuses = {}
    for ip, config in monitors.items():
        # Aqui, você pode enriquecer com status atual do DB, mas por simplicidade, retornamos config
        statuses[ip] = MonitorStatus(**config, current_status="unknown")  # Adapte para buscar status real
    return statuses


@app.get("/monitor/{ip}", response_model=UptimeData)
async def get_monitor_details(ip: str):
    if ip not in monitoring_tasks:
        raise HTTPException(status_code=404, detail="IP not monitored")
    return await get_uptime_data(ip)


@app.put("/monitor/{ip}")
async def update_monitor_endpoint(ip: str, update_data: Dict = Body(...)):
    config = await get_monitor(ip)
    if not config:
        raise HTTPException(status_code=404, detail="IP not monitored")
    # Atualiza campos (ex: interval_seconds)
    if "interval_seconds" in update_data:
        config["interval_seconds"] = update_data["interval_seconds"]
    # Outros campos...
    await update_monitor(ip, config)
    # Cancela e reinicia tarefa
    monitoring_tasks[ip].cancel()
    task = asyncio.create_task(start_monitoring_loop(ip, config))
    monitoring_tasks[ip] = task
    return {"message": "Monitor updated"}


@app.delete("/monitor/{ip}")
async def delete_monitor_endpoint(ip: str):
    if ip not in monitoring_tasks:
        raise HTTPException(status_code=404, detail="IP not monitored")
    await delete_monitor(ip)
    monitoring_tasks[ip].cancel()
    del monitoring_tasks[ip]
    return {"message": "Monitor removed"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
