import asyncio
import logging
from typing import Dict, List, Optional, Tuple
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
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None


class PerHostSNMPEngine:
    """Engine SNMP dedicada por host com auto-renovação"""
    
    def __init__(self, host_ip: str, auth_config: dict):
        self.host_ip = host_ip
        self.auth_config = auth_config
        self.engine = None
        self.created_at = datetime.now()
        self.failure_count = 0
        self.max_failures = 5
        self.max_age_seconds = 600  # 10 minutos
        self.lock = asyncio.Lock()
    
    async def get_engine(self, force_recreate: bool = False):
        """Obtém a engine, recriando se necessário"""
        async with self.lock:
            should_recreate = (
                force_recreate or
                self.engine is None or
                self.failure_count >= self.max_failures or
                (datetime.now() - self.created_at).seconds > self.max_age_seconds
            )
            
            if should_recreate:
                await self._recreate_engine()
            
            return self.engine
    
    async def _recreate_engine(self):
        """Recria a engine SNMP"""
        # Limpa engine anterior se existir
        if self.engine:
            try:
                if hasattr(self.engine, 'transport_dispatcher'):
                    self.engine.transport_dispatcher.close_dispatcher()
            except Exception as e:
                logger.debug(f"Erro ao fechar engine anterior para {self.host_ip}: {e}")
        
        # Cria nova engine
        self.engine = SnmpEngine()
        self.created_at = datetime.now()
        self.failure_count = 0
        logger.debug(f"Nova engine SNMP criada para {self.host_ip}")
    
    def mark_failure(self):
        """Marca uma falha na engine"""
        self.failure_count += 1
        logger.debug(f"Falha #{self.failure_count} na engine para {self.host_ip}")
    
    def mark_success(self):
        """Marca sucesso, resetando contador de falhas"""
        self.failure_count = 0


class SNMPEngineManager:
    """Gerenciador de engines SNMP por host"""
    
    def __init__(self):
        self.engines: Dict[str, PerHostSNMPEngine] = {}
        self.lock = asyncio.Lock()
    
    def _get_auth_config_key(self, host: HostStatus) -> str:
        """Gera chave única baseada na configuração de auth"""
        return f"{host.version}_{host.community}_{host.user}_{host.authKey}_{host.privKey}"
    
    async def get_engine_for_host(self, host: HostStatus, force_recreate: bool = False) -> SnmpEngine:
        """Obtém engine dedicada para o host"""
        engine_key = f"{host.ip}_{self._get_auth_config_key(host)}"
        
        async with self.lock:
            if engine_key not in self.engines:
                auth_config = {
                    'version': host.version,
                    'community': host.community,
                    'user': host.user,
                    'authKey': host.authKey,
                    'privKey': host.privKey
                }
                self.engines[engine_key] = PerHostSNMPEngine(host.ip, auth_config)
        
        engine_wrapper = self.engines[engine_key]
        return await engine_wrapper.get_engine(force_recreate)
    
    async def mark_engine_failure(self, host: HostStatus):
        """Marca falha na engine do host"""
        engine_key = f"{host.ip}_{self._get_auth_config_key(host)}"
        if engine_key in self.engines:
            self.engines[engine_key].mark_failure()
    
    async def mark_engine_success(self, host: HostStatus):
        """Marca sucesso na engine do host"""
        engine_key = f"{host.ip}_{self._get_auth_config_key(host)}"
        if engine_key in self.engines:
            self.engines[engine_key].mark_success()
    
    async def cleanup_old_engines(self):
        """Remove engines antigas ou não utilizadas"""
        async with self.lock:
            to_remove = []
            for key, engine_wrapper in self.engines.items():
                # Remove engines muito antigas ou com muitas falhas
                age_seconds = (datetime.now() - engine_wrapper.created_at).seconds
                if (age_seconds > 1800 or  # 30 minutos
                    engine_wrapper.failure_count > engine_wrapper.max_failures * 2):
                    to_remove.append(key)
            
            for key in to_remove:
                engine_wrapper = self.engines[key]
                if engine_wrapper.engine:
                    try:
                        if hasattr(engine_wrapper.engine, 'transport_dispatcher'):
                            engine_wrapper.engine.transport_dispatcher.close_dispatcher()
                    except:
                        pass
                del self.engines[key]
                logger.debug(f"Engine removida: {key}")
    
    async def recreate_all_engines(self):
        """Força recriação de todas as engines"""
        logger.info("Recriando todas as engines SNMP...")
        async with self.lock:
            for engine_wrapper in self.engines.values():
                await engine_wrapper._recreate_engine()
        logger.info("Todas as engines foram recriadas")


# Manager global
snmp_engine_manager = SNMPEngineManager()


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
    return bool(host.ip and host.version and 
                (host.community or host.user))


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


def print_logs(result):
    status_icon = "🟢" if result.is_alive else "🔴"
    failure_info = f" (Falhas: {result.consecutive_failures})" if result.consecutive_failures > 0 else ""
    snmp_icon = f"📊 : {result.snmp_data['sysDescr'].split(' ')[0]}" if result.snmp_data and result.snmp_data.get('sysDescr') else "❌"
    print(f"{status_icon} {result.ip} | RTT: {result.ping_rtt:.1f}ms | SNMP: {snmp_icon}{failure_info}")


class PerHostOptimizedMonitor:
    def __init__(self, session: Session = init_session()):
        self.hosts_status: Dict[str, HostStatus] = {}
        self.lock = asyncio.Lock()
        self.tcp_ports = [int(p) for p in os.getenv("TCP_PORTS", "80,443,22,161").split(",")]
        self.max_consecutive_failures = 3

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
                for ip in list(self.hosts_status.keys()):
                    if ip not in new_hosts:
                        del self.hosts_status[ip]
                
                for ip, host in new_hosts.items():
                    if ip in self.hosts_status:
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

    async def snmp_check_with_dedicated_engine(self, host: HostStatus, max_retries: int = 3):
        """SNMP check usando engine dedicada por host"""
        
        for attempt in range(max_retries):
            # Força recreação da engine se muitas falhas
            force_recreate = host.consecutive_failures >= self.max_consecutive_failures
            
            try:
                # Obtém engine dedicada para este host
                engine = await snmp_engine_manager.get_engine_for_host(host, force_recreate)
                auth_data = select_snmp_authentication(host)
                
                oids_values = list(host.oids.values()) if host.oids else []
                oids_keys = list(host.oids.keys()) if host.oids else []
                result = {}

                for idx, oid in enumerate(oids_values):
                    try:
                        error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                            get_cmd(engine, auth_data,
                                await UdpTransportTarget.create((host.ip, 161), timeout=1.0, retries=1),
                                ContextData(), ObjectType(ObjectIdentity(oid))), 
                            timeout=2.0
                        )

                        if not (error_indication or error_status or error_index):
                            result[oids_keys[idx]] = str(var_binds[0][1])
                        else:
                            result[oids_keys[idx]] = None

                    except Exception as oid_error:
                        logger.debug(f"SNMP OID error for {host.ip} OID {oid}: {oid_error}")
                        result[oids_keys[idx]] = None

                # Marca sucesso na engine se obteve algum resultado
                if any(result.values()):
                    await snmp_engine_manager.mark_engine_success(host)
                    return result
                else:
                    raise Exception("Nenhum OID retornou dados válidos")

            except Exception as e:
                logger.debug(f"SNMP tentativa {attempt + 1}/{max_retries} falhou para {host.ip}: {e}")
                await snmp_engine_manager.mark_engine_failure(host)
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.2 * (attempt + 1))  # Backoff
                
        return {}

    async def check_single_host(self, host_status: HostStatus) -> HostStatus:
        """Verificação completa com engine dedicada por host"""
        ip = host_status.ip
        
        # Ping check
        ping_results = await self.fast_ping_check([ip])
        is_alive, rtt = ping_results.get(ip, (False, 0.0))

        snmp_data = None

        if is_alive and check_ip_for_snmp(host_status):
            # SNMP com engine dedicada
            snmp_data = await self.snmp_check_with_dedicated_engine(host_status)
        else:
            # Fallback TCP
            tcp_alive = await self.fast_tcp_check(ip)
            if tcp_alive and check_ip_for_snmp(host_status):
                is_alive = True
                snmp_data = await self.snmp_check_with_dedicated_engine(host_status)
    
        # Atualiza contadores
        if is_alive and snmp_data and any(v for v in snmp_data.values() if v):
            host_status.consecutive_failures = 0
            host_status.last_success = datetime.now()
        else:
            host_status.consecutive_failures += 1

        host_status.is_alive = is_alive
        host_status.snmp_data = snmp_data
        host_status.last_updated = datetime.now()
        host_status.ping_rtt = rtt
        
        return host_status
    
    async def monitoring_cycle(self):
        """Ciclo de monitoramento com engines dedicadas"""
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
                    self.hosts_status[result.ip] = result
                    yield result
        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
   
    async def run_monitoring(self, interval: float = 30.0):
        """Loop principal com limpeza periódica de engines"""
        logger.info("🚀 Iniciando monitoramento com engines dedicadas por host...")

        session_factory = init_session
        last_cleanup = datetime.now()

        while True:
            start_time = asyncio.get_event_loop().time()

            async for result in self.monitoring_cycle():
                if result:
                    interval = int(result.interval) if result.interval else interval
                if result and result.snmp_data:
                    await self.insert_snmp_data_async(session_factory, result)

            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.1, interval - elapsed)

            # Limpeza periódica de engines antigas (a cada 5 minutos)
            if (datetime.now() - last_cleanup).seconds > 300:
                logger.info("Limpeza periódica de engines antigas...")
                await snmp_engine_manager.cleanup_old_engines()
                last_cleanup = datetime.now()

            check_task = asyncio.create_task(self.check_hosts_db())
            await asyncio.sleep(sleep_time)
            await check_task

            logger.info(f"Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.2f}s")


if __name__ == "__main__":
    print("⚡ Modo com Engines Dedicadas por Host ativado!")
    monitor = PerHostOptimizedMonitor()
    asyncio.run(monitor.run_monitoring(interval=30.0))