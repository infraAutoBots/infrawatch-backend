from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime



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
    sysDescr: Optional[str]
    sysName: Optional[str]
    sysUpTime: Optional[str]
    hrProcessorLoad: Optional[str]
    memTotalReal: Optional[str]
    memAvailReal: Optional[str]
    hrStorageSize: Optional[str]
    hrStorageUsed: Optional[str]
    last_updated: Optional[datetime]

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

    class Config:
        from_attributes = True


class AddEndPointRequest(BaseModel):
    """
    Schema para requisição de adição de endpoint.
    """
    ip: str
    interval: int
    version: Optional[str]
    community: Optional[str]
    port: Optional[int] | None
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
