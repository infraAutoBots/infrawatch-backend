import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.monitor import start_monitoring_loop, check_online
from app.models import MonitorConfig


@pytest.mark.asyncio
async def test_check_online_with_ping():
    config = MonitorConfig(ip="192.168.1.1").dict()
    with patch("monitor.async_ping", new=AsyncMock()) as mock_ping:
        mock_ping.return_value.is_alive = True
        result = await check_online("192.168.1.1", config)
        assert result is True
        mock_ping.assert_called_once_with("192.168.1.1", count=1, timeout=2)

@pytest.mark.asyncio
async def test_check_online_fallback_services(mocker):
    config = MonitorConfig(ip="192.168.1.1").dict()
    mocker.patch("monitor.async_ping", AsyncMock(return_value=AsyncMock(is_alive=False)))
    mocker.patch("monitor.get_confirmed_services", AsyncMock(return_value=["HTTP"]))
    mocker.patch("monitor.check_services", AsyncMock(return_value=["HTTP"]))
    result = await check_online("192.168.1.1", config)
    assert result is True

@pytest.mark.asyncio
async def test_check_online_offline(mocker):
    config = MonitorConfig(ip="192.168.1.1").dict()
    mocker.patch("monitor.async_ping", AsyncMock(return_value=AsyncMock(is_alive=False)))
    mocker.patch("monitor.get_confirmed_services", AsyncMock(return_value=[]))
    result = await check_online("192.168.1.1", config)
    assert result is False

@pytest.mark.asyncio
async def test_monitoring_loop(mocker):
    config = MonitorConfig(ip="192.168.1.1", interval_seconds=0.1).dict()
    mocker.patch("monitor.check_online", AsyncMock(return_value=True))
    mocker.patch("monitor.check_services", AsyncMock(return_value=["HTTP"]))
    mocker.patch("monitor.get_snmp_data", AsyncMock(return_value={"uptime": "1000"}))
    mocker.patch("monitor.log_status", AsyncMock())
    mocker.patch("monitor.send_webhook", AsyncMock())
    mocker.patch("monitor.get_confirmed_services", AsyncMock(return_value=[]))
    mocker.patch("monitor.update_confirmed_services", AsyncMock())

    # Executa o loop por um curto período
    task = asyncio.create_task(start_monitoring_loop("192.168.1.1", config))
    await asyncio.sleep(0.3)  # Permite 2-3 iterações
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert monitor.check_services.called
    assert monitor.log_status.called
