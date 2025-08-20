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


class DeviceSchemas(BaseModel):

    ip: str
    interval: int
    version: str
    community: str
    port: int
    user: str
    authKey: str
    privKey: str

    class Config:
        from_attributes = True


class DeviceDataSchemas(BaseModel):
    id_device: int
    status: bool
    sys_descr: Optional[str]
    cpu: Optional[str]
    disk: Optional[str]
    uptime: Optional[str]
    storage: Optional[str]
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True

class LoginSchemas(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True