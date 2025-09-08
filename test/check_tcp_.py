import asyncio
import aiohttp
from ipaddress import ip_address
import time

async def check_port_first(endpoint, port, timeout, verbose):
    try:
        start = time.time()
        _, writer = await asyncio.wait_for(asyncio.open_connection(endpoint, port), timeout)
        writer.close()

        import asyncio
        import aiohttp
        from ipaddress import ip_address

        async def fast_tcp_check(ip: str, ports=None, timeout=0.3, verbose=False):
            async def check_port(port):
                try:
                    _, writer = await asyncio.wait_for(
                        asyncio.open_connection(ip, port), timeout=timeout
                    )
                    writer.close()
                    await writer.wait_closed()
                    if verbose:
                        print(f"TCP {port} OK")
                    return port
                except Exception as e:
                    if verbose:
                        print(f"TCP {port} falhou: {e}")
                    return None

            ports = ports or [80, 443, 22, 21, 25, 53, 110, 143, 3306, 5432, 6379,
                              27017, 8080, 8443, 3389, 5900, 161, 389, 1521, 9200]
            tasks = [check_port(port) for port in ports]
            results = await asyncio.gather(*tasks)
            open_ports = [p for p in results if p]
            return open_ports

        async def fast_http_check(endpoint: str, paths=None, timeout=1, headers=None, verbose=False):
            paths = paths or ["/"]
            headers = headers or {"User-Agent": "InfraWatchMonitor/1.0"}
            for path in paths:
                for url in [f"http://{endpoint}{path}", f"https://{endpoint}{path}"]:
                    try:
                        async with aiohttp.ClientSession(headers=headers) as session:
                            async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                                if resp.status < 500:
                                    if verbose:
                                        print(f"HTTP {url} OK ({resp.status})")
                                    return url
                    except Exception as e:
                        if verbose:
                            print(f"HTTP {url} falhou: {e}")
                        continue
            return None

if __name__ == "__main__":
    async def main():
        endpoint = input("Digite o IP ou domínio para testar: ").strip()
        print("Testando TCP...")
        open_ports = await fast_tcp_check(endpoint, verbose=True)
        print("Portas abertas:", open_ports)
        print("Testando HTTP...")
        http_ok = await fast_http_check(endpoint, verbose=True)
        print("HTTP OK:", http_ok)

asyncio.run(main())
