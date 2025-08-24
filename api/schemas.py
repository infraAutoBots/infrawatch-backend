from pydantic import BaseModel
from typing import Optional
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