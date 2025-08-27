from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime



class UserSchemas(BaseModel):    
    name: str
    email: str
    password: str
    state: Optional[bool] = True
    last_login: Optional[datetime] = None
    access_level: str

    class Config:
        from_attributes = True


class EndPointSchemas(BaseModel):

    ip: str
    interval: int
    version: str
    community: str
    port: Optional[int] | None
    user: str
    authKey: str
    privKey: str
    webhook: str

    class Config:
        from_attributes = True


class EndPointsDataSchemas(BaseModel):
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
    ip: str
    interval: int
    version: Optional[str]
    community: Optional[str]
    port: Optional[int] | None
    user: Optional[str]
    authKey: Optional[str]
    privKey: Optional[str]
    webhook: Optional[str]
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
    email: str
    password: str

    class Config:
        from_attributes = True

class ResponseEndPointsDataSchemas(BaseModel):
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
    id: int
    name: str
    email: str
    access_level: str
    state: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreateSchemas(BaseModel):
    name: str
    email: str
    password: str
    access_level: str
    state: Optional[bool] = True

    class Config:
        from_attributes = True


class UserUpdateSchemas(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    access_level: Optional[str] = None
    state: Optional[bool] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


class UserStatusUpdateSchemas(BaseModel):
    state: bool

    class Config:
        from_attributes = True


class UserStatsSchemas(BaseModel):
    total_users: int
    admins: int
    monitors: int
    viewers: int
    active_users: int
    inactive_users: int

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponseSchemas]
    total: int
    page: int
    pages: int
    stats: UserStatsSchemas

    class Config:
        from_attributes = True
