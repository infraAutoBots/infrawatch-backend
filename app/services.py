# - Funções assíncronas para verificar serviços.
# - Usa aiohttp para HTTP/HTTPS/WebSocket, asyncio para TCP/UDP, etc.
# - Para cada serviço, tenta uma conexão rápida (timeout 2s).
# - Retorna lista de serviços disponíveis.
# - Serviços: CoAP (UDP 5683), Telnet (TCP 23), Modbus (TCP 502), HTTP (TCP 80), HTTPS (TCP 443), SMTP (TCP 25), POP3 (TCP 110), IMAP (TCP 143), FTP (TCP 21), SFTP (TCP 22, mas SSH), DNS (UDP 53), TCP/UDP genérico (porta custom? assumimos padrões), WebSocket (ws://ip), SSH (TCP 22), MQTT (TCP 1883).

import asyncio
import aiohttp
from typing import List

SERVICES_PORTS = {
    "CoAP": ("udp", 5683),
    "Telnet": ("tcp", 23),
    "Modbus": ("tcp", 502),
    "HTTP": ("tcp", 80),
    "HTTPS": ("tcp", 443),
    "SMTP": ("tcp", 25),
    "POP3": ("tcp", 110),
    "IMAP": ("tcp", 143),
    "FTP": ("tcp", 21),
    "SFTP": ("tcp", 22),  # Via SSH
    "DNS": ("udp", 53),
    "WebSocket": ("ws", 80),  # Assumindo ws://
    "SSH": ("tcp", 22),
    "MQTT": ("tcp", 1883),
    # TCP/UDP baixo nível: Assumimos portas comuns, ou adicione params
}


async def check_services(ip: str, only_these: List[str] = None) -> List[str]:
    available = []
    services_to_check = only_these or list(SERVICES_PORTS.keys())
    tasks = [check_service(ip, service) for service in services_to_check]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for service, result in zip(services_to_check, results):
        if isinstance(result, bool) and result:
            available.append(service)
    return available


async def check_service(ip: str, service: str) -> bool:
    proto, port = SERVICES_PORTS.get(service, (None, None))
    if not proto:
        return False
    try:
        if proto == "tcp":
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
            writer.close()
            await writer.wait_closed()
            return True
        elif proto == "udp":
            transport, _ = await asyncio.wait_for(
                asyncio.get_event_loop().create_datagram_endpoint(lambda: asyncio.Protocol(), remote_addr=(ip, port)),
                timeout=2)
            transport.close()
            return True
        elif proto == "ws":
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"ws://{ip}:{port}", timeout=2):
                    return True
    except Exception:
        return False
    return False
