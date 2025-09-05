import os
import asyncio
import re

import aiohttp
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from icmplib import async_multiping
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Tuple
from pysnmp.hlapi.v3arch.asyncio import (get_cmd, UdpTransportTarget, next_cmd,
                                         ContextData, ObjectType, ObjectIdentity)

from utils import (HostStatus, print_logs, get_HostStatus,
                   check_ip_for_snmp, select_snmp_authentication)
from alert_email_service import EmailService
from alert_webhook_service import WebhookService
from dependencies import init_session
from models import EndPoints, EndPointsData, Alerts, AlertLogs, FailureThresholdConfig
from snmp_engine_pool import SNMPEnginePool, logger
from pprint import pprint


load_dotenv()


# Pool global renovado
snmp_pool = SNMPEnginePool()


# Adicionar na classe OptimizedMonitor
# Constantes de configuração
NOTIFICATION_CONFIG = {
    "default_email": ["ndondadaniel2020@gmail.com"],
    "default_user_id": 0,
}


# Definições para eventos comuns
ALERT_TYPES = {
    "ping_down": {
        "title": "Host {ip} está OFFLINE",
        "description": "Falhas consecutivas de ping: {failures}",
        "severity": "high",
        "category": "network",
        "system": "monitoring",
        "impact": "host unreachable",
        "status": "DOWN",
    },
    "ping_up": {
        "title": "Host {ip} foi restaurado (PING)",
        "description": "Ping de recuperação: {failures}",
        "severity": "low",
        "category": "network",
        "system": "monitoring",
        "impact": "host reachable",
        "status": "UP",
    },
    "snmp_down": {
        "title": "Host {ip} ONLINE mas SNMP FALHOU",
        "description": "Falhas consecutivas de SNMP: {failures}",
        "severity": "medium",
        "category": "network",
        "system": "monitoring",
        "impact": "host SNMP unreachable",
        "status": "SNMP DOWN",
    },
    "snmp_up": {
        "title": "Host {ip} SNMP voltou a responder",
        "description": "SNMP de recuperação: {failures}",
        "severity": "low",
        "category": "network",
        "system": "monitoring",
        "impact": "host SNMP reachable",
        "status": "SNMP UP",
    }
}


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


def create_alert(title: str, description: str, severity: str,
                 category: str, system: str, impact: str,
                 id_endpoint: int, id_user_created: int,
                 assignee: str, session: Session):
    """
    Cria um novo alerta no sistema.
    """

    new_alert = Alerts(
        title=title,
        description=description,
        severity=severity,
        category=category,
        system=system,
        impact=impact,
        id_endpoint=id_endpoint,
        id_user_created=id_user_created,
        assignee=assignee
    )

    session.add(new_alert)
    session.commit()
    session.refresh(new_alert)

    # Log da criação
    log_entry = AlertLogs(
        id_alert=new_alert.id,
        id_user=0,
        action="created",
        comment=f"Alerta criado: {title}"
    )
    session.add(log_entry)
    session.commit()



class OptimizedMonitor:
    def __init__(self, logger = False, session: Session = init_session()):
        self.hosts_status: Dict[str, HostStatus] = {}
        self.lock = asyncio.Lock()
        self.tcp_ports = [int(p) for p in os.getenv("TCP_PORTS", "80, 443, 22, 21, 25, 53, 110, 143, 3306, 5432, 6379, 27017, 8080, 8443, 3389, 5900, 161, 389, 1521, 9200").split(",")]
        
        self.alert_email = EmailService()
        self.alert_webhook = WebhookService()

        # NOVO: Configurações de reconexão
        failure_threshold = session.query(FailureThresholdConfig).first()
        self.max_consecutive_snmp_failures = failure_threshold.consecutive_snmp_failures if failure_threshold else 10
        self.max_consecutive_ping_failures = failure_threshold.consecutive_ping_failures if failure_threshold else 5
        self.engine_refresh_threshold = self.max_consecutive_snmp_failures
        self.global_failure_count = 0
        self.logger = logger

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
                        if self.logger:
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
                if self.logger:
                    logger.debug(f"Novo registro inserido para endpoint {hosts._id}")
                
            except Exception as e:
                if self.logger:
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
            if self.logger:
                logger.debug(f"Ping error: {e}")
            return {ip: (False, 0.0) for ip in ips}

    async def fast_tcp_check(self, endpoint: str):
        async def check_port_first(port):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(endpoint, port), 1)
                writer.close()
                await writer.wait_closed()
                return True
            except Exception:
                return False

        # Teste HTTP/HTTPS real (sequencial, retorna no primeiro sucesso)
        paths = ["/"]
        for path in paths:
            for url in [f"http://{endpoint}{path}", f"https://{endpoint}{path}"]:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=1, allow_redirects=True) as resp:
                            if resp.status < 500:
                                return True
                except Exception:
                    continue

        tasks = [asyncio.create_task(check_port_first(port)) for port in self.tcp_ports]
        results = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
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
                if self.logger:
                    logger.debug(f"SNMP tentativa {attempt + 1}/{max_retries} falhou para {ip}: {e}")
                
                # Se é a última tentativa, força nova engine
                if attempt == max_retries - 1:
                    try:
                        return await self._perform_snmp_check(ip, force_new=True)
                    except:
                        pass
                
                await asyncio.sleep(0.1 * (attempt + 1))  # Backoff exponencial
        
        return {}

    def _is_table_oid(self, oid: str) -> bool:
        """Verifica se o OID é de uma tabela baseado em padrões conhecidos"""
        table_patterns = [
            "1.3.6.1.2.1.25.2.3.1",  # hrStorageTable
            "1.3.6.1.2.1.25.3.3.1",  # hrProcessorTable
            "1.3.6.1.2.1.2.2.1",     # ifTable
            "1.3.6.1.2.1.4.20.1",    # ipAddrTable
        ]
        return any(oid.startswith(pattern) for pattern in table_patterns)

    async def _get_values_from_snmp_tables(self, engine, auth_data, ip: str, port: int, base_oid: str):
        """Obtém todos os valores de uma tabela SNMP usando next_cmd (SNMP walk)"""
        
        values = []
        try:
            # Criar o transport target primeiro
            transport_target = await UdpTransportTarget.create((ip, port), timeout=2.0, retries=1)
            
            # Usar next_cmd para fazer SNMP walk (equivalente ao snmpwalk)
            from pysnmp.hlapi.v3arch.asyncio import next_cmd
            
            # Começar do OID base
            current_oid = ObjectIdentity(base_oid)
            
            while True:
                try:
                    error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                        next_cmd(
                            engine, 
                            auth_data,
                            transport_target,
                            ContextData(),
                            ObjectType(current_oid),
                            lexicographicMode=False
                        ), 
                        timeout=3.0
                    )
                    
                    if error_indication:
                        if self.logger:
                            logger.debug(f"SNMP walk error indication: {error_indication}")
                        break
                    elif error_status:
                        if self.logger:
                            logger.debug(f"SNMP walk error status: {error_status}")
                        break
                    else:
                        # Verificar se ainda estamos na mesma tabela
                        oid_str = str(var_binds[0][0])
                        value = str(var_binds[0][1])
                        
                        if not oid_str.startswith(base_oid):
                            break  # Saímos da tabela
                        values.append({oid_str[len(base_oid):].lstrip('.'): value
                        })

                        # Próximo OID para continuar o walk
                        current_oid = var_binds[0][0]
                        
                        # Limite de segurança para evitar loops infinitos
                        if len(values) >= 100:
                            if self.logger:
                                logger.debug(f"Limite de 100 entradas atingido para tabela {base_oid}")
                            break
                            
                except asyncio.TimeoutError:
                    if self.logger:
                        logger.debug(f"Timeout durante walk da tabela {base_oid}")
                    break
                except Exception as e:
                    if self.logger:
                        logger.debug(f"Erro durante walk da tabela {base_oid}: {e}")
                    break

            return str(values) if values else None

        except Exception as e:
            if self.logger:
                logger.debug(f"Error getting table values for {base_oid}: {e}")
            return None

    async def _perform_snmp_check(self, ip: str, force_new: bool = False):
        """Executa uma verificação SNMP"""
        async with get_snmp_engine(force_new) as engine:
            auth_data = select_snmp_authentication(self.hosts_status[ip])
            oids_values = self.hosts_status[ip].oids.values() or []
            oids_keys = list(self.hosts_status[ip].oids.keys())
            port = self.hosts_status[ip].port or 161
            result = {}

            for idx, oid in enumerate(oids_values):
                try:
                    # Verificar se é uma tabela
                    if self._is_table_oid(oid):
                        # Usar next_cmd para tabelas (SNMP walk)
                        values = await self._get_values_from_snmp_tables(engine, auth_data, ip, port, oid)
                        result[oids_keys[idx]] = values
                        if self.logger:
                            logger.debug(f"OID de tabela {oid} retornou {len(values)} entradas para {ip}")
                    else:
                        # Usar get_cmd para valores únicos
                        error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                            get_cmd(engine, auth_data,
                                await UdpTransportTarget.create((ip, port), timeout=1.0, retries=1),
                                ContextData(), ObjectType(ObjectIdentity(oid))), 
                            timeout=2.0
                        )

                        if not (error_indication or error_status or error_index):
                            result[oids_keys[idx]] = str(var_binds[0][1])
                        else:
                            result[oids_keys[idx]] = None
                            
                except asyncio.TimeoutError:
                    if self.logger:
                        logger.debug(f"SNMP timeout para {ip} OID {oid}")
                    result[oids_keys[idx]] = None
                except Exception as e:
                    if self.logger:
                        logger.debug(f"SNMP error para {ip} OID {oid}: {e}")
                    result[oids_keys[idx]] = None
                    raise
            
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
            if self.logger:
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
                        if self.logger:
                            logger.error(f"Error checking {ips[i]}: {result}")
                        continue
                    if self.logger:
                        print_logs(result)
                    yield result
        except Exception as e:
            if self.logger:
                logger.error(f"Monitoring cycle error: {e}")

    async def send_alert(self, session_factory, result: HostStatus):
        """Processa notificações baseadas no estado atual do host"""
        host_data = self.hosts_status[result.ip]
        ping_failures = host_data.consecutive_ping_failures
        snmp_failures = host_data.consecutive_snmp_failures
        
        # 1. Verificar ping down (host offline)
        if (ping_failures >= self.max_consecutive_ping_failures and 
            not result.is_alive and 
            not getattr(host_data, 'informed', False)):
            await self._process_alert(session_factory, "ping_down", result, ping_failures)
            host_data.informed = True
    
        # 2. Verificar ping up (host voltou a ficar online)
        elif (ping_failures >= self.max_consecutive_ping_failures and 
              result.is_alive and 
              getattr(host_data, 'informed', False)):
            await self._process_alert(session_factory, "ping_up", result, ping_failures)
            host_data.informed = False
            host_data.consecutive_ping_failures = 0
    
        # 3. Verificar snmp down (host online, mas snmp não responde)
        if (result.is_alive and 
            snmp_failures > self.max_consecutive_snmp_failures and
            check_ip_for_snmp(host_data) and
            (not result.snmp_data or not any(result.snmp_data.values())) and
            not getattr(host_data, 'snmp_informed', False)):
            await self._process_alert(session_factory, "snmp_down", result, snmp_failures)
            host_data.consecutive_snmp_failures = 0
            host_data.snmp_informed = True
    
        # 4. Verificar snmp up (snmp voltou a responder)
        elif (result.is_alive and
              check_ip_for_snmp(host_data) and
              result.snmp_data and any(result.snmp_data.values()) and
              getattr(host_data, 'snmp_informed', False)):
            await self._process_alert(session_factory, "snmp_up", result, snmp_failures)
            host_data.consecutive_snmp_failures = 0
            host_data.snmp_informed = False

    async def _process_alert(self, session_factory, alert_type, result, failures):
        """Processa um alerta específico, enviando email e criando registro no banco"""
        ip = result.ip
        alert_config = ALERT_TYPES[alert_type]

        # Formatar mensagens com os dados atuais
        title = alert_config["title"].format(ip=ip)
        description = alert_config["description"].format(failures=failures)
    
        # Enviar email de notificação
        name = result.nickname if result.nickname else ip
        if check_ip_for_snmp(result) and result.snmp_data:
            name = result.snmp_data.get('sysName')
            if not name and result.snmp_data.get('sysDescr'):
                name = result.snmp_data['sysDescr'].split(' ')[0]
            else:
                name = result.nickname if result.nickname else ip

        try:
            self.alert_email.send_alert_email(
                to_emails=NOTIFICATION_CONFIG["default_email"],
                subject=title,
                endpoint_name=name,
                endpoint_ip=ip,
                status=alert_config["status"],
                timestamp=datetime.now()
            )
        except Exception as e:
            if self.logger:
                logger.error(f"Error sending alert email for {ip}: {e}")

        try:
            self.alert_webhook.send_alert_webhook(
                endpoint_name=name,
                endpoint_ip=ip,
                status=alert_config["status"],
                timestamp=datetime.now()
            )
        except Exception as e:
            if self.logger:
                logger.error(f"Error sending alert webhook for {ip}: {e}")

        # Criar alerta no banco de dados
        session = None
        try:
            session = session_factory()
            create_alert(
                title=title,
                description=description,
                severity=alert_config["severity"],
                category=alert_config["category"],
                system=alert_config["system"],
                impact=alert_config["impact"],
                id_endpoint=result._id,
                id_user_created=0,
                assignee=NOTIFICATION_CONFIG["default_email"][0],
                session=session
            )
        except Exception as e:
            if self.logger:
                logger.error(f"Error creating alert for {ip}: {e}")
        finally:
            if session:
                session.close()
        
        # Log apropriado para o tipo de evento
        log_message = f"{'✅' if 'up' in alert_type else '⚠️'} Host {ip} {alert_config['status']}"
        if 'up' in alert_type:
            if self.logger:
                logger.info(log_message)
        else:
            if self.logger:
                logger.warning(log_message)
            
    async def run_monitoring(self, interval: float = 30.0):
        """Loop principal com renovação periódica de engines"""
        if self.logger:
            logger.info("🚀 Iniciando monitoramento otimizado com auto-reconexão...")

        session_factory = init_session
        last_engine_refresh = datetime.now()

        while True:
            start_time = asyncio.get_event_loop().time()
            async for result in self.monitoring_cycle():
                if result:
                    interval = int(result.interval) if result.interval else interval
                    await asyncio.gather(self.send_alert(session_factory, result),
                        self.insert_snmp_data_async(session_factory, result),
                        return_exceptions=True)

            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.1, interval - elapsed)

            # Renovação periódica de engines (a cada 10 minutos)
            if (datetime.now() - last_engine_refresh).seconds > 600:
                if self.logger:
                    logger.info("Renovação periódica das engines SNMP...")
                await snmp_pool.refresh_all_engines()
                last_engine_refresh = datetime.now()

            check_task = asyncio.create_task(self.check_hosts_db())
            await asyncio.sleep(sleep_time)
            await check_task

            if self.logger:
                logger.info(f"Cycle completed in {elapsed:.2f}s, sleeping {sleep_time:.2f}s | Global failures: {self.global_failure_count}")

  


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor(logger=True)
        asyncio.run(monitor.run_monitoring(interval=30.0))
    else:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor()
        asyncio.run(monitor.run_monitoring(interval=30.0))

