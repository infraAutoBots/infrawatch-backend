
# 3. models.py
# - Modelos Pydantic para validação de inputs/outputs.
# - MonitorConfig: IP, intervalo, SNMP version, community/user/auth, webhook_url, etc.
# - MonitorStatus: Status atual.
# - UptimeData: Dados de tempo ativo/inativo.

from pydantic import BaseModel
from typing import Optional, List, Dict


class MonitorConfig(BaseModel):
    ip: str
    interval_seconds: int = 60
    snmp_version: str = "v2c"  # v1, v2c, v3
    snmp_community: Optional[str] = "public"  # Para v1/v2c
    snmp_user: Optional[str] = None  # Para v3
    snmp_auth_protocol: Optional[str] = None  # ex: usmHMACMD5AuthProtocol
    snmp_auth_password: Optional[str] = None
    snmp_priv_protocol: Optional[str] = None  # ex: usmDESPrivProtocol
    snmp_priv_password: Optional[str] = None
    webhook_url: Optional[str] = None


class MonitorStatus(BaseModel):
    ip: str
    interval_seconds: int
    current_status: str  # ex: "online", "offline"
    # Adicione mais campos se necessário


class UptimeData(BaseModel):
    uptime_seconds: float
    downtime_seconds: float
    history: List[Dict]


