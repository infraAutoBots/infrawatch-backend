from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, EndPoints, EndPointsData
from schemas import EndPointSchemas, EndPointsDataSchemas
from utils import valid_end_point
from typing import Dict, Any, Optional


monitor_router = APIRouter(prefix="/monitor", tags=["monitor"], dependencies=[Depends(verify_token)])


@monitor_router.post("/")
async def add_ip(end_point_schemas: EndPointSchemas, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Adicione um endereço Ip/Domínio à lista de monitoramento.

    Args:
        Ip/Domínio (str): O endereço IP a ser adicionado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_end_point(end_point_schemas):
        raise HTTPException(status_code=400, detail="Invalid endpoint")

    ip = session.query(EndPoints).filter(EndPoints.ip == end_point_schemas.ip).first()
    if ip:
        raise HTTPException(status_code=400, detail="Existing IP/Domain")
    else:
        new_endpoint = EndPoints(end_point_schemas.ip, end_point_schemas.interval,
                         end_point_schemas.version, end_point_schemas.community,
                         end_point_schemas.port, end_point_schemas.user, end_point_schemas.authKey,
                         end_point_schemas.privKey, end_point_schemas.webhook, logged_user.id)
        session.add(new_endpoint)
        session.commit()
        return {"message": f"Endereço IP {end_point_schemas.ip} adicionado à lista de monitoramento"}


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
async def get_ip_info(ip: str, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
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
async def update_ip_info(end_point_schemas: EndPointSchemas, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Atualize as informações de um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser atualizado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    if logged_user.access_level != "ADMIN":
        raise HTTPException(status_code=403, detail="Operation not permitted")
    if not valid_end_point(end_point_schemas):
        raise HTTPException(status_code=400, detail="Invalid endpoint")

    endpoint = session.query(EndPoints).filter(EndPoints.ip == end_point_schemas.ip).first()
    if not endpoint:
        raise HTTPException(status_code=400, detail="Not existing IP/Domain")
    else:
        endpoint.ip = end_point_schemas.ip
        endpoint.interval = end_point_schemas.interval
        endpoint.version = end_point_schemas.version
        endpoint.community = end_point_schemas.community
        endpoint.port = end_point_schemas.port
        endpoint.user = end_point_schemas.user
        endpoint.authKey = end_point_schemas.authKey
        endpoint.privKey = end_point_schemas.privKey
        endpoint.webhook = end_point_schemas.webhook
        session.commit()
        return {"message": f"Endereço IP {endpoint.ip} atualizado na lista de monitoramento."}


@monitor_router.delete("/{ip}")
async def delete_ip(ip: str, logged_user: Users = Depends(verify_token), session: Session = Depends(init_session)):
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


