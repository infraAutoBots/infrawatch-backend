# app_optimized.py
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from icmplib import async_multiping
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from contextlib import asynccontextmanager
from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd, SnmpEngine, UdpTransportTarget,
    CommunityData, ContextData, ObjectType, ObjectIdentity, UsmUserData
)

load_dotenv()

# Configuração de logging otimizada
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class HostStatus:
    ip: str
    is_alive: bool = False
    snmp_data: Dict = None
    last_updated: datetime = None
    ping_rtt: float = 0.0

# Pool global de engines SNMP (reutilização)
_snmp_engines = asyncio.Queue(maxsize=10)
_engines_created = 0

@asynccontextmanager
async def get_snmp_engine():
    global _engines_created
    try:
        engine = _snmp_engines.get_nowait()
    except asyncio.QueueEmpty:
        if _engines_created < 10:
            engine = SnmpEngine()
            _engines_created += 1
        else:
            engine = await _snmp_engines.get()
    
    try:
        yield engine
    finally:
        try:
            _snmp_engines.put_nowait(engine)
        except asyncio.QueueFull:
            engine.transport_dispatcher.close_dispatcher()

# OIDs otimizados (apenas os mais essenciais)
ESSENTIAL_OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
    "cpu": "1.3.6.1.4.1.2021.11.9.0"  # Apenas um OID por métrica
}

class OptimizedMonitor:
    def __init__(self):
        self.hosts_status: Dict[str, HostStatus] = {}
        self.lock = asyncio.Lock()
        self.tcp_ports = [int(p) for p in os.getenv("TCP_PORTS", "80,443,22,161").split(",")]
        
        # Inicialização dos hosts
        # criar uma sessão e pegar todos os ips/host
        ips = ['192.168.8.159', '192.168.8.146', '192.168.8.121', '127.0.0.1', '127.0.0.2']
        for ip in ips:
            self.hosts_status[ip] = HostStatus(ip=ip)
    
    async def fast_ping_check(self, ips: List[str]) -> Dict[str, Tuple[bool, float]]:
        """Ping ultra-rápido com timeout agressivo"""
        try:
            hosts = await async_multiping(
                ips, 
                count=1,  # Reduzido para 1
                timeout=0.5,  # Timeout muito mais agressivo
                interval=0.02  # Intervalo menor
            )
            return {
                host.address: (host.is_alive, host.avg_rtt or 0.0) 
                for host in hosts
            }
        except Exception as e:
            logger.debug(f"Ping error: {e}")
            return {ip: (False, 0.0) for ip in ips}
    
    async def fast_tcp_check(self, ip: str) -> bool:
        """TCP check paralelo e ultra-rápido"""
        async def check_port(port):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), 
                    timeout=0.3  # Timeout agressivo
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False
        
        # Testa apenas as primeiras 2 portas em paralelo
        tasks = [check_port(port) for port in self.tcp_ports[:2]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(r is True for r in results)
    
    async def fast_snmp_check(self, ip: str) -> Optional[Dict[str, str]]:
        """SNMP otimizado com pool de engines"""
        async with get_snmp_engine() as engine:
            try:
                auth_data = CommunityData(os.getenv("SNMP_COMMUNITY", "public"), mpModel=1)
                
                # Apenas sysDescr para verificação rápida de conectividade
                error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                    get_cmd(
                        engine, auth_data,
                        await UdpTransportTarget.create((ip, 161), timeout=0.5, retries=0),
                        ContextData(), 
                        ObjectType(ObjectIdentity(ESSENTIAL_OIDS["sysDescr"]))
                    ),
                    timeout=1.0
                )
                
                if not (error_indication or error_status or error_index):
                    return {"sysDescr": str(var_binds[0][1])}
            except Exception as e:
                logger.debug(f"SNMP error for {ip}: {e}")
        return None
    
    async def check_single_host(self, host_status: HostStatus) -> HostStatus:
        """Verificação completa de um host com fallbacks inteligentes"""
        ip = host_status.ip
        
        # 1. Ping primeiro (mais rápido)
        ping_results = await self.fast_ping_check([ip])
        is_alive, rtt = ping_results.get(ip, (False, 0.0))
        
        snmp_data = None
        
        if is_alive:
            # Se ping OK, tenta SNMP
            snmp_data = await self.fast_snmp_check(ip)
        else:
            # Se ping falhou, tenta TCP como fallback
            tcp_alive = await self.fast_tcp_check(ip)
            if tcp_alive:
                is_alive = True
                # Se TCP OK, tenta SNMP também
                snmp_data = await self.fast_snmp_check(ip)
        
        return HostStatus(
            ip=ip,
            is_alive=is_alive,
            snmp_data=snmp_data or {},
            last_updated=datetime.now(timezone.utc),
            ping_rtt=rtt
        )
    
    async def monitoring_cycle(self):
        """Um ciclo de monitoramento otimizado"""
        ips = list(self.hosts_status.keys())
        if not ips:
            return
        
        # Verifica todos os hosts em paralelo
        current_statuses = list(self.hosts_status.values())
        tasks = [self.check_single_host(host) for host in current_statuses]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            async with self.lock:
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error checking {ips[i]}: {result}")
                        continue
                    
                    self.hosts_status[result.ip] = result
                    # chamo uma fucao logged que armazenas os dados na db
                    status_icon = "🟢" if result.is_alive else "🔴"
                    snmp_icon = "📊" if result.snmp_data else "❌"
                    
                    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | SNMP: {snmp_icon}")
                    
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
    
    async def run_monitoring(self, interval: float = 2.0):
        """Loop principal otimizado"""
        logger.info("🚀 Iniciando monitoramento otimizado...")
        
        while True:
            start_time = asyncio.get_event_loop().time()
            
            await self.monitoring_cycle()
            
            # Calcula tempo decorrido e ajusta sleep
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.1, interval - elapsed)
            
            logger.debug(f"Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

# Versão ainda mais otimizada para casos extremos
class HyperFastMonitor(OptimizedMonitor):
    """Versão para quando você precisa de velocidade máxima"""
    
    async def hyper_check(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Verificação híbrida ultra-rápida"""
        # Ping e SNMP em paralelo
        ping_task = self.fast_ping_check([ip])
        snmp_task = self.fast_snmp_check(ip)
        
        ping_result, snmp_result = await asyncio.gather(
            ping_task, snmp_task, return_exceptions=True
        )
        
        is_alive_ping = False
        if not isinstance(ping_result, Exception):
            is_alive_ping = ping_result.get(ip, (False, 0.0))[0]
        
        has_snmp = not isinstance(snmp_result, Exception) and snmp_result
        
        # Se qualquer um funcionar, consideramos vivo
        is_alive = is_alive_ping or has_snmp
        snmp_desc = snmp_result.get('sysDescr', '') if has_snmp else None
        
        return is_alive, snmp_desc
    
    async def hyper_monitoring_cycle(self):
        """Ciclo de monitoramento hiper-otimizado"""
        ips = list(self.hosts_status.keys())
        tasks = [self.hyper_check(ip) for ip in ips]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        async with self.lock:
            for i, result in enumerate(results):
                ip = ips[i]
                if isinstance(result, Exception):
                    continue
                
                is_alive, snmp_desc = result
                self.hosts_status[ip] = HostStatus(
                    ip=ip,
                    is_alive=is_alive,
                    snmp_data={'sysDescr': snmp_desc} if snmp_desc else {},
                    last_updated=datetime.now(timezone.utc)
                )
                
                status = "🟢" if is_alive else "🔴"
                snmp = "📊" if snmp_desc else "❌"
                print(f"{status} {ip} {snmp}")

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "hyper"


    if mode == "hyper":
        print("🏃‍♂️ Modo HYPER-RÁPIDO ativado!")
        monitor = HyperFastMonitor()
        asyncio.run(monitor.run_monitoring(interval=1.0))
    else:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor()
        asyncio.run(monitor.run_monitoring(interval=2.0))
