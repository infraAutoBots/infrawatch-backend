import pytest
import asyncio
from app.services import check_services, check_service
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_check_services(mocker):
    mocker.patch("services.check_service", AsyncMock(side_effect=lambda ip, svc: svc in ["HTTP", "SSH"]))
    services = await check_services("192.168.1.1", only_these=["HTTP", "SSH", "FTP"])
    assert services == ["HTTP", "SSH"]

@pytest.mark.asyncio
async def test_check_service_tcp(mocker):
    mocker.patch("asyncio.open_connection", AsyncMock())
    result = await check_service("192.168.1.1", "HTTP")
    assert result is True
    asyncio.open_connection.assert_called_with("192.168.1.1", 80)

@pytest.mark.asyncio
async def test_check_service_tcp_fail(mocker):
    mocker.patch("asyncio.open_connection", AsyncMock(side_effect=asyncio.TimeoutError))
    result = await check_service("192.168.1.1", "HTTP")
    assert result is False

@pytest.mark.asyncio
async def test_check_service_unsupported():
    result = await check_service("192.168.1.1", "INVALID")
    assert result is False
