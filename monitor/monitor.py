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

from alert_email_service import EmailService
from dependencies import init_session
from models import EndPoints, EndPointsData
from snmp_engine_pool import SNMPEnginePool, logger
from utils import (HostStatus, print_logs, get_HostStatus,
                   check_ip_for_snmp, select_snmp_authentication)
from pprint import pprint


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
        
        self.notification_smtp_email = EmailService()

        # NOVO: Configurações de reconexão
        self.max_consecutive_snmp_failures = 5
        self.max_consecutive_ping_failures = 5
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
                # Extrair dados do SNMP
                sysDescr = hosts.snmp_data.get("sysDescr") if hosts.snmp_data else None
                sysName = hosts.snmp_data.get("sysName") if hosts.snmp_data else None
                sysUpTime = hosts.snmp_data.get("sysUpTime") if hosts.snmp_data else None
                hrProcessorLoad = hosts.snmp_data.get("hrProcessorLoad") if hosts.snmp_data else None
                memTotalReal = hosts.snmp_data.get("memTotalReal") if hosts.snmp_data else None
                memAvailReal = hosts.snmp_data.get("memAvailReal") if hosts.snmp_data else None
                hrStorageSize = hosts.snmp_data.get("hrStorageSize") if hosts.snmp_data else None
                hrStorageUsed = hosts.snmp_data.get("hrStorageUsed") if hosts.snmp_data else None
    
                # Buscar os dois últimos registros para este endpoint, ordenados por data (mais recente primeiro)
                last_records = session.query(EndPointsData)\
                    .filter(EndPointsData.id_end_point == hosts._id)\
                    .order_by(EndPointsData.last_updated.desc())\
                    .limit(2)\
                    .all()
    
                # Função para comparar dados relevantes
                def are_data_equal(record, new_data):
                    """Compara se os dados relevantes são iguais"""
                    if not record:
                        return False
                    
                    return (
                        record.id_end_point == new_data["id_end_point"] and
                        record.status == new_data["status"] and
                        record.sysDescr == new_data["sysDescr"] and
                        record.sysName == new_data["sysName"] and
                        record.hrProcessorLoad == new_data["hrProcessorLoad"] and
                        record.memTotalReal == new_data["memTotalReal"] and
                        record.memAvailReal == new_data["memAvailReal"] and
                        record.hrStorageSize == new_data["hrStorageSize"] and
                        record.hrStorageUsed == new_data["hrStorageUsed"]
                    )
    
                # Dados atuais para comparação
                current_data = {
                    "id_end_point": hosts._id,
                    "status": hosts.is_alive,
                    "sysDescr": sysDescr,
                    "sysName": sysName,
                    "hrProcessorLoad": hrProcessorLoad,
                    "memTotalReal": memTotalReal,
                    "memAvailReal": memAvailReal,
                    "hrStorageSize": hrStorageSize,
                    "hrStorageUsed": hrStorageUsed
                }
    
                # Verificar se temos pelo menos um registro anterior
                if len(last_records) >= 1:
                    last_record = last_records[0]  # Mais recente
                    penultimate_record = last_records[1] if len(last_records) >= 2 else None
    
                    # Verificar se o último e penúltimo são iguais aos dados atuais
                    last_equal = are_data_equal(last_record, current_data)
                    penultimate_equal = are_data_equal(penultimate_record, current_data) if penultimate_record else True
    
                    if last_equal and penultimate_equal:
                        # Dados são iguais aos dois últimos registros
                        # Atualizar apenas last_updated e sysUpTime no último registro
                        last_record.last_updated = hosts.last_updated
                        last_record.sysUpTime = sysUpTime
                        
                        session.commit()
                        logger.debug(f"Dados duplicados para endpoint {hosts._id}. Atualizando último registro com timestamp: {hosts.last_updated}")
                        return
                
                # Dados são diferentes ou não temos histórico suficiente
                # Inserir novo registro
                new_data = EndPointsData(
                    id_end_point=hosts._id,
                    status=hosts.is_alive,
                    sysDescr=sysDescr,
                    sysName=sysName,
                    sysUpTime=sysUpTime,
                    hrProcessorLoad=hrProcessorLoad,
                    memTotalReal=memTotalReal,
                    memAvailReal=memAvailReal,
                    hrStorageSize=hrStorageSize,
                    hrStorageUsed=hrStorageUsed,
                    last_updated=hosts.last_updated
                )
                
                session.add(new_data)
                session.commit()
                logger.debug(f"Novo registro inserido para endpoint {hosts._id}")
                
            except Exception as e:
                logger.error(f"Erro ao inserir dados SNMP para endpoint {hosts._id}: {e}")
                session.rollback()
                raise
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
                        # Preserva TODOS os contadores e estadísticas de falha
                        new_hosts[ip].consecutive_snmp_failures = self.hosts_status[ip].consecutive_snmp_failures
                        new_hosts[ip].consecutive_ping_failures = self.hosts_status[ip].consecutive_ping_failures
                        new_hosts[ip].informed = getattr(self.hosts_status[ip], 'informed', False)
                        new_hosts[ip].snmp_informed = getattr(self.hosts_status[ip], 'snmp_informed', False)
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
            force_new = host.consecutive_snmp_failures >= self.max_consecutive_snmp_failures
            
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
        is_alive_ping, rtt = ping_results.get(ip, (False, 0.0))

        snmp_data = None
        is_alive = is_alive_ping  # Valor inicial baseado no ping
        
        if is_alive_ping and check_ip_for_snmp(self.hosts_status[ip]):
            # Tenta SNMP com retry
            snmp_data = await self.fast_snmp_check_with_retry(ip)
        else:
            # Fallback TCP
            tcp_alive = await self.fast_tcp_check(ip)
            if tcp_alive and check_ip_for_snmp(self.hosts_status[ip]):
                is_alive = True
                snmp_data = await self.fast_snmp_check_with_retry(ip)

        # CORREÇÃO: Atualiza contadores de ping baseado APENAS no resultado do ping inicial
        if is_alive_ping:
            self.hosts_status[ip].consecutive_ping_failures = 0
        elif self.hosts_status[ip].consecutive_ping_failures < self.max_consecutive_ping_failures + 1:
            self.hosts_status[ip].consecutive_ping_failures += 1

        # Atualiza contadores de SNMP separadamente
        if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            if snmp_data and any(snmp_data.values()):
                self.hosts_status[ip].consecutive_snmp_failures = 0
            else:
                self.hosts_status[ip].consecutive_snmp_failures += 1
                self.global_failure_count += 1

        self.hosts_status[ip].is_alive = is_alive
        self.hosts_status[ip].snmp_data = snmp_data
        self.hosts_status[ip].last_updated = datetime.now()
        self.hosts_status[ip].ping_rtt = rtt

        # Verifica se precisa renovar engines globalmente
        if self.global_failure_count >= self.engine_refresh_threshold:
            logger.info("Renovando todas as engines SNMP devido a falhas globais...")
            await snmp_pool.refresh_all_engines()
            self.hosts_status[ip].consecutive_snmp_failures = 0
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

    async def notification(self, session_factory, result: HostStatus):
        ping_failures = self.hosts_status[result.ip].consecutive_ping_failures
        snmp_failures = self.hosts_status[result.ip].consecutive_snmp_failures

        # Alerta por falhas de PING (host offline)   session_factory
        if (ping_failures >= self.max_consecutive_ping_failures and not result.is_alive 
            and not getattr(self.hosts_status[result.ip], 'informed', False)):
            self.notification_smtp_email.send_alert_email(
                to_emails=["ndondadaniel2020@gmail.com"],
                subject=f"Host {result.ip} está OFFLINE",
                endpoint_name=result.ip,
                endpoint_ip=result.ip,
                status="DOWN",
                timestamp=datetime.now()
            )
            logger.warning(f"📛📛📛📛📛📛 Host {result.ip} está OFFLINE com {ping_failures} falhas consecutivas de ping.")
            # add na db
            self.hosts_status[result.ip].informed = True

        # Recuperação de PING (host volta a ficar online)   session_factory
        if (ping_failures >= self.max_consecutive_ping_failures and result.is_alive 
            and getattr(self.hosts_status[result.ip], 'informed', False)):
            self.notification_smtp_email.send_alert_email(
            to_emails=["ndondadaniel2020@gmail.com"],
            subject=f"Host {result.ip} está ONLINE",
            endpoint_name=result.ip,
            endpoint_ip=result.ip,
            status="UP",
            timestamp=datetime.now()
            )
            logger.info(f"✅✅✅✅✅✅ Host {result.ip} foi restaurado (PING).")
            # add na db
            self.hosts_status[result.ip].informed = False
            self.hosts_status[result.ip].consecutive_ping_failures = 0

        # Host está online, mas não consegue pegar dados SNMP (e SNMP está configurado)
        if (result.is_alive and snmp_failures > self.max_consecutive_snmp_failures
            and check_ip_for_snmp(self.hosts_status[result.ip])
            and (not result.snmp_data or not any(result.snmp_data.values()))
            and not getattr(self.hosts_status[result.ip], 'snmp_informed', False)
        ):
            self.notification_smtp_email.send_alert_email(
            to_emails=["ndondadaniel2020@gmail.com"],
            subject=f"Host {result.ip} ONLINE mas SNMP FALHOU",
            endpoint_name=result.ip,
            endpoint_ip=result.ip,
            status="SNMP DOWN",
            timestamp=datetime.now()
            )
            logger.warning(f"⚠️⚠️⚠️ Host {result.ip} está ONLINE mas SNMP não respondeu.")
            self.hosts_status[result.ip].snmp_informed = True

        # Se SNMP voltar a responder, limpa flag de alerta SNMP
        if (result.is_alive
            and check_ip_for_snmp(self.hosts_status[result.ip])
            and result.snmp_data and any(result.snmp_data.values())
            and getattr(self.hosts_status[result.ip], 'snmp_informed', False)):
            logger.info(f"✅✅✅ Host {result.ip} SNMP voltou a responder.")
            self.hosts_status[result.ip].snmp_informed = False

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
                    await asyncio.gather(self.notification(session_factory, result),
                        self.insert_snmp_data_async(session_factory, result),
                        return_exceptions=True)

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

    print("⚡ Modo OTIMIZADO ativado!")
    monitor = OptimizedMonitor()
    asyncio.run(monitor.run_monitoring(interval=30.0))
