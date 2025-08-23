import re
from ipaddress import ip_address
from schemas import EndPointSchemas



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


def valid_end_point(end_point_schemas: EndPointSchemas) -> bool:
    """Valida se o endpoint é um endereço IP ou domínio válido.

    Args:
        end_point_schemas (EndPointSchemas): O esquema do endpoint a ser validado.

    Returns:
        bool: True se o endpoint for válido, False caso contrário.
    """

    # Validações básicas
    if not is_valid_ip(end_point_schemas.ip) and not is_valid_url(end_point_schemas.ip):
        return False
    if end_point_schemas.interval <= 0:
        return False
    if end_point_schemas.version not in ["1", "2c", "3", ""]:
        return False
    if end_point_schemas.community and end_point_schemas.user:
        return False

    # so ping
    if (end_point_schemas.ip and end_point_schemas.interval and not end_point_schemas.version and
        not end_point_schemas.community and not end_point_schemas.port and not end_point_schemas.user and
        not end_point_schemas.authKey and not end_point_schemas.privKey):
        return True

    # ping snmp 1
    if (end_point_schemas.ip and end_point_schemas.interval and end_point_schemas.version == "1" and
        end_point_schemas.community and end_point_schemas.port):
        return True

    # ping snmp 2
    if (end_point_schemas.ip and end_point_schemas.interval and end_point_schemas.version == "2c" and
        end_point_schemas.community and end_point_schemas.port):
        return True

    # ping snmp 3
    if (end_point_schemas.ip and end_point_schemas.interval and end_point_schemas.version == "3" and
        not end_point_schemas.community and end_point_schemas.port):
        return True

    return False
