from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, EndPoints, EndPointsData, EndPointOIDs
from schemas import EndPointsDataSchemas, AddEndPointRequest
from utils import valid_end_point
from typing import Dict, Any, Optional


monitor_router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(verify_token)])


@monitor_router.post("/")
async def add_ip(
    end_point: AddEndPointRequest,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> dict:
    """Adicione um endereço Ip/Domínio à lista de monitoramento.

    Args:
        Ip/Domínio (str): O endereço IP a ser adicionado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    # print(end_point)
    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_end_point(end_point):
        raise HTTPException(status_code=400, detail="Invalid endpoint")

    ip = session.query(EndPoints).filter(EndPoints.ip == end_point.ip).first()
    if ip:
        raise HTTPException(status_code=400, detail="Existing IP/Domain")
    else:
        new_endpoint = EndPoints(end_point.ip,
                                 end_point.interval,
                                 end_point.version,
                                 end_point.community,
                                 end_point.port,
                                 end_point.user,
                                 end_point.authKey,
                                 end_point.privKey,
                                 end_point.webhook,
                                 logged_user.id)
        session.add(new_endpoint)
        session.commit()
        new_endpoint_id = session.query(EndPoints).filter(EndPoints.ip == end_point.ip).first().id
        new_endpoint_oids = EndPointOIDs(new_endpoint_id,
                                         end_point.sysDescr,
                                         end_point.sysName,
                                         end_point.sysUpTime,
                                         end_point.hrProcessorLoad,
                                         end_point.memTotalReal,
                                         end_point.memAvailReal,
                                         end_point.hrStorageSize,
                                         end_point.hrStorageUsed)
        session.add(new_endpoint_oids)
        session.commit()
        return {"message": f"Endereço IP {end_point.ip} adicionado à lista de monitoramento"}


@monitor_router.get("/status")
async def get_status(session: Session = Depends(init_session)):
    """Obtenha o status de todos os dispositivos monitorados.

    Args:
        session (Session, optional): _description_. Defaults to Depends(init_session).

    Returns:
        dict: O status do serviço.
    """

    list_data: Dict[str, Any] = []
    all_data = session.query(EndPoints).all()
    for data in all_data:
        endpoint_data = session.query(EndPointsData).filter(EndPointsData.id_end_point == data.id).all()
        list_data.append({"endpoint": data.ip, "data": endpoint_data})

    return {"data": list_data}


@monitor_router.get("/{ip}", response_model=Optional[EndPointsDataSchemas])
async def get_ip_info(
    ip: str,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)):
    """Obtenha informações sobre um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser consultado.

    Returns:
        dict: As informações do IP consultado.
    """

    if logged_user.access_level not in ["ADMIN", "MONITOR"]:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    endpoint = session.query(EndPoints).filter(EndPoints.ip == ip).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="IP/Domain not found")
    else:
        last_data = (session.query(EndPointsData).filter(EndPointsData.id_end_point == endpoint.id)
            .order_by(EndPointsData.id.desc()).first())
        # return {"ip": ip, "data": last_data}
        return last_data


@monitor_router.put("/")
async def update_ip_info(
    end_point: AddEndPointRequest,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)) -> dict:
    """Atualize as informações de um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser atualizado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_end_point(end_point):
        raise HTTPException(status_code=400, detail="Invalid endpoint")

    endpoint = session.query(EndPoints).filter(EndPoints.ip == end_point.ip).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Not existing IP/Domain")
    
    oids = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == endpoint.id).first()
    if not oids:
        raise HTTPException(status_code=404, detail="Not existing IP/Domain")
    else:
        endpoint.ip = end_point.ip
        endpoint.interval = end_point.interval
        endpoint.version = end_point.version
        endpoint.community = end_point.community
        endpoint.port = end_point.port
        endpoint.user = end_point.user
        endpoint.authKey = end_point.authKey
        endpoint.privKey = end_point.privKey
        endpoint.webhook = end_point.webhook

        if oids:
            oids.sysDescr = end_point.sysDescr
            oids.sysName = end_point.sysName
            oids.sysUpTime = end_point.sysUpTime
            oids.hrProcessorLoad = end_point.hrProcessorLoad
            oids.memTotalReal = end_point.memTotalReal
            oids.memAvailReal = end_point.memAvailReal
            oids.hrStorageSize = end_point.hrStorageSize
            oids.hrStorageUsed = end_point.hrStorageUsed

        session.commit()
        return {"message": f"Endereço IP {endpoint.ip} atualizado na lista de monitoramento."}


@monitor_router.delete("/{ip}")
async def delete_ip(
    ip: str,
    logged_user: Users = Depends(verify_token),
    session: Session = Depends(init_session)):
    """Remova um endereço IP da lista de monitoramento.

    Args:
        ip/domínio (str): O endereço IP a ser removido.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    ip = session.query(EndPoints).filter(EndPoints.ip == ip).first()
    if not ip:
        raise HTTPException(status_code=404, detail="IP/Domain not found")
    session.delete(ip)
    session.commit()
    return {"message": f"Endereço IP {ip} removido da lista de monitoramento."}


