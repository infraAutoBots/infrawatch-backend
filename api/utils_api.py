import re
from ipaddress import ip_address
from api.schemas import AddEndPointRequest
from fastapi import HTTPException



def check_oids(end_point: AddEndPointRequest) -> bool:
    """Verifica se ha todos os oids.
    Args:
        end_point_oids_schemas (EndPointOIDsSchemas): O esquema dos OIDs a ser verificado.
    Returns:
        bool: True se todos os OIDs forem válidos, False caso contrário.
    """

    if (end_point.sysDescr and
        end_point.sysName and
        end_point.sysUpTime and
        end_point.hrProcessorLoad and
        end_point.memTotalReal and
        end_point.memAvailReal and
        end_point.hrStorageSize and
        end_point.hrStorageUsed):
        return True
    return False


def is_valid_ip(ip: str) -> bool:
    """Verifica se o endereço IP é válido.
    Args:
        ip (str): O endereço IP a ser verificado.
    Returns:
        bool: True se o endereço IP for válido, False caso contrário.
    """

    try:
        ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_url(url: str) -> bool:
    """Verifica se a URL é válida.
    Args:
        url (str): A URL a ser verificada.
    Returns:
        bool: True se a URL for válida, False caso contrário.
    """

    url_regex = re.compile(
    r'^(https?:\/\/)?'
    r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
    r'(:\d+)?'
    r'(\/[^\s]*)?$')
    return bool(url_regex.match(url))


def valid_end_point(end_point: AddEndPointRequest) -> bool:
    """Valida se o endpoint é um endereço IP ou domínio válido.
    Args:
        end_point_schemas (EndPointSchemas): O esquema do endpoint a ser validado.
    Returns:
        bool: True se o endpoint for válido, False caso contrário.
    """

    # Validações básicas
    if not is_valid_ip(end_point.ip) and not is_valid_url(end_point.ip):
        raise HTTPException(status_code=400, detail="Ip/domain inválido")

    if end_point.interval <= 0:
        raise HTTPException(status_code=400, detail="Intervalo inválido")

    # ping snmp 1  and ping snmp 2
    if (end_point.version == "1" or end_point.version == "2c"):
        if end_point.community is None or end_point.community.strip() == "":
            raise HTTPException(status_code=400, detail="Comunidade inválida")
        if end_point.port is None or end_point.port <= 0:
            raise HTTPException(status_code=400, detail="Porta inválida")
        if not check_oids(end_point):
            raise HTTPException(status_code=400, detail="OIDs inválidos")
        return True

    # ping snmp 3
    if end_point.version == "3":
        if end_point.port is None or end_point.port <= 0:
            raise HTTPException(status_code=400, detail="Porta inválida")
        if end_point.user is None or end_point.user.strip() == "":
            raise HTTPException(status_code=400, detail="Usuário inválido")
        if not check_oids(end_point):
            raise HTTPException(status_code=400, detail="OIDs inválidos")
        return True

    # so ping
    if (end_point.ip and end_point.interval and not end_point.version and
        not end_point.community and not end_point.port and not end_point.user and
        not end_point.authKey and not end_point.privKey and not check_oids(end_point)):
        return True
    
    if check_oids(end_point):
        raise HTTPException(status_code=400, detail="OIDs passados sem SNMP")

    raise HTTPException(status_code=400, detail="configuracao inválido")
