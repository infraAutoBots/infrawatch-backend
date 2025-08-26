from pydantic import BaseModel
from typing import Optional
from datetime import datetime



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
    sysDescr: Optional[str]  # Descrição do sistema (SO, versão, etc.)
    sysName: Optional[str]  # Nome do host
    sysUpTime: Optional[str]  # Tempo de atividade desde o último reboot
    hrProcessorLoad: Optional[str]  #  Uso de CPU (Carga da CPU por núcleo)
    memTotalReal: Optional[str]  # Total de memória física
    memAvailReal: Optional[str]  # Memória física livre
    hrStorageSize: Optional[str]  # Capacidade total Armazenamento e discos
    hrStorageUsed: Optional[str]  # Espaço utilizado Armazenamento e discos

    class Config:
        from_attributes = True
