from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional

from models import EndPoints, EndPointOIDs

from sqlalchemy.orm import Session
from pysnmp.hlapi.v3arch.asyncio import (CommunityData, UsmUserData, 
                                         usmHMACSHAAuthProtocol, usmAesCfb128Protocol)



@dataclass
class HostStatus:
    _id: Optional[int] = None
    ip: str = ""
    is_alive: bool = False
    interval: int = 0
    version: str = ""
    community: str = ""
    port: Optional[int] = None
    user: str = ""
    authKey: str = ""
    privKey: str = ""
    snmp_data: Dict[str, str] = None
    oids: List[str] = None
    last_updated: Optional[datetime] = None
    ping_rtt: float = 0.0
    # NOVO: Contador de falhas consecutivas
    consecutive_failures: int = 0


def print_logs(result):
    status_icon = "🟢" if result.is_alive else "🔴"
    failure_info = f" (Falhas: {result.consecutive_failures})" if result.consecutive_failures > 0 else ""
    snmp_icon = f"📊 : {result.snmp_data['sysDescr'].split(' ')[0]}" if result.snmp_data and result.snmp_data.get('sysDescr') else "❌"
    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | SNMP: {snmp_icon}{failure_info}")


def get_HostStatus(row: EndPoints, session: Session) -> Optional[HostStatus]:
    oids = {}
    oids_data = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == row.id).first()
    if oids_data:
        oids = {
            "sysDescr": oids_data.sysDescr,
            "sysName": oids_data.sysName,
            "sysUpTime": oids_data.sysUpTime,
            "hrProcessorLoad": oids_data.hrProcessorLoad,
            "memTotalReal": oids_data.memTotalReal,
            "memAvailReal": oids_data.memAvailReal,
            "hrStorageSize": oids_data.hrStorageSize,
            "hrStorageUsed": oids_data.hrStorageUsed
        }
    return HostStatus(
        _id=row.id,
        ip=row.ip,
        is_alive=False,
        interval=row.interval,
        version=row.version,
        community=row.community,
        port=row.port,
        user=row.user,
        authKey=row.authKey,
        privKey=row.privKey,
        oids=oids
    )


def check_ip_for_snmp(host: HostStatus):
    if (host.ip and host.interval and not host.port 
        and not host.version and not host.community
        and not host.user and not host.authKey 
        and not host.privKey):
        return False
    return True 


def select_snmp_authentication(host: HostStatus):
    if host.version in ["1", "2c"]:
        auth_data = CommunityData(host.community, mpModel=0 if host.version == "1" else 1)
    else:
        # Configura credenciais dependendo do caso
        if host.authKey and host.privKey:
            auth_data = UsmUserData(
                userName=host.user,
                authKey=host.authKey,
                privKey=host.privKey,
                authProtocol=usmHMACSHAAuthProtocol,
                privProtocol=usmAesCfb128Protocol,
            )
        elif host.authKey:
            auth_data = UsmUserData(
                userName=host.user,
                authKey=host.authKey,
                authProtocol=usmHMACSHAAuthProtocol,
            )
        else:
            auth_data = UsmUserData(host.user)
    return auth_data
