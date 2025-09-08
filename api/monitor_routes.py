from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, EndPoints, EndPointsData, EndPointOIDs
from schemas import EndPointsDataSchemas, AddEndPointRequest
from utils_api import valid_end_point
from typing import Dict, Any, Optional



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
        end_point.nickname,
        end_point.interval,
        end_point.version,
        end_point.community,
        end_point.port,
        end_point.user,
        end_point.active,
        end_point.authKey,
        end_point.privKey,
        logged_user.id
    )
    session.add(new_endpoint)
    session.commit()

    if (not end_point.sysDescr and not end_point.sysName and not end_point.sysUpTime and
        not end_point.hrProcessorLoad and not end_point.memTotalReal and not end_point.memAvailReal and
        not end_point.hrStorageSize and not end_point.hrStorageUsed and not end_point.hrStorageDescr and 
        not end_point.ifOperStatus and not end_point.ifInOctets and not end_point.ifOutOctets):
        new_endpoint_oids = EndPointOIDs(
            new_endpoint.id,
            end_point.sysDescr or "1.3.6.1.2.1.1.1.0",
            end_point.sysName or "1.3.6.1.2.1.1.5.0",
            end_point.sysUpTime or "1.3.6.1.2.1.1.3.0",
            end_point.hrProcessorLoad or "1.3.6.1.2.1.25.3.3.1.2",
            end_point.memTotalReal or "1.3.6.1.4.1.2021.4.5.0",
            end_point.memAvailReal or "1.3.6.1.4.1.2021.4.6.0",
            end_point.hrStorageSize or "1.3.6.1.2.1.25.2.3.1.5",
            end_point.hrStorageUsed or "1.3.6.1.2.1.25.2.3.1.6",
            end_point.hrStorageDescr or "1.3.6.1.2.1.25.2.3.1.3",
            end_point.ifOperStatus or "1.3.6.1.2.1.2.2.1.8",
            end_point.ifInOctets or "1.3.6.1.2.1.2.2.1.10",
            end_point.ifOutOctets or "1.3.6.1.2.1.2.2.1.16"
        )
        session.add(new_endpoint_oids)
        session.commit()
    return {"success": True, "message": f"Endereço IP {end_point.ip} adicionado à lista de monitoramento."}



@monitor_router.get("/history", response_model=Dict[str, Any])
async def get_history(session: Session = Depends(init_session)) -> dict:
    """
    Obtém o histórico de todos os dispositivos monitorados.
    """
    list_data = []
    all_data = session.query(EndPoints).all()
    for data in all_data:
        endpoint_data = session.query(EndPointsData).filter(EndPointsData.id_end_point == data.id).all()
        endpoint_data_serialized = []
        for d in endpoint_data:
            # Cria um dicionário com os dados do EndPointsData e adiciona o campo active do endpoint
            data_dict = {
                'id_end_point': d.id_end_point,
                'status': d.status,
                'active': data.active,  # Campo do endpoint
                'sysDescr': d.sysDescr,
                'sysName': d.sysName,
                'sysUpTime': d.sysUpTime,
                'hrProcessorLoad': d.hrProcessorLoad,
                'memTotalReal': d.memTotalReal,
                'memAvailReal': d.memAvailReal,
                'hrStorageSize': d.hrStorageSize,
                'hrStorageUsed': d.hrStorageUsed,
                'hrStorageDescr': d.hrStorageDescr,
                'ifOperStatus': d.ifOperStatus,
                'ifInOctets': d.ifInOctets,
                'ifOutOctets': d.ifOutOctets,
                'ping_rtt': d.ping_rtt,
                'snmp_rtt': d.snmp_rtt,
                'last_updated': d.last_updated
            }
            endpoint_data_serialized.append(EndPointsDataSchemas.model_validate(data_dict))
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
        
        last_data_serialize = None
        if last_data:
            # Cria um dicionário com os dados do EndPointsData e adiciona o campo active do endpoint
            data_dict = {
                'id_end_point': last_data.id_end_point,
                'status': last_data.status,
                'active': data.active,  # Campo do endpoint
                'sysDescr': last_data.sysDescr,
                'sysName': last_data.sysName,
                'sysUpTime': last_data.sysUpTime,
                'hrProcessorLoad': last_data.hrProcessorLoad,
                'memTotalReal': last_data.memTotalReal,
                'memAvailReal': last_data.memAvailReal,
                'hrStorageSize': last_data.hrStorageSize,
                'hrStorageUsed': last_data.hrStorageUsed,
                'hrStorageDescr': last_data.hrStorageDescr,
                'ifOperStatus': last_data.ifOperStatus,
                'ifInOctets': last_data.ifInOctets,
                'ifOutOctets': last_data.ifOutOctets,
                'ping_rtt': last_data.ping_rtt,
                'snmp_rtt': last_data.snmp_rtt,
                'last_updated': last_data.last_updated
            }
            last_data_serialize = EndPointsDataSchemas.model_validate(data_dict)
        
        snmp = None
        if last_data:
            snmp = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == last_data.id)
        list_data.append({"endpoint": data.ip, "snmp": True if snmp else False, "data": last_data_serialize})

    def total_depravado(data:EndPointsDataSchemas):
        return (data and data.status 
                and data.sysDescr is None 
                and data.sysName is None
                and data.sysUpTime is None
                and data.hrProcessorLoad is None
                and data.memTotalReal is None
                and data.memAvailReal is None
                and data.hrStorageSize is None
                and data.hrStorageUsed is None)

    return {
        "monitors": list_data,
        "total": len(list_data),
        "total_online": sum(1 for m in list_data
                                if m["data"] and m["data"].status),
        "total_offline": sum(1 for m in list_data
                             if m["data"] and not m["data"].status),
        "total_depravado": sum(1 for m in list_data
                            if m["data"] and m["snmp"] and total_depravado(m["data"]))
    }


 
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
        # Cria um dicionário com os dados do EndPointsData e adiciona o campo active do endpoint
        data_dict = {
            'id_end_point': last_data.id_end_point,
            'status': last_data.status,
            'active': endpoint.active,  # Campo do endpoint, não do data
            'sysDescr': last_data.sysDescr,
            'sysName': last_data.sysName,
            'sysUpTime': last_data.sysUpTime,
            'hrProcessorLoad': last_data.hrProcessorLoad,
            'memTotalReal': last_data.memTotalReal,
            'memAvailReal': last_data.memAvailReal,
            'hrStorageSize': last_data.hrStorageSize,
            'hrStorageUsed': last_data.hrStorageUsed,
            'hrStorageDescr': last_data.hrStorageDescr,
            'ifOperStatus': last_data.ifOperStatus,
            'ifInOctets': last_data.ifInOctets,
            'ifOutOctets': last_data.ifOutOctets,
            'ping_rtt': last_data.ping_rtt,
            'snmp_rtt': last_data.snmp_rtt,
            'last_updated': last_data.last_updated
        }
        return EndPointsDataSchemas.model_validate(data_dict)
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
    endpoint.active = end_point.active
    endpoint.authKey = end_point.authKey
    endpoint.privKey = end_point.privKey

    oids.sysDescr = end_point.sysDescr
    oids.sysName = end_point.sysName
    oids.sysUpTime = end_point.sysUpTime
    oids.hrProcessorLoad = end_point.hrProcessorLoad
    oids.memTotalReal = end_point.memTotalReal
    oids.memAvailReal = end_point.memAvailReal
    oids.hrStorageSize = end_point.hrStorageSize
    oids.hrStorageUsed = end_point.hrStorageUsed
    oids.hrStorageDescr = end_point.hrStorageDescr

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


