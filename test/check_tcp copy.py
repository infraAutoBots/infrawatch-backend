import asyncio
import aiohttp
from ipaddress import ip_address
import time

async def check_tcp_or_http(endpoint: str, ports=None, timeout=2, paths=None, headers=None, verbose=False):

    async def check_port_first(endpoint, port, timeout):
        try:
            _, writer = await asyncio.wait_for(asyncio.open_connection(endpoint, port), timeout)
            writer.close()
            await writer.wait_closed()
            return {"port": port}
        except Exception:
            return None

    ports = [80, 443, 22, 21, 25, 53, 110, 143, 3306, 5432, 6379, 27017, 8080, 8443, 3389, 5900, 161, 389, 1521, 9200]
    tasks = [asyncio.create_task(check_port_first(endpoint, port, timeout)) for port in ports]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in done:
        result = task.result()
        if result:
            return {"status": True, "open_port": result["port"]}

    # Teste HTTP/HTTPS real (sequencial, retorna no primeiro sucesso)
    paths = paths or ["/"]
    headers = headers or {"User-Agent": "InfraWatchMonitor/1.0"}
    for path in paths:
        for url in [f"http://{endpoint}{path}", f"https://{endpoint}{path}"]:
            try:
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                        if resp.status < 500:
                            return {"status": True, "http_success": {"url": url, "http_status": resp.status}}
            except Exception as e:
                continue

    return {"status": False, "reason": "Nenhuma porta ou HTTP respondeu"}

if __name__ == "__main__":
    async def main():
        endpoint = "ddg.gg"
        result = await check_tcp_or_http(endpoint, verbose=True)
        print("Resultado:", result)

    asyncio.run(main())
