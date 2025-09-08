import pytest
from app.snmp_monitor import get_snmp_data
from pysnmp.hlapi.asyncio import CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_get_snmp_data_v2c(mocker):
    config = {
        "snmp_version": "v2c",
        "snmp_community": "public"
    }
    mock_get_cmd = mocker.patch("snmp_monitor.getCmd", AsyncMock(return_value=(None, 0, 0, [(ObjectIdentity("1.3.6.1.2.1.1.3.0"), "1000")])))
    result = await get_snmp_data("192.168.1.1", config)
    assert result["uptime"] == "1000"
    mock_get_cmd.assert_called()

@pytest.mark.asyncio
async def test_get_snmp_data_invalid_version():
    config = {"snmp_version": "invalid"}
    result = await get_snmp_data("192.168.1.1", config)
    assert result["error"] == "Invalid SNMP version"
