import os
import asyncio

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from icmplib import async_multiping
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Tuple
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, UdpTransportTarget,
                                         ContextData, ObjectType, ObjectIdentity)

from dependencies import init_session
from models import EndPoints, EndPointsData
from snmp_engine_pool import SNMPEnginePool, logger
from utils import (HostStatus, print_logs, get_HostStatus,
                   check_ip_for_snmp, select_snmp_authentication)



load_dotenv()


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



class OptimizedMonitor:
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

    async def has_recent_snmp_data(self, ip: str, days: int = 7) -> bool:
        """
        Verifica se houve coleta de dados SNMP nas últimas X dias.
        Não interrompe o fluxo de execução em caso de erro.
        """
        try:
            session = init_session()
            try:
                # Busca o endpoint
                endpoint = session.query(EndPoints).filter(EndPoints.ip == ip).first()
                if not endpoint:
                    return False
                
                # Calcula data limite (X dias atrás)
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # Verifica se existe algum dado coletado recentemente
                recent_data = session.query(EndPointsData).filter(
                    EndPointsData.id_end_point == endpoint.id,
                    EndPointsData.last_updated >= cutoff_date,
                    # Verifica se pelo menos um campo SNMP não está vazio/None
                    (EndPointsData.sysDescr.isnot(None) |
                     EndPointsData.sysName.isnot(None) |
                     EndPointsData.sysUpTime.isnot(None) |
                     EndPointsData.hrProcessorLoad.isnot(None))
                ).first()
                
                return recent_data is not None
                
            finally:
                session.close()
                
        except Exception as e:
            # Log o erro mas não interrompe o fluxo
            logger.debug(f"Erro ao verificar dados recentes para {ip}: {e}")
            return False

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
        elif is_alive and not snmp_data and check_ip_for_snmp(self.hosts_status[ip]):
            # Falha - incrementa contador
            # o host tem que ter SNMP configurado
            # Verifica se houve coleta de dados recente antes de incrementar falha
            # has_recent_data = await self.has_recent_snmp_data(ip, days=7)
            # if has_recent_data:
                # Se é possível pingar, não consegue pegar dados via SNMP
                # em um host que tem SNMP configurado E já coletou dados recentemente
                # = falha do host ++
                self.hosts_status[ip].consecutive_failures += 1
                self.global_failure_count += 1

        self.hosts_status[ip].is_alive = is_alive
        self.hosts_status[ip].snmp_data = snmp_data
        self.hosts_status[ip].last_updated = datetime.now()
        self.hosts_status[ip].ping_rtt = rtt

        # Verifica se precisa renovar engines globalmente
        if self.global_failure_count >= self.engine_refresh_threshold:
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
