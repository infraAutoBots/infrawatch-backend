# - Usa aiosqlite para operações assíncronas no SQLite.
# - Tabelas: monitors (IPs e configs), status_logs (histórico de status para uptime), services (serviços confirmados por IP).
# - Funções: add, get, update, delete, log_status, get_uptime_data (calcula tempo ativo/inativo baseado em logs).

import aiosqlite
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Optional


DB_FILE = "monitors.db"


async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monitors (
                ip TEXT PRIMARY KEY,
                config JSON
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS status_logs (
                ip TEXT,
                timestamp DATETIME,
                is_online BOOLEAN,
                services JSON,
                snmp_data JSON,
                FOREIGN KEY(ip) REFERENCES monitors(ip)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                ip TEXT PRIMARY KEY,
                confirmed_services JSON,
                FOREIGN KEY(ip) REFERENCES monitors(ip)
            )
        """)
        await db.commit()


async def add_monitor(config: BaseModel):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO monitors (ip, config) VALUES (?, ?)", (config.ip, json.dumps(config.dict())))
        await db.execute("INSERT INTO services (ip, confirmed_services) VALUES (?, ?)", (config.ip, json.dumps([])))
        await db.commit()


async def get_monitor(ip: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT config FROM monitors WHERE ip = ?", (ip,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None


async def get_all_monitors() -> Dict[str, Dict]:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT ip, config FROM monitors")
        rows = await cursor.fetchall()
        return {row[0]: json.loads(row[1]) for row in rows}


async def update_monitor(ip: str, config: Dict):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE monitors SET config = ? WHERE ip = ?", (json.dumps(config), ip))
        await db.commit()


async def delete_monitor(ip: str):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM monitors WHERE ip = ?", (ip,))
        await db.execute("DELETE FROM status_logs WHERE ip = ?", (ip,))
        await db.execute("DELETE FROM services WHERE ip = ?", (ip,))
        await db.commit()


async def log_status(ip: str, is_online: bool, services: list, snmp_data: Dict):
    timestamp = datetime.now().isoformat()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO status_logs (ip, timestamp, is_online, services, snmp_data) VALUES (?, ?, ?, ?, ?)",
            (ip, timestamp, is_online, json.dumps(services), json.dumps(snmp_data))
        )
        await db.commit()


async def get_uptime_data(ip: str) -> Dict:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT timestamp, is_online FROM status_logs WHERE ip = ? ORDER BY timestamp", (ip,))
        rows = await cursor.fetchall()
        if not rows:
            return {"uptime_seconds": 0, "downtime_seconds": 0, "history": []}
        history = []
        total_up = 0
        total_down = 0
        prev_time = datetime.fromisoformat(rows[0][0])
        prev_online = rows[0][1]
        for ts, online in rows[1:]:
            curr_time = datetime.fromisoformat(ts)
            delta = (curr_time - prev_time).total_seconds()
            if prev_online:
                total_up += delta
            else:
                total_down += delta
            history.append({"timestamp": ts, "online": online})
            prev_time = curr_time
            prev_online = online
        # Adiciona até agora
        now = datetime.now()
        delta = (now - prev_time).total_seconds()
        if prev_online:
            total_up += delta
        else:
            total_down += delta
        return {"uptime_seconds": total_up, "downtime_seconds": total_down, "history": history}


async def get_confirmed_services(ip: str) -> list:
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute("SELECT confirmed_services FROM services WHERE ip = ?", (ip,))
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else []


async def update_confirmed_services(ip: str, services: list):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE services SET confirmed_services = ? WHERE ip = ?", (json.dumps(services), ip))
        await db.commit()
