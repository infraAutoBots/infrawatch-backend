import asyncio
import logging
from tkinter import NO
from typing import Dict, List, Optional, Tuple
from unittest import result
from icmplib import async_multiping
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from dependencies import init_session
from sqlalchemy.orm import Session
from models import EndPoints, EndPointOIDs, EndPointsData
from pprint import pp, pprint
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, SnmpEngine, UdpTransportTarget,
                                         CommunityData, ContextData, ObjectType,
                                         ObjectIdentity, UsmUserData, usmHMACSHAAuthProtocol,
                                         usmAesCfb128Protocol)

load_dotenv()

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
    # NOVO: Contador de falhas consecutivas
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None


# Pool melhorado de engines SNMP com auto-renovação
class SNMPEnginePool:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.engines = asyncio.Queue(maxsize=max_size)
        self.engines_created = 0
        self.lock = asyncio.Lock()
        # Rastreamento de engines problemáticas
        self.faulty_engines = set()
        
    async def get_engine(self, force_new: bool = False):
        """Obtém uma engine do pool ou cria uma nova"""
        async with self.lock:
            if force_new:
                return self._create_new_engine()
                
            try:
                engine = self.engines.get_nowait()
                # Verifica se a engine não está marcada como defeituosa
                if id(engine) in self.faulty_engines:
                    await self._dispose_engine(engine)
                    return await self._get_or_create_engine()
                return engine
            except asyncio.QueueEmpty:
                return await self._get_or_create_engine()
    
    async def _get_or_create_engine(self):
        """Obtém ou cria uma engine"""
        if self.engines_created < self.max_size:
            return self._create_new_engine()
        else:
            # Espera por uma engine disponível
            engine = await self.engines.get()
            if id(engine) in self.faulty_engines:
                await self._dispose_engine(engine)
                return self._create_new_engine()
            return engine
    
    def _create_new_engine(self):
        """Cria uma nova engine"""
        engine = SnmpEngine()
        self.engines_created += 1
        logger.debug(f"Nova SNMP engine criada. Total: {self.engines_created}")
        return engine
    
    async def return_engine(self, engine, is_faulty: bool = False):
        """Retorna uma engine ao pool"""
        async with self.lock:
            if is_faulty:
                self.faulty_engines.add(id(engine))
                await self._dispose_engine(engine)
                logger.debug(f"Engine marcada como defeituosa e descartada")
            else:
                try:
                    self.engines.put_nowait(engine)
                except asyncio.QueueFull:
                    await self._dispose_engine(engine)
    
    async def _dispose_engine(self, engine):
        """Descarta uma engine defeituosa"""
        try:
            if hasattr(engine, 'transport_dispatcher'):
                engine.transport_dispatcher.close_dispatcher()
            self.engines_created -= 1
            self.faulty_engines.discard(id(engine))
        except Exception as e:
            logger.error(f"Erro ao descartar engine: {e}")
    
    async def refresh_all_engines(self):
        """Força a renovação de todas as engines"""
        async with self.lock:
            logger.info("Renovando todas as engines SNMP...")
            # Marca todas as engines como defeituosas
            while not self.engines.empty():
                try:
                    engine = self.engines.get_nowait()
                    await self._dispose_engine(engine)
                except asyncio.QueueEmpty:
                    break
            self.faulty_engines.clear()
            logger.info("Todas as engines SNMP foram renovadas")


# Pool global renovado
snmp_pool = SNMPEnginePool()


@asynccontextmanager
async def get_snmp_engine(force_new: bool = False):
    """Context manager melhorado para engines SNMP"""
    engine = await snmp_pool.get_engine(force_new)
    is_faulty = False
    
    try:
        yield engine
    except Exception as e:
        # Marca como defeituosa se houver erro de conexão/timeout
        if any(error_type in str(e).lower() for error_type in 
               ['timeout', 'connection', 'unreachable', 'refused']):
            is_faulty = True
        raise
    finally:
        await snmp_pool.return_engine(engine, is_faulty)


def print_logs(result):
    status_icon = "🟢" if result.is_alive else "🔴"
    failure_info = f" (Falhas: {result.consecutive_failures})" if result.consecutive_failures > 0 else ""
    snmp_icon = f"📊 : {result.snmp_data['sysDescr'].split(' ')[0]}" if result.snmp_data and result.snmp_data.get('sysDescr') else "❌"
    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | SNMP: {snmp_icon}{failure_info}")


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


class ImprovedOptimizedMonitor:
    def __init__(self, session: Session = init_session()):
        self.hosts_status: Dict[str, HostStatus] = {}
        self.lock = asyncio.Lock()
        self.tcp_ports = [int(p) for p in os.getenv("TCP_PORTS", "80,443,22,161").split(",")]
        # NOVO: Configurações de reconexão
        self.max_consecutive_failures = 5
        self.engine_refresh_threshold = 10  # Renova engines após X falhas globais
        self.global_failure_count = 0

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
        session = init_session()
        try:
            data = session.query(EndPoints).all()
            new_hosts = {row.ip: get_HostStatus(row, session) for row in data}
            
            async with self.lock:
                # Preserva contadores de falha para hosts existentes
                for ip in list(self.hosts_status.keys()):
                    if ip not in new_hosts:
                        del self.hosts_status[ip]
                
                for ip, host in new_hosts.items():
                    if ip in self.hosts_status:
                        # Preserva estatísticas de falha
                        new_hosts[ip].consecutive_failures = self.hosts_status[ip].consecutive_failures
                        new_hosts[ip].last_success = self.hosts_status[ip].last_success
                    self.hosts_status[ip] = new_hosts[ip]
        finally:
            session.close()

    async def fast_ping_check(self, ips: List[str]) -> Dict[str, Tuple[bool, float]]:
        try:
            hosts = await async_multiping(
                ips, 
                count=1,
                timeout=0.5,
                interval=0.02
            )
            return {
                host.address: (host.is_alive, host.avg_rtt or 0.0) 
                for host in hosts
            }
        except Exception as e:
            logger.debug(f"Ping error: {e}")
            return {ip: (False, 0.0) for ip in ips}

    async def fast_tcp_check(self, ip: str) -> bool:
        async def check_port(port):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), 
                    timeout=0.3
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False
        
        tasks = [check_port(port) for port in self.tcp_ports[:2]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(r is True for r in results)

    async def fast_snmp_check_with_retry(self, ip: str, max_retries: int = 3):
        """SNMP check com retry e renovação de engine"""
        host = self.hosts_status[ip]
        
        for attempt in range(max_retries):
            # Força nova engine se muitas falhas consecutivas
            force_new = host.consecutive_failures >= self.max_consecutive_failures
            
            try:
                return await self._perform_snmp_check(ip, force_new)
            except Exception as e:
                logger.debug(f"SNMP tentativa {attempt + 1}/{max_retries} falhou para {ip}: {e}")
                
                # Se é a última tentativa, força nova engine
                if attempt == max_retries - 1:
                    try:
                        return await self._perform_snmp_check(ip, force_new=True)
                    except:
                        pass
                
                await asyncio.sleep(0.1 * (attempt + 1))  # Backoff exponencial
        
        return {}

    async def _perform_snmp_check(self, ip: str, force_new: bool = False):
        """Executa uma verificação SNMP"""
        async with get_snmp_engine(force_new) as engine:
            auth_data = select_snmp_authentication(self.hosts_status[ip])
            oids_values = self.hosts_status[ip].oids.values() or []
            oids_keys = list(self.hosts_status[ip].oids.keys())
            result = {}

            for idx, oid in enumerate(oids_values):
                try:
                    error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                        get_cmd(engine, auth_data,
                            await UdpTransportTarget.create((ip, 161), timeout=1.0, retries=1),
                            ContextData(), ObjectType(ObjectIdentity(oid))), 
                        timeout=2.0
                    )

                    if not (error_indication or error_status or error_index):
                        result[oids_keys[idx]] = str(var_binds[0][1])
                    else:
                        result[oids_keys[idx]] = None
                        
                except asyncio.TimeoutError:
                    logger.debug(f"SNMP timeout para {ip} OID {oid}")
                    result[oids_keys[idx]] = None
                except Exception as e:
                    logger.debug(f"SNMP error para {ip} OID {oid}: {e}")
                    result[oids_keys[idx]] = None
                    raise  # Re-levanta para trigger do retry
            
            return result
    
    async def check_single_host(self, host_status: HostStatus) -> HostStatus:
        """Verificação completa com controle de falhas consecutivas"""
        ip = host_status.ip
        
        # Ping check
        ping_results = await self.fast_ping_check([ip])
        is_alive, rtt = ping_results.get(ip, (False, 0.0))

        snmp_data = None

        if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            # Tenta SNMP com retry
            snmp_data = await self.fast_snmp_check_with_retry(ip)
        else:
            # Fallback TCP
            tcp_alive = await self.fast_tcp_check(ip)
            if tcp_alive and check_ip_for_snmp(self.hosts_status[ip]):
                is_alive = True
                snmp_data = await self.fast_snmp_check_with_retry(ip)
    
        # Atualiza contadores de falha
        if is_alive and snmp_data and any(snmp_data.values()):
            # Sucesso - reseta contador
            self.hosts_status[ip].consecutive_failures = 0
            self.hosts_status[ip].last_success = datetime.now()
        else:
            # Falha - incrementa contador
            self.hosts_status[ip].consecutive_failures += 1
            self.global_failure_count += 1

        self.hosts_status[ip].is_alive = is_alive
        self.hosts_status[ip].snmp_data = snmp_data
        self.hosts_status[ip].last_updated = datetime.now()
        self.hosts_status[ip].ping_rtt = rtt
        
        # Verifica se precisa renovar engines globalmente
        if self.global_failure_count >= self.engine_refresh_threshold:
            logger.warning("Muitas falhas detectadas. Renovando pool de engines SNMP...")
            await snmp_pool.refresh_all_engines()
            self.global_failure_count = 0
        
        return self.hosts_status[ip]
    
    async def monitoring_cycle(self):
        """Ciclo de monitoramento com melhor handling de falhas"""
        ips = list(self.hosts_status.keys())
        if not ips:
            return
        
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
   
    async def run_monitoring(self, interval: float = 30.0):
        """Loop principal com renovação periódica de engines"""
        logger.info("🚀 Iniciando monitoramento otimizado com auto-reconexão...")

        session_factory = init_session
        last_engine_refresh = datetime.now()

        while True:
            start_time = asyncio.get_event_loop().time()

            async for result in self.monitoring_cycle():
                if result:
                    interval = int(result.interval) if result.interval else interval
                if result and result.snmp_data:
                    await self.insert_snmp_data_async(session_factory, result)

            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.1, interval - elapsed)

            # Renovação periódica de engines (a cada 10 minutos)
            if (datetime.now() - last_engine_refresh).seconds > 600:
                logger.info("Renovação periódica das engines SNMP...")
                await snmp_pool.refresh_all_engines()
                last_engine_refresh = datetime.now()

            check_task = asyncio.create_task(self.check_hosts_db())
            await asyncio.sleep(sleep_time)
            await check_task

            logger.info(f"Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.2f}s | Global failures: {self.global_failure_count}")


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "improved"
    
    print("⚡ Modo OTIMIZADO com Auto-Reconexão ativado!")
    monitor = ImprovedOptimizedMonitor()
    asyncio.run(monitor.run_monitoring(interval=30.0))