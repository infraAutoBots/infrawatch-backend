from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, EndPoints, EndPointsData, EndPointOIDs
from schemas import EndPointsDataSchemas, AddEndPointRequest
from utils import valid_end_point
from typing import Dict, Any, Optional
from pprint import pprint


monitor_router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(verify_token)])


def _check_admin(user: Users):
    if user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operação não permitida: requer nível ADMIN")

def _check_monitor_or_admin(user: Users):
    if user.access_level not in ["ADMIN", "MONITOR"]:
        raise HTTPException(status_code=403, detail="Operação não permitida: requer nível ADMIN ou MONITOR")

def _get_endpoint_by_ip(ip: str, session: Session) -> Optional[EndPoints]:
    return session.query(EndPoints).filter(EndPoints.ip == ip).one_or_none()



@monitor_router.post("/")
async def add_ip(
    end_point: AddEndPointRequest,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> dict:
    """
    Adiciona um endereço IP/Domínio à lista de monitoramento.
    """
    _check_admin(logged_user)
    if not valid_end_point(end_point):
        raise HTTPException(status_code=400, detail="Endpoint inválido")

    if _get_endpoint_by_ip(end_point.ip, session):
        raise HTTPException(status_code=400, detail="IP/Domínio já cadastrado")

    new_endpoint = EndPoints(
        end_point.ip,
        end_point.interval,
        end_point.version,
        end_point.community,
        end_point.port,
        end_point.user,
        end_point.authKey,
        end_point.privKey,
        end_point.webhook,
        logged_user.id
    )
    session.add(new_endpoint)
    session.commit()

    new_endpoint_oids = EndPointOIDs(
        new_endpoint.id,
        end_point.sysDescr,
        end_point.sysName,
        end_point.sysUpTime,
        end_point.hrProcessorLoad,
        end_point.memTotalReal,
        end_point.memAvailReal,
        end_point.hrStorageSize,
        end_point.hrStorageUsed
    )
    session.add(new_endpoint_oids)
    session.commit()
    return {"success": True, "message": f"Endereço IP {end_point.ip} adicionado à lista de monitoramento."}



@monitor_router.get("/history", response_model=Dict[str, Any])
async def get_status(session: Session = Depends(init_session)) -> dict:
    """
    Obtém o status de todos os dispositivos monitorados.
    """
    list_data = []
    all_data = session.query(EndPoints).all()
    for data in all_data:
        endpoint_data = session.query(EndPointsData).filter(EndPointsData.id_end_point == data.id).all()
        endpoint_data_serialized = [EndPointsDataSchemas.model_validate(d) for d in endpoint_data]
        list_data.append({"endpoint": data.ip, "data": endpoint_data_serialized})
    
    return {"success": True, "data": list_data}


@monitor_router.get("/status", response_model=Dict[str, Any])
async def get_status(session: Session = Depends(init_session)) -> dict:
    """
    Obtém o status de todos os dispositivos monitorados.
    """
    list_data = []
    all_data = session.query(EndPoints).all()
    for data in all_data:
        last_data = (session.query(EndPointsData)
                     .filter(EndPointsData.id_end_point == data.id)
                     .order_by(EndPointsData.id.desc()).first())
        last_data_serialize = EndPointsDataSchemas.model_validate(last_data) if last_data else None
        list_data.append({"endpoint": data.ip, "data": last_data_serialize})
    return {"success": True, "data": list_data}

 
@monitor_router.get("/{ip}", response_model=Optional[EndPointsDataSchemas])
async def get_ip_info(
    ip: str,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> Optional[EndPointsDataSchemas]:
    """
    Obtém informações sobre um endereço IP específico.
    """
    _check_monitor_or_admin(logged_user)
    endpoint = _get_endpoint_by_ip(ip, session)
    if not endpoint:
        raise HTTPException(status_code=404, detail="IP/Domínio não encontrado")
    last_data = (
        session.query(EndPointsData)
        .filter(EndPointsData.id_end_point == endpoint.id)
        .order_by(EndPointsData.id.desc())
        .first()
    )
    # Converte o objeto SQLAlchemy para schema Pydantic se existir
    if last_data:
        return EndPointsDataSchemas.model_validate(last_data)
    return None



@monitor_router.put("/")
async def update_ip_info(
    end_point: AddEndPointRequest,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> dict:
    """
    Atualiza as informações de um endereço IP específico.
    """
    _check_admin(logged_user)
    if not valid_end_point(end_point):
        raise HTTPException(status_code=400, detail="Endpoint inválido")

    endpoint = _get_endpoint_by_ip(end_point.ip, session)
    if not endpoint:
        raise HTTPException(status_code=404, detail="IP/Domínio não existente")

    oids = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == endpoint.id).one_or_none()
    if not oids:
        raise HTTPException(status_code=404, detail="IP/Domínio não existente")

    endpoint.ip = end_point.ip
    endpoint.interval = end_point.interval
    endpoint.version = end_point.version
    endpoint.community = end_point.community
    endpoint.port = end_point.port
    endpoint.user = end_point.user
    endpoint.authKey = end_point.authKey
    endpoint.privKey = end_point.privKey
    endpoint.webhook = end_point.webhook

    oids.sysDescr = end_point.sysDescr
    oids.sysName = end_point.sysName
    oids.sysUpTime = end_point.sysUpTime
    oids.hrProcessorLoad = end_point.hrProcessorLoad
    oids.memTotalReal = end_point.memTotalReal
    oids.memAvailReal = end_point.memAvailReal
    oids.hrStorageSize = end_point.hrStorageSize
    oids.hrStorageUsed = end_point.hrStorageUsed

    session.commit()
    return {"success": True, "message": f"Endereço IP {endpoint.ip} atualizado na lista de monitoramento."}



@monitor_router.delete("/{ip}")
async def delete_ip(
    ip: str,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> dict:
    """
    Remove um endereço IP da lista de monitoramento.
    """
    _check_admin(logged_user)
    endpoint = _get_endpoint_by_ip(ip, session)
    if not endpoint:
        raise HTTPException(status_code=404, detail="IP/Domínio não encontrado")
    session.delete(endpoint)
    session.commit()
    return {"success": True, "message": f"Endereço IP {ip} removido da lista de monitoramento."}


