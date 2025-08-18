from fastapi import APIRouter



monitor_router = APIRouter(prefix="/monitor", tags=["monitor"])


@monitor_router.post("/ips")
async def add_ip(ip: str):
    """Adicione um endereço IP à lista de monitoramento.

    Args:
        ip/domínio (str): O endereço IP a ser adicionado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """
    return {"message": f"Endereço IP {ip} adicionado à lista de monitoramento."}


@monitor_router.get("/ips/{ip}")
async def get_ip_info(ip: str):
    """Obtenha informações sobre um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser consultado.

    Returns:
        dict: As informações do IP consultado.
    """
    return {"ip": ip}


@monitor_router.put("/ips/{ip}")
async def update_ip_info(ip: str):
    """Atualize as informações de um endereço IP específico.

    Args:
        ip/domínio (str): O endereço IP a ser atualizado.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """
    return {"message": f"Endereço IP {ip} atualizado na lista de monitoramento."}


@monitor_router.delete("/ips/{ip}")
async def delete_ip(ip: str):
    """Remova um endereço IP da lista de monitoramento.

    Args:
        ip/domínio (str): O endereço IP a ser removido.

    Returns:
        dict: Uma mensagem indicando o resultado da operação.
    """
    return {"message": f"Endereço IP {ip} removido da lista de monitoramento."}


# Obter status do serviço
@monitor_router.get("/status")
async def get_status():
    """Obtenha o status do serviço de monitoramento.

    Returns:
        dict: O status do serviço.
    """
    return {"status": "O serviço de monitoramento está em execução."}

