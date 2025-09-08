from pydantic import BaseModel, field_validator
from typing import Optional, List, Union, Any, Dict
import json
from datetime import datetime
from enum import Enum



class UserSchemas(BaseModel):
    """
    Schema para criação e manipulação de dados de usuário.
    """
    name: str
    email: str
    password: str
    state: Optional[bool] = True
    last_login: Optional[datetime] = None
    access_level: str

    class Config:
        from_attributes = True


class EndPointSchemas(BaseModel):
    """
    Schema para representação de um endpoint monitorado.
    """

    ip: str
    nickname: str
    interval: int
    version: str
    community: str
    port: Optional[int] | None
    user: str
    authKey: str
    privKey: str

    class Config:
        from_attributes = True


class EndPointsDataSchemas(BaseModel):
    """
    Schema para dados coletados de um endpoint.
    """
    id_end_point: int
    status: bool
    active: Optional[bool] = True
    sysDescr: Optional[str]
    sysName: Optional[str]
    sysUpTime: Optional[str]
    hrProcessorLoad: Optional[List[Dict[str, str]]]
    memTotalReal: Optional[str]
    memAvailReal: Optional[str]
    hrStorageSize: Optional[List[Dict[str, str]]]
    hrStorageUsed: Optional[List[Dict[str, str]]]
    hrStorageDescr: Optional[List[Dict[str, str]]]
    ifOperStatus: Optional[List[Dict[str, str]]]
    ifInOctets: Optional[List[Dict[str, str]]]
    ifOutOctets: Optional[List[Dict[str, str]]]
    ping_rtt: Optional[str]
    snmp_rtt: Optional[str]
    last_updated: Optional[datetime]

    @field_validator('hrProcessorLoad', 'hrStorageSize', 'hrStorageUsed', 'hrStorageDescr', 'ifOperStatus', 'ifInOctets', 'ifOutOctets', mode='before')
    @classmethod
    def parse_json_or_list(cls, v):
        """
        Converte string JSON para lista de dicts se necessário
        """
        if v is None:
            return None
        if isinstance(v, str):
            if v.strip() == "" or v.strip() == "[]":
                return None
            try:
                # Corrigir aspas simples para duplas (JSON válido)
                json_str = v.replace("'", '"')
                # Tenta fazer parse do JSON
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    return parsed
                return None
            except (json.JSONDecodeError, ValueError):
                return None
        if isinstance(v, list):
            return v
        return None

    class Config:
        from_attributes = True

class EndPointOIDsSchemas(BaseModel):
    """
    Schema para OIDs SNMP de um endpoint.
    """
    sysDescr: Optional[str]
    sysName: Optional[str]
    sysUpTime: Optional[str]
    hrProcessorLoad: Optional[str]
    memTotalReal: Optional[str]
    memAvailReal: Optional[str]
    hrStorageSize: Optional[str]
    hrStorageUsed: Optional[str]
    hrStorageDescr: Optional[str]
    ifOperStatus: Optional[str]
    ifInOctets: Optional[str]
    ifOutOctets: Optional[str]

    class Config:
        from_attributes = True


class AddEndPointRequest(BaseModel):
    """
    Schema para requisição de adição de endpoint.
    """
    ip: str
    interval: int
    nickname: str
    version: Optional[str]
    community: Optional[str]
    port: Optional[int] | None
    active: Optional[bool] = True
    user: Optional[str]
    authKey: Optional[str]
    privKey: Optional[str]
    sysDescr: Optional[str]
    sysName: Optional[str]
    sysUpTime: Optional[str]
    hrProcessorLoad: Optional[str]
    memTotalReal: Optional[str]
    memAvailReal: Optional[str]
    hrStorageSize: Optional[str]
    hrStorageUsed: Optional[str]
    hrStorageDescr: Optional[str]
    ifOperStatus: Optional[str]
    ifInOctets: Optional[str]
    ifOutOctets: Optional[str]

    class Config:
        from_attributes = True

class LoginSchemas(BaseModel):
    """
    Schema para autenticação de usuário (login).
    """
    email: str
    password: str

    class Config:
        from_attributes = True

class ResponseEndPointsDataSchemas(BaseModel):
    """
    Schema para resposta de dados de endpoint.
    """
    status: bool
    sys_descr: Optional[str]
    cpu: Optional[str]
    disk: Optional[str]
    uptime: Optional[str]
    storage: Optional[str]
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# Schemas adicionais para usuários
class UserResponseSchemas(BaseModel):
    """
    Schema para resposta detalhada de usuário.
    """
    id: int
    name: str
    email: str
    access_level: str
    url: Optional[str] = None
    state: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateSchemas(BaseModel):
    """
    Schema para criação de novo usuário.
    """
    name: str
    email: str
    password: str
    access_level: str
    url: Optional[str] = None
    state: Optional[bool] = True

    class Config:
        from_attributes = True


class UserUpdateSchemas(BaseModel):
    """
    Schema para atualização de dados de usuário.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    access_level: Optional[str] = None
    url: Optional[str] = None
    state: Optional[bool] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


class UserStatusUpdateSchemas(BaseModel):
    """
    Schema para atualização de status de usuário (ativo/inativo).
    """
    state: bool

    class Config:
        from_attributes = True


class UserStatsSchemas(BaseModel):
    """
    Schema para estatísticas agregadas de usuários.
    """
    total_users: int
    admins: int
    monitors: int
    viewers: int
    active_users: int
    inactive_users: int

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """
    Schema para resposta paginada de usuários.
    """
    users: List[UserResponseSchemas]
    total: int
    page: int
    pages: int
    stats: UserStatsSchemas

    class Config:
        from_attributes = True


# Schemas de Alertas
class AlertSeverityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertStatusEnum(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class AlertCategoryEnum(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NETWORK = "network"

class AlertImpactEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertBaseSchema(BaseModel):
    """Schema base para alertas"""
    title: str
    description: Optional[str] = None
    severity: AlertSeverityEnum
    category: AlertCategoryEnum
    system: str
    impact: AlertImpactEnum = AlertImpactEnum.MEDIUM
    assignee: Optional[str] = None
    id_endpoint: Optional[int] = None

class AlertCreateSchema(AlertBaseSchema):
    """Schema para criação de alertas"""
    pass

class AlertUpdateSchema(BaseModel):
    """Schema para atualização de alertas"""
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[AlertSeverityEnum] = None
    category: Optional[AlertCategoryEnum] = None
    impact: Optional[AlertImpactEnum] = None
    assignee: Optional[str] = None
    status: Optional[AlertStatusEnum] = None

class AlertResponseSchema(AlertBaseSchema):
    """Schema de resposta para alertas"""
    id: int
    status: AlertStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    duration: str
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def validate_updated_at(cls, v, info):
        """Se updated_at for None, usa created_at como fallback"""
        if v is None and info.data:
            return info.data.get('created_at')
        return v
    
    class Config:
        from_attributes = True

class AlertLogSchema(BaseModel):
    """Schema para logs de alertas"""
    id: int
    action: str
    comment: Optional[str] = None
    created_at: datetime
    user: UserResponseSchemas  # Dados do usuário que realizou a ação
    
    class Config:
        from_attributes = True

class AlertWithLogsSchema(AlertResponseSchema):
    """Schema de alerta com histórico de logs"""
    alert_logs: List[AlertLogSchema] = []

class AlertFiltersSchema(BaseModel):
    """Schema para filtros de alertas"""
    search: Optional[str] = None
    severity: Optional[List[AlertSeverityEnum]] = None
    status: Optional[List[AlertStatusEnum]] = None
    category: Optional[List[AlertCategoryEnum]] = None
    impact: Optional[List[AlertImpactEnum]] = None
    assignee: Optional[str] = None
    system: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class PaginationSchema(BaseModel):
    """Schema para paginação"""
    page: int = 1
    size: int = 10
    total: int
    pages: int

class AlertListResponseSchema(BaseModel):
    """Schema de resposta para lista paginada de alertas"""
    success: bool = True
    data: List[AlertResponseSchema]
    pagination: PaginationSchema
    filters_applied: AlertFiltersSchema

class AlertStatsSchema(BaseModel):
    """Schema para estatísticas de alertas"""
    total_alerts: int
    critical_active: int
    high_active: int
    medium_active: int
    low_active: int
    acknowledged: int
    resolved_today: int
    average_resolution_time: str  # MTTR médio
    by_category: dict
    by_system: dict

class AlertActionSchema(BaseModel):
    """Schema para ações nos alertas"""
    action: str  # acknowledge, resolve, assign
    comment: Optional[str] = None
    assignee: Optional[str] = None


# Schemas para Configurações
class WebHookConfigSchema(BaseModel):
    """Schema para configuração de webhook."""
    url: str
    active: Optional[bool] = True
    timeout: Optional[int] = 30
    access_token: Optional[str] = None

    class Config:
        from_attributes = True


class WebHookConfigResponse(BaseModel):
    """Schema de resposta para configuração de webhook."""
    id: int
    url: str
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebHookConfigUpdate(BaseModel):
    """Schema para atualização de configuração de webhook."""
    url: Optional[str] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True


class EmailConfigSchema(BaseModel):
    """Schema para configuração de email."""
    email: str
    password: str
    port: int
    server: str

    class Config:
        from_attributes = True


class EmailConfigResponse(BaseModel):
    """Schema de resposta para configuração de email."""
    id: int
    email: str
    port: int
    server: str
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailConfigUpdate(BaseModel):
    """Schema para atualização de configuração de email."""
    email: Optional[str] = None
    password: Optional[str] = None
    port: Optional[int] = None
    server: Optional[str] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True


class FailureThresholdConfigSchema(BaseModel):
    """Schema para configuração de limites de falhas."""
    consecutive_snmp_failures: Optional[int] = 3
    consecutive_ping_failures: Optional[int] = 5
    active: Optional[bool] = True

    class Config:
        from_attributes = True


class FailureThresholdConfigResponse(BaseModel):
    """Schema de resposta para configuração de limites de falhas."""
    id: int
    consecutive_snmp_failures: int
    consecutive_ping_failures: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PerformanceThresholdsSchemas(BaseModel):
    """
    Schema para configuração de limites de performance.
    """
    metric_type: str
    warning_threshold: int
    critical_threshold: int
    enabled: bool = True

    class Config:
        from_attributes = True


class PerformanceThresholdsResponse(BaseModel):
    """
    Schema para resposta de configuração de limites de performance.
    """
    id: int
    metric_type: str
    warning_threshold: int
    critical_threshold: int
    enabled: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PerformanceThresholdsUpdate(BaseModel):
    """
    Schema para atualização de configuração de limites de performance.
    """
    warning_threshold: Optional[int] = None
    critical_threshold: Optional[int] = None
    enabled: Optional[bool] = None

    class Config:
        from_attributes = True


class FailureThresholdConfigUpdate(BaseModel):
    """Schema para atualização de configuração de limites de falhas."""
    consecutive_snmp_failures: Optional[int] = None
    consecutive_ping_failures: Optional[int] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True
