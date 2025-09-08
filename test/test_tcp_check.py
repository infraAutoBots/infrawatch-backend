#!/usr/bin/env python3
"""
Script de teste para verificar a nova implementação do fast_tcp_check
"""
import asyncio
import aiohttp
import os
import sys
from datetime import datetime

# Adicionar o diretório do monitor ao path
sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend/monitor')

class TestTCPCheck:
    def __init__(self, logger=True):
        self.logger = logger
        # Portas TCP comuns para teste
        self.tcp_ports = [80, 443, 22, 21, 25, 53, 110, 143, 3306, 5432, 6379, 27017, 8080, 8443, 3389, 5900, 161, 389, 1521, 9200]

    async def _check_http_https(self, endpoint: str):
        """Verifica HTTP/HTTPS com timeout adequado e múltiplas tentativas"""
        protocols_and_paths = [
            ("https", "/"),
            ("http", "/"),
            ("https", ""),
            ("http", "")
        ]
        
        for protocol, path in protocols_and_paths:
            url = f"{protocol}://{endpoint}{path}"
            try:
                timeout = aiohttp.ClientTimeout(total=5, connect=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        url, 
                        allow_redirects=True,
                        ssl=False if protocol == "https" else None  # Ignora erros SSL para testes
                    ) as resp:
                        if resp.status < 500:  # Aceita 2xx, 3xx, 4xx como "vivo"
                            if self.logger:
                                print(f"HTTP check {endpoint}: {protocol.upper()} {resp.status} - SUCCESS")
                            return True
                        elif self.logger:
                            print(f"HTTP check {endpoint}: {protocol.upper()} {resp.status} - Server Error")
            except asyncio.TimeoutError:
                if self.logger:
                    print(f"HTTP check {endpoint}: {protocol.upper()} timeout")
            except Exception as e:
                if self.logger:
                    print(f"HTTP check {endpoint}: {protocol.upper()} error - {type(e).__name__}")
        
        return False
    
    async def _check_tcp_ports(self, endpoint: str):
        """Verifica portas TCP comuns com melhor gestão de tasks"""
        async def check_single_port(port):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(endpoint, port), timeout=3)
                writer.close()
                await writer.wait_closed()
                if self.logger:
                    print(f"TCP port check {endpoint}:{port} - SUCCESS")
                return True
            except Exception as e:
                if self.logger:
                    print(f"TCP port check {endpoint}:{port} - {type(e).__name__}")
                return False

        # Priorizar portas mais comuns
        priority_ports = [80, 443, 22, 8080, 8443]
        other_ports = [p for p in self.tcp_ports if p not in priority_ports]
        
        # Verificar portas prioritárias primeiro
        for port in priority_ports:
            if port in self.tcp_ports:
                result = await check_single_port(port)
                if result:
                    return True
        
        # Se portas prioritárias falharam, verificar outras em paralelo
        if other_ports:
            tasks = [asyncio.create_task(check_single_port(port)) for port in other_ports[:10]]  # Limite para evitar overhead
            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=5)
                
                # Cancelar tasks pendentes
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # Verificar se alguma teve sucesso
                for task in done:
                    try:
                        if await task:
                            return True
                    except Exception:
                        pass
            except asyncio.TimeoutError:
                # Cancelar todas as tasks em caso de timeout geral
                for task in tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
        
        return False

    async def fast_tcp_check(self, endpoint: str):
        """
        Verifica conectividade TCP com prioridade para HTTP/HTTPS e fallback para portas TCP.
        Corrige falsos negativos melhorando timeouts e lógica de verificação.
        """
        if self.logger:
            print(f"TCP check iniciado para {endpoint}")
        
        # Primeiro: Teste HTTP/HTTPS com timeout maior e melhor tratamento
        http_success = await self._check_http_https(endpoint)
        if http_success:
            if self.logger:
                print(f"TCP check {endpoint}: HTTP/HTTPS respondeu - SUCCESS")
            return True
        
        # Segundo: Fallback para verificação de portas TCP comuns
        tcp_success = await self._check_tcp_ports(endpoint)
        if tcp_success:
            if self.logger:
                print(f"TCP check {endpoint}: Porta TCP respondeu - SUCCESS") 
            return True
        
        if self.logger:
            print(f"TCP check {endpoint}: Todas as verificações falharam - FAILED")
        return False

async def test_endpoints():
    """Testa vários endpoints conhecidos"""
    tester = TestTCPCheck(logger=True)
    
    test_hosts = [
        "dgg.gg",
        "google.com", 
        "github.com",
        "httpbin.org",
        "1.1.1.1",        # Cloudflare DNS (só ping, não HTTP)
        "192.168.1.1",    # IP local típico (provavelmente não responde)
        "fake-host-12345.com"  # Host inexistente
    ]
    
    print(f"=== Teste TCP Check - {datetime.now()} ===\n")
    
    for host in test_hosts:
        print(f"\n--- Testando {host} ---")
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await tester.fast_tcp_check(host)
            elapsed = asyncio.get_event_loop().time() - start_time
            status = "✅ ONLINE" if result else "❌ OFFLINE"
            print(f"Resultado: {status} (tempo: {elapsed:.2f}s)")
        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"Erro: {e} (tempo: {elapsed:.2f}s)")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
