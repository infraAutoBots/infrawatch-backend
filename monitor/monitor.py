import asyncio
import logging
from tkinter import NO
from typing import Dict, List, Optional, Tuple
from unittest import result
from icmplib import async_multiping
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from contextlib import asynccontextmanager
from dependencies import init_session
from sqlalchemy.orm import Session
from models import EndPoints, EndPointOIDs, EndPointsData
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, SnmpEngine, UdpTransportTarget,
                                         CommunityData, ContextData, ObjectType,
                                         ObjectIdentity, UsmUserData, usmHMACSHAAuthProtocol,
                                         usmAesCfb128Protocol)

load_dotenv()

# Configuração de logging otimizada
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class HostStatus:
    _id: Optional[int] = None
    ip: str = ""
    is_alive: bool = False
    interval: int = 0
    version: str = ""
    community: str = ""
    port: Optional[int] = None
    user: str = ""
    authKey: str = ""
    privKey: str = ""
    webhook: str = ""
    snmp_data: Dict[str, str] = None
    oids: List[str] = None
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



def print_logs(result):
    status_icon = "🟢" if result.is_alive else "🔴"
    snmp_icon = f"📊 : {result.snmp_data['sysDescr'].split(' ')[0]}" if result.snmp_data and result.snmp_data.get('sysDescr') else "❌"
    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | SNMP: {snmp_icon}")


def get_HostStatus(row: EndPoints, session: Session) -> Optional[HostStatus]:
    oids = {}
    oids_data = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == row.id).first()
    if oids_data:
        oids = {
            "sysDescr": oids_data.sysDescr,
            "sysName": oids_data.sysName,
            "sysUpTime": oids_data.sysUpTime,
            "hrProcessorLoad": oids_data.hrProcessorLoad,
            "memTotalReal": oids_data.memTotalReal,
            "memAvailReal": oids_data.memAvailReal,
            "hrStorageSize": oids_data.hrStorageSize,
            "hrStorageUsed": oids_data.hrStorageUsed
        }
    return HostStatus(
        _id=row.id,
        ip=row.ip,
        is_alive=False,
        interval=row.interval,
        version=row.version,
        community=row.community,
        port=row.port,
        user=row.user,
        authKey=row.authKey,
        privKey=row.privKey,
        webhook=row.webhook,
        oids=oids
    )


def check_ip_for_snmp(host: HostStatus):
    if (host.ip and host.interval and not host.port 
        and not host.version and not host.community
        and not host.user and not host.authKey 
        and not host.privKey):
        return False
    return True 


def select_snmp_authentication(host: HostStatus):
    if host.version in ["1", "2c"]:
        auth_data = CommunityData(host.community, mpModel=0 if host.version == "1" else 1)
    else:
        # Configura credenciais dependendo do caso
        if host.authKey and host.privKey:
            auth_data = UsmUserData(
                userName=host.user,
                authKey=host.authKey,
                privKey=host.privKey,
                authProtocol=usmHMACSHAAuthProtocol,
                privProtocol=usmAesCfb128Protocol,
            )
        elif host.authKey:
            auth_data = UsmUserData(
                userName=host.user,
                authKey=host.authKey,
                authProtocol=usmHMACSHAAuthProtocol,
            )
        else:
            auth_data = UsmUserData(host.user)
    return auth_data


class OptimizedMonitor:
    def __init__(self, session: Session = init_session()):
        self.hosts_status: Dict[str, HostStatus] = {}
        self.lock = asyncio.Lock()
        self.tcp_ports = [int(p) for p in os.getenv("TCP_PORTS", "80,443,22,161").split(",")]

        # criar uma sessão e pegar todos os ips/host e Inicialização dos hosts
        if session:
            data = session.query(EndPoints).all()
            for row in data:
                self.hosts_status[row.ip] = get_HostStatus(row, session)
            session.close()
    
    async def insert_snmp_data_async(self, session_factory, hosts: HostStatus):
        loop = asyncio.get_event_loop()
    
        def sync_insert():
            session = session_factory()
            try:
                data = EndPointsData(
                    id_end_point=hosts._id,
                    status=True,
                    sysDescr=hosts.snmp_data.get("sysDescr"),
                    sysName=hosts.snmp_data.get("sysName"),
                    sysUpTime=hosts.snmp_data.get("sysUpTime"),
                    hrProcessorLoad=hosts.snmp_data.get("hrProcessorLoad"),
                    memTotalReal=hosts.snmp_data.get("memTotalReal"),
                    memAvailReal=hosts.snmp_data.get("memAvailReal"),
                    hrStorageSize=hosts.snmp_data.get("hrStorageSize"),
                    hrStorageUsed=hosts.snmp_data.get("hrStorageUsed"),
                    last_updated=hosts.last_updated
                )
                session.add(data)
                session.commit()
            finally:
                session.close()
        await loop.run_in_executor(None, sync_insert)

    async def check_hosts_db(self):
        # Exemplo: recarrega hosts do banco e atualiza self.hosts_status
        session = init_session()
        try:
            data = session.query(EndPoints).all()
            new_hosts = {row.ip: get_HostStatus(row, session) for row in data}
            # Remove hosts que não existem mais
            for ip in list(self.hosts_status.keys()):
                if ip not in new_hosts:
                    del self.hosts_status[ip]
            # Adiciona novos hosts
            for ip, host in new_hosts.items():
                if ip not in self.hosts_status:
                    self.hosts_status[ip] = host
        finally:
            session.close()

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

    async def fast_snmp_check(self, ip: str):
        """SNMP otimizado com pool de engines - coleta todos os OIDs"""
        async with get_snmp_engine() as engine:
            try:
                auth_data = select_snmp_authentication(self.hosts_status[ip])
                oids_values = self.hosts_status[ip].oids.values() or []
                oids_keys = list(self.hosts_status[ip].oids.keys())
                result = {}

                for idx, oid in enumerate(oids_values):
                    try:
                        error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                            get_cmd(engine, auth_data,
                                await UdpTransportTarget.create((ip, 161), timeout=0.5, retries=0),
                                ContextData(), ObjectType(ObjectIdentity(oid))), timeout=1.0)

                        if not (error_indication or error_status or error_index):
                            result[oids_keys[idx]] = str(var_binds[0][1])
                        else:
                            result[oids_keys[idx]] = None
                    except Exception as e:
                        logger.debug(f"SNMP error for {ip} OID {oid}: {e}")
                        result[oids_keys[idx]] = None
                return result
            except Exception as e:
                logger.debug(f"SNMP error for {ip}: {e}")
                return result
    
    async def check_single_host(self, host_status: HostStatus) -> HostStatus:
        """Verificação completa de um host com fallbacks inteligentes"""
        ip = host_status.ip
        
        # 1. Ping primeiro (mais rápido)
        ping_results = await self.fast_ping_check([ip])
        is_alive, rtt = ping_results.get(ip, (False, 0.0))

        snmp_data = None

        if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            # Se ping OK, tenta SNMP
            snmp_data = await self.fast_snmp_check(ip)
        else:
            # Se ping falhou, tenta TCP como fallback
            tcp_alive = await self.fast_tcp_check(ip)
            if tcp_alive and check_ip_for_snmp(self.hosts_status[ip]):
                is_alive = True
                # Se TCP OK, tenta SNMP também
                snmp_data = await self.fast_snmp_check(ip)
    
        self.hosts_status[ip].is_alive = is_alive
        self.hosts_status[ip].snmp_data = snmp_data
        self.hosts_status[ip].last_updated = datetime.now()
        self.hosts_status[ip].ping_rtt = rtt
        return self.hosts_status[ip]
    
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
                    print_logs(result)
                    yield result
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
            yield result
   
    async def run_monitoring(self, interval: float = 2.0):
        """Loop principal otimizado"""
        logger.info("🚀 Iniciando monitoramento otimizado...")

        session_factory = init_session  # Função que retorna uma nova Session

        while True:
            start_time = asyncio.get_event_loop().time()

            async for result in self.monitoring_cycle():
                if result:
                    interval = int(result.interval) if result else interval
                if result and result.snmp_data:
                    await self.insert_snmp_data_async(session_factory, result)

            # Calcula tempo decorrido e ajusta sleep
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.1, interval - elapsed)

            # Executa a checagem da base de dados em paralelo ao sleep
            check_task = asyncio.create_task(self.check_hosts_db())
            await asyncio.sleep(sleep_time)
            await check_task  # Garante que a checagem terminou antes do próximo ciclo

            logger.info(f"Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.2f}s")


            

# Versão ainda mais otimizada para casos extremos
class HyperFastMonitor(OptimizedMonitor):
    """Versão para quando você precisa de velocidade máxima"""

    async def monitoring_cycle(self):
        await self.hyper_monitoring_cycle()

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
                    last_updated=datetime.now()
                )
                
                status = "🟢" if is_alive else "🔴"
                snmp = "📊" if snmp_desc else "❌"
                print(f"{status} {ip} {snmp}")

# se for possivel pingar, e nao ser possivel pegar os dados via snmp
# em um host que tem SNMP configurado  falha do host ++
# 
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "hypers"
    # se estiver online  e nao cosegui pegar os dados 4 relatar
    # se estiver offline  relatar como offline

    if mode == "hyper":
        print("🏃‍♂️ Modo HYPER-RÁPIDO ativado!")
        monitor = HyperFastMonitor()
        asyncio.run(monitor.run_monitoring(interval=30.0))
    else:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor()
        asyncio.run(monitor.run_monitoring(interval=30.0))
