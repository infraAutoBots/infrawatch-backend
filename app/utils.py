import re
from ipaddress import ip_address
from schemas import DeviceSchemas



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


def valid_device(device_schemas: DeviceSchemas) -> bool:
    """Valida se o dispositivo é um endereço IP ou domínio válido.

    Args:
        device_schemas (DeviceSchemas): O esquema do dispositivo a ser validado.

    Returns:
        bool: True se o dispositivo for válido, False caso contrário.
    """

    # Validações básicas
    if not is_valid_ip(device_schemas.ip) and not is_valid_url(device_schemas.ip):
        return False
    if device_schemas.interval <= 0:
        return False
    if device_schemas.version not in ["1", "2c", "3", ""]:
        return False
    if device_schemas.community and device_schemas.user:
        return False

    # so ping
    if (device_schemas.ip and device_schemas.interval and not device_schemas.version and
        not device_schemas.community and not device_schemas.port and not device_schemas.user and
        not device_schemas.authKey and not device_schemas.privKey):
        return True

    # ping snmp 1
    if (device_schemas.ip and device_schemas.interval and device_schemas.version == "1" and
        device_schemas.community and device_schemas.port):
        return True

    # ping snmp 2
    if (device_schemas.ip and device_schemas.interval and device_schemas.version == "2c" and
        device_schemas.community and device_schemas.port):
        return True

    # ping snmp 3
    if (device_schemas.ip and device_schemas.interval and device_schemas.version == "3" and
        not device_schemas.community and device_schemas.port):
        return True

    return False
