from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, Devices, DeviceData
from schemas import DeviceSchemas, DeviceDataSchemas
from utils import valid_device
from typing import Dict, Any


monitor_router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(verify_token)])


@monitor_router.post("/")
async def add_ip(device_schemas: DeviceSchemas, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Adicione um endereço Ip/Domínio à lista de monitoramento.

    Args:
        Ip/Domínio (str): O endereço IP a ser adicionado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_device(device_schemas):
        raise HTTPException(status_code=400, detail="Invalid device")

    ip = session.query(Devices).filter(Devices.ip == device_schemas.ip).first()
    if ip:
        raise HTTPException(status_code=400, detail="Existing IP/Domain")
    else:
        new_device = Devices(device_schemas.ip, device_schemas.interval,
                         device_schemas.version, device_schemas.community,
                         device_schemas.port, device_schemas.user, device_schemas.authKey,
                         device_schemas.privKey, device_schemas.webhook, logged_user.id)
        session.add(new_device)
        session.commit()
        return {"message": f" {device_schemas.ip} adicionado à lista de monitoramento"}


@monitor_router.get("/{ip}")
async def get_ip_info(ip: str, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Obtenha informações sobre um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser consultado.

    Returns:
        dict: As informações do IP consultado.
    """

    if logged_user.access_level not in ["ADMIN", "MONITOR"]:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    device = session.query(Devices).filter(Devices.ip == ip).first()
    if not device:
        raise HTTPException(status_code=404, detail="IP/Domain not found")
    else:
        last_data = (session.query(DeviceData).filter(DeviceData.id_device == device.id)
            .order_by(DeviceData.id.desc()).first())
        return {"ip": ip, "data": last_data}


@monitor_router.put("/")
async def update_ip_info(device_schemas: DeviceSchemas, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Atualize as informações de um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser atualizado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_device(device_schemas):
        raise HTTPException(status_code=400, detail="Invalid device")
    
    ip = session.query(Devices).filter(Devices.ip == device_schemas.ip).first()
    if not ip:
        raise HTTPException(status_code=400, detail="Not existing IP/Domain")
    else:
        ip.ip = device_schemas.ip
        ip.interval = device_schemas.interval
        ip.version = device_schemas.version
        ip.community = device_schemas.community
        ip.port = device_schemas.port
        ip.user = device_schemas.user
        ip.authKey = device_schemas.authKey
        ip.privKey = device_schemas.privKey
        ip.webhook = device_schemas.webhook
        session.commit()
        return {"message": f"Endereço IP {ip} atualizado na lista de monitoramento."}


@monitor_router.delete("/{ip}")
async def delete_ip(ip: str, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Remova um endereço IP da lista de monitoramento.

    Args:
        ip/domínio (str): O endereço IP a ser removido.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    # verifcar utilizar o conseito de ship que apaga todos os dados relacionados com este ip/domini
    # if logged_user.access_level != "ADMIN":
    #     raise HTTPException(status_code=403, detail="Operation not permitted")
    # # verificar se ele e admin e se o end point existe
    # ip = session.query(Devices).filter(Devices.ip == ip).first()
    # if not ip:
    #     raise HTTPException(status_code=404, detail="IP/Domain not found")

    # session.delete(ip)
    # session.commit()
    return {"message": f"Endereço IP {ip} removido da lista de monitoramento."}


@monitor_router.get("/status")
async def get_status(session: Session = Depends(init_session)):
    """Obtenha o status do serviço de monitoramento.

    Returns:
        dict: O status do serviço.
    """

    # verificar se esta logado
    list_data: Dict[str, Any] = []
    all_data = session.query(Devices).all()
    for data in all_data:
        device_data = session.query(DeviceData).filter(DeviceData.id_device == data.id).all()
        list_data.append({"device": data, "data": device_data})

    return {"data": list_data}

