import asyncio
from icmplib import async_ping

async def ping_individual(address):
    host = await async_ping(address, count=3, interval=0.2, timeout=2)
    status = "ativo" if host.is_alive else "inativo"
    print(f'{address}: {status} (RTT média: {host.avg_rtt:.2f} ms)')

async def ping_multiplos(enderecos):
    tarefas = [asyncio.create_task(ping_individual(ip)) for ip in enderecos]
    await asyncio.gather(*tarefas)

if __name__ == "__main__":
    enderecos = ['8.8.8.8', '1.1.1.1', '192.168.0.1', '4.2.2.2', '127.0.0.1']
    asyncio.run(ping_multiplos(enderecos))
