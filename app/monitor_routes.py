from fastapi import APIRouter, Depends, HTTPException
from dependencies import init_session, verify_token
from sqlalchemy.orm import Session
from models import Users, Devices, DeviceData
from schemas import DeviceSchemas, DeviceDataSchemas


monitor_router = APIRouter(prefix="/monitor", tags=["monitor"])


# token jwt
@monitor_router.post("/")
async def add_ip(device_schemas: DeviceSchemas, user: Users = Depends(verify_token), session: Session = Depends(init_session)):
    """Adicione um endereço Ip/Domínio à lista de monitoramento.

    Args:
        Ip/Domínio (str): O endereço IP a ser adicionado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    # verificar se esta logado X
    # fazer a validacao de device valido X
    # verificar se quem esta a add e um admin X
    # pegar o id deste admin e add no id_user X
    ip = session.query(Devices).filter(Devices.ip == device_schemas.ip).first()
    if not ip:
        raise HTTPException(status_code=400, detail="Existing IP/Domain")
    else:
        new_device = Devices(device_schemas.ip, device_schemas.interval,
                         device_schemas.version, device_schemas.community,
                         device_schemas.port, device_schemas.user, device_schemas.authKey,
                         device_schemas.privKey, device_schemas.id_user)
        session.add(new_device)
        session.commit()
        return {"message": f" {device_schemas.ip} adicionado à lista de monitoramento."}


@monitor_router.get("/{ip}")
async def get_ip_info(ip: str, user: Users = Depends(verify_token)):
    """Obtenha informações sobre um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser consultado.

    Returns:
        dict: As informações do IP consultado.
    """

    # verificar se esta logado
    # qual quer um pode pegar os dados individual nao importa o usuario

    return {"ip": ip}


@monitor_router.put("/{ip}")
async def update_ip_info(ip: str):
    """Atualize as informações de um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser atualizado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    # verificar se esta logado
    # verificar se o usuario e admin
    # validar as alteracoes
    # pegar o id deste admin e fazer o update
    # verificar se endponit exite 

    return {"message": f"Endereço IP {ip} atualizado na lista de monitoramento."}


@monitor_router.delete("/{ip}")
async def delete_ip(ip: str):
    """Remova um endereço IP da lista de monitoramento.

    Args:
        ip/domínio (str): O endereço IP a ser removido.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """

    # verificar se esta logado
    # verificar se ele e admin e se o end point existe

    return {"message": f"Endereço IP {ip} removido da lista de monitoramento."}


@monitor_router.get("/status")
async def get_status():
    """Obtenha o status do serviço de monitoramento.

    Returns:
        dict: O status do serviço.
    """

    # verificar se esta logado
    #qualque um pode fazer isso

    return {"status": "O serviço de monitoramento está em execução."}

