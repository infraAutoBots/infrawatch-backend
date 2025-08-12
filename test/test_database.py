import pytest
import aiosqlite
from datetime import datetime, timedelta
from app.database import init_db, add_monitor, get_monitor, get_all_monitors, update_monitor, delete_monitor, log_status, get_uptime_data, get_confirmed_services, update_confirmed_services
from app.models import MonitorConfig


@pytest.fixture
async def db():
	async with aiosqlite.connect(":memory:") as db:
		await init_db(db=db)  # Passa conexão para usar memória
		yield db

@pytest.mark.asyncio
async def test_init_db(db):
	# Verifica se tabelas foram criadas
	cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
	tables = await cursor.fetchall()
	table_names = [t[0] for t in tables]
	assert "monitors" in table_names
	assert "status_logs" in table_names
	assert "services" in table_names

@pytest.mark.asyncio
async def test_add_and_get_monitor(db):
	config = MonitorConfig(ip="192.168.1.1", interval_seconds=60, snmp_version="v2c", snmp_community="public")
	await add_monitor(config, db=db)
	result = await get_monitor("192.168.1.1", db=db)
	assert result["ip"] == "192.168.1.1"
	assert result["interval_seconds"] == 60
	assert result["snmp_version"] == "v2c"

@pytest.mark.asyncio
async def test_get_all_monitors(db):
	config1 = MonitorConfig(ip="192.168.1.1", interval_seconds=60)
	config2 = MonitorConfig(ip="192.168.1.2", interval_seconds=30)
	await add_monitor(config1, db=db)
	await add_monitor(config2, db=db)
	monitors = await get_all_monitors(db=db)
	assert len(monitors) == 2
	assert "192.168.1.1" in monitors
	assert "192.168.1.2" in monitors

@pytest.mark.asyncio
async def test_update_monitor(db):
	config = MonitorConfig(ip="192.168.1.1", interval_seconds=60)
	await add_monitor(config, db=db)
	updated_config = {"ip": "192.168.1.1", "interval_seconds": 30, "snmp_version": "v2c", "snmp_community": "public"}
	await update_monitor("192.168.1.1", updated_config, db=db)
	result = await get_monitor("192.168.1.1", db=db)
	assert result["interval_seconds"] == 30

@pytest.mark.asyncio
async def test_delete_monitor(db):
	config = MonitorConfig(ip="192.168.1.1", interval_seconds=60)
	await add_monitor(config, db=db)
	await delete_monitor("192.168.1.1", db=db)
	result = await get_monitor("192.168.1.1", db=db)
	assert result is None

@pytest.mark.asyncio
async def test_log_status_and_get_uptime(db):
	await add_monitor(MonitorConfig(ip="192.168.1.1"), db=db)
	# Simula logs com timestamps
	base_time = datetime.now()
	await log_status("192.168.1.1", True, ["HTTP"], {"uptime": "1000"}, db=db, timestamp=base_time)
	await log_status("192.168.1.1", False, [], {}, db=db, timestamp=base_time + timedelta(seconds=60))
	uptime_data = await get_uptime_data("192.168.1.1", db=db)
	assert uptime_data["uptime_seconds"] == 60.0
	assert uptime_data["downtime_seconds"] > 0  # Inclui tempo até agora
	assert len(uptime_data["history"]) == 2

@pytest.mark.asyncio
async def test_confirmed_services(db):
	await add_monitor(MonitorConfig(ip="192.168.1.1"), db=db)
	await update_confirmed_services("192.168.1.1", ["HTTP", "SSH"], db=db)
	services = await get_confirmed_services("192.168.1.1", db=db)
	assert services == ["HTTP", "SSH"]
