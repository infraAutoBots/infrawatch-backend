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
    nickname: str = ""
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
    informed: bool = False
    snmp_informed: bool = False
    consecutive_ping_failures: int = 0
    consecutive_snmp_failures: int = 0
    
    
def print_logs(result):
    status_icon = "🟢" if result.is_alive else "🔴"
    
    failure_info = (f"SNMP: (Falhas: {result.consecutive_snmp_failures})"
                              if result.consecutive_snmp_failures > 0 else "")

    failure_ping = (f"Ping: (Falhas: {result.consecutive_ping_failures})"
                    if result.consecutive_ping_failures > 0 else "")

    snmp_icon = ""
    if check_ip_for_snmp(result):
        snmp_icon = (f"📊 : {result.snmp_data['sysDescr'].split(' ')[0]}"
                     if result.snmp_data and result.snmp_data.get('sysDescr') else "❌")

    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | {snmp_icon} {failure_info}{failure_ping}")


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
            "hrStorageUsed": oids_data.hrStorageUsed,
            "ifOperStatus": oids_data.ifOperStatus,
            "ifInOctets": oids_data.ifInOctets,
            "ifOutOctets": oids_data.ifOutOctets
        }
    return HostStatus(
        _id=row.id,
        ip=row.ip,
        nickname=row.nickname,
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
    """Verifica se o host tem configuração SNMP válida"""
    if not host or not host.ip:
        return False
    
    # Verifica se tem configuração SNMP v1/v2c válida
    has_v1_v2c = (host.version in ["1", "2c"] and 
                  host.community and 
                  host.community.strip() != "")
    
    # Verifica se tem configuração SNMP v3 válida
    has_v3 = (host.version == "3" and 
              host.user and 
              host.user.strip() != "")
    
    return bool(has_v1_v2c or has_v3)


def is_snmp_data_valid(snmp_data: dict) -> bool:
    """Valida se os dados SNMP retornados são úteis"""
    if not snmp_data:
        return False
    
    # OIDs críticos que são mais importantes para validação
    critical_oids = ['sysDescr', 'sysUpTime', 'sysName']
    
    # Conta valores não-None, não-vazios e não-inválidos
    valid_values = []
    critical_working = 0
    
    for key, value in snmp_data.items():
        if value is not None:
            str_value = str(value).strip()
            # Considera válido se não for vazio e não for um valor de erro comum
            if str_value and str_value not in ['', 'None', 'noSuchInstance', 'noSuchObject', 'endOfMibView']:
                valid_values.append(value)
                
                # Conta se é um OID crítico
                if key in critical_oids:
                    critical_working += 1
    
    # Validação mais inteligente:
    # 1. Se pelo menos 1 OID crítico funciona, considerar válido
    # 2. Ou se pelo menos 30% dos OIDs retornaram dados válidos
    # 3. Ou se pelo menos 1 OID funciona (para casos com poucos OIDs)
    
    total_oids = len(snmp_data)
    min_required = max(1, int(total_oids * 0.3))
    
    has_critical = critical_working > 0
    has_minimum_percentage = len(valid_values) >= min_required
    has_at_least_one = len(valid_values) >= 1
    
    return has_critical or has_minimum_percentage or (total_oids <= 3 and has_at_least_one) 


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
