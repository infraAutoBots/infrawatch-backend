import os
import sys
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

from utils_monitor import (HostStatus, print_logs, get_HostStatus,
                   check_ip_for_snmp, select_snmp_authentication, is_snmp_data_valid)
from alert_email_service import EmailService
from alert_webhook_service import WebhookService
from dependencies import init_session_monitor

# Configurações padrão
DEFAULT_SYSTEM_USER_ID = 8  # ID do usuário admin para alertas do sistema
from snmp_engine_pool import SNMPEnginePool, logger
from performance_alerts import (should_alert_cpu, should_alert_memory, 
                               should_alert_storage, should_alert_network,
                               initialize_default_thresholds)

from models import EndPoints, EndPointsData, Alerts, AlertLogs, FailureThresholdConfig, SLAMetrics, IncidentTracking, PerformanceMetrics

import asyncio
import os
import sys
import time
from pprint import pprint


load_dotenv()


# Pool global renovado
snmp_pool = SNMPEnginePool()


# Adicionar na classe OptimizedMonitor
# Constantes de configuração


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


class SLADataCollector:
    """
    Coletor de dados para métricas de SLA.
    Calcula disponibilidade, MTTR, MTBF e compliance de SLA.
    """
    
    def __init__(self):
        self.sla_buffer = {}
        self.incident_tracking = {}
        
    def calculate_percentile(self, data_list: List[float], percentile: float) -> float:
        """Calcula percentil manualmente sem numpy"""
        if not data_list:
            return 0.0
        
        sorted_data = sorted(data_list)
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            if upper_index >= len(sorted_data):
                return sorted_data[lower_index]
            
            # Interpolação linear
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    async def collect_sla_metrics(self, host_result: HostStatus, session_factory):
        """Coleta métricas específicas para SLA"""
        ip = host_result.ip
        endpoint_id = host_result._id
        
        # Inicializar buffer se necessário
        if ip not in self.sla_buffer:
            self.sla_buffer[ip] = {
                'last_state': host_result.is_alive,
                'last_change': datetime.now(),
                'uptime_seconds': 0,
                'downtime_seconds': 0,
                'response_times': [],
                'incidents': [],
                'last_sla_save': datetime.now()
            }
        
        buffer = self.sla_buffer[ip]
        now = datetime.now()
        time_diff = (now - buffer['last_change']).total_seconds()
        
        # Acumular tempo baseado no estado anterior
        if buffer['last_state']:
            buffer['uptime_seconds'] += time_diff
        else:
            buffer['downtime_seconds'] += time_diff
            
        # Coletar tempo de resposta
        if host_result.ping_rtt > 0:
            buffer['response_times'].append(host_result.ping_rtt)
            # Manter apenas os últimos 1000 tempos de resposta
            if len(buffer['response_times']) > 1000:
                buffer['response_times'] = buffer['response_times'][-1000:]
        
        # Verificar mudança de estado para tracking de incidentes
        if buffer['last_state'] != host_result.is_alive:
            if not host_result.is_alive:
                # Início de incidente
                await self._create_incident(endpoint_id, host_result, session_factory)
            else:
                # Fim de incidente
                await self._resolve_incident(endpoint_id, host_result, session_factory)
                
        buffer['last_state'] = host_result.is_alive
        buffer['last_change'] = now
        
        # Salvar métricas SLA a cada hora
        if (now - buffer['last_sla_save']).seconds >= 3600:  # 1 hora
            await self._save_sla_metrics(endpoint_id, buffer, session_factory)
            buffer['last_sla_save'] = now
        
        return buffer
    
    async def _create_incident(self, endpoint_id: int, host_result: HostStatus, session_factory):
        """Cria um novo incidente no banco"""
        session = session_factory()
        try:
            incident_type = "ping_down" if not host_result.is_alive else "snmp_down"
            impact_desc = f"Host {host_result.ip} está inacessível via {'ping' if not host_result.is_alive else 'SNMP'}"
            
            incident = IncidentTracking(
                endpoint_id=endpoint_id,
                incident_type=incident_type,
                severity="high" if not host_result.is_alive else "medium",
                impact_description=impact_desc
            )
            
            session.add(incident)
            session.commit()
            
            # Guardar referência do incidente
            self.incident_tracking[host_result.ip] = incident.id
            
        except Exception as e:
            print(f"Erro ao criar incidente: {e}")
            session.rollback()
        finally:
            session.close()
    
    async def _resolve_incident(self, endpoint_id: int, host_result: HostStatus, session_factory):
        """Resolve incidente ativo"""
        if host_result.ip not in self.incident_tracking:
            return
            
        session = session_factory()
        try:
            incident_id = self.incident_tracking[host_result.ip]
            incident = session.query(IncidentTracking).filter(
                IncidentTracking.id == incident_id,
                IncidentTracking.status == "open"
            ).first()
            
            if incident:
                incident.close_incident(
                    resolution_notes=f"Host {host_result.ip} voltou a responder"
                )
                session.commit()
            
            # Remove da tracking
            del self.incident_tracking[host_result.ip]
            
        except Exception as e:
            print(f"Erro ao resolver incidente: {e}")
            session.rollback()
        finally:
            session.close()
    
    async def _save_sla_metrics(self, endpoint_id: int, buffer: dict, session_factory):
        """Salva métricas de SLA agregadas no banco"""
        session = session_factory()
        try:
            total_seconds = buffer['uptime_seconds'] + buffer['downtime_seconds']
            availability = 0.0
            
            if total_seconds > 0:
                availability = (buffer['uptime_seconds'] / total_seconds) * 100
            
            # Calcular métricas de performance
            response_times = buffer['response_times']
            avg_response = sum(response_times) / len(response_times) if response_times else 0
            max_response = max(response_times) if response_times else 0
            min_response = min(response_times) if response_times else 0
            
            # Calcular MTTR baseado em incidentes resolvidos das últimas 24h
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            recent_incidents = session.query(IncidentTracking).filter(
                IncidentTracking.endpoint_id == endpoint_id,
                IncidentTracking.start_time >= twenty_four_hours_ago,
                IncidentTracking.status == "resolved"
            ).all()
            
            mttr_minutes = None
            incidents_count = len(recent_incidents)
            
            if recent_incidents:
                total_resolution_time = sum(
                    incident.resolution_time_minutes or 0 
                    for incident in recent_incidents
                )
                mttr_minutes = total_resolution_time / len(recent_incidents)
            
            # Criar registro de SLA
            sla_metric = SLAMetrics(
                endpoint_id=endpoint_id,
                availability_percentage=availability,
                uptime_seconds=buffer['uptime_seconds'],
                downtime_seconds=buffer['downtime_seconds'],
                mttr_minutes=mttr_minutes,
                incidents_count=incidents_count,
                avg_response_time=avg_response,
                max_response_time=max_response,
                min_response_time=min_response,
                sla_target=99.9
            )
            
            session.add(sla_metric)
            
            # Calcular e salvar métricas de performance detalhadas
            if response_times:
                perf_metric = PerformanceMetrics(
                    endpoint_id=endpoint_id,
                    response_time_p50=self.calculate_percentile(response_times, 50),
                    response_time_p90=self.calculate_percentile(response_times, 90),
                    response_time_p95=self.calculate_percentile(response_times, 95),
                    response_time_p99=self.calculate_percentile(response_times, 99),
                    response_time_p99_9=self.calculate_percentile(response_times, 99.9),
                    response_time_avg=avg_response,
                    response_time_max=max_response,
                    response_time_min=min_response,
                    total_requests=len(response_times),
                    sample_count=len(response_times)
                )
                session.add(perf_metric)
            
            session.commit()
            
            # Reset dos contadores
            buffer['uptime_seconds'] = 0
            buffer['downtime_seconds'] = 0
            buffer['response_times'] = []
            
        except Exception as e:
            print(f"Erro ao salvar métricas SLA: {e}")
            session.rollback()
        finally:
            session.close()


class OptimizedMonitor:
    def __init__(self, logger = False, session: Session = init_session_monitor()):
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
        
        # Performance alerts tracking
        self._last_performance_alerts = {}
        
        # SLA Data Collector
        self.sla_collector = SLADataCollector()
        
        # Inicializar thresholds padrão
        initialize_default_thresholds(session)

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
                hrStorageDescr = hosts.snmp_data.get("hrStorageDescr") if hosts.snmp_data else None
                ifOperStatus = hosts.snmp_data.get("ifOperStatus") if hosts.snmp_data else None
                ifInOctets = hosts.snmp_data.get("ifInOctets") if hosts.snmp_data else None
                ifOutOctets = hosts.snmp_data.get("ifOutOctets") if hosts.snmp_data else None
    
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
                        record.hrStorageUsed == new_data["hrStorageUsed"] and
                        record.hrStorageDescr == new_data["hrStorageDescr"] and
                        record.ifOperStatus == new_data["ifOperStatus"] and
                        record.ifInOctets == new_data["ifInOctets"] and
                        record.ifOutOctets == new_data["ifOutOctets"]
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
                    "hrStorageUsed": hrStorageUsed,
                    "hrStorageDescr": hrStorageDescr,
                    "ifOperStatus": ifOperStatus,
                    "ifInOctets": ifInOctets,
                    "ifOutOctets": ifOutOctets
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
                    hrStorageDescr=hrStorageDescr,
                    ifOperStatus=ifOperStatus,
                    ifInOctets=ifInOctets,
                    ifOutOctets=ifOutOctets,
                    ping_rtt=str(hosts.ping_rtt),
                    snmp_rtt=str(hosts.snmp_rtt),
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
        session = init_session_monitor()
        try:
            data = session.query(EndPoints).filter(EndPoints.active == True).all()
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
        """
        Verificação TCP ultra-rápida e robusta. 
        Otimizada para velocidade com timeouts agressivos e verificação paralela.
        """
        if self.logger:
            logger.debug(f"Fast TCP check iniciado para {endpoint}")
        
        # Fase 1: Verificação paralela rápida (HTTP + Portas principais)
        http_task = asyncio.create_task(self._quick_http_check(endpoint))
        tcp_task = asyncio.create_task(self._quick_tcp_check(endpoint))
        
        try:
            # Aguarda a primeira resposta positiva ou ambas falharem
            done, pending = await asyncio.wait(
                [http_task, tcp_task], 
                return_when=asyncio.FIRST_COMPLETED, 
                timeout=4.0  # Timeout total agressivo
            )
            
            # Cancela tasks pendentes
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Verifica se alguma teve sucesso
            for task in done:
                try:
                    result = await task
                    if result:
                        if self.logger:
                            logger.debug(f"Fast TCP check {endpoint}: SUCCESS (fase 1)")
                        return True
                except Exception:
                    pass
            
        except asyncio.TimeoutError:
            # Cancela todas se timeout geral
            for task in [http_task, tcp_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        
        # Fase 2: Fallback robusto apenas se fase 1 falhou
        if await self._robust_fallback_check(endpoint):
            if self.logger:
                logger.debug(f"Fast TCP check {endpoint}: SUCCESS (fase 2 - fallback)")
            return True
        
        if self.logger:
            logger.debug(f"Fast TCP check {endpoint}: FAILED")
        return False
    
    async def _quick_http_check(self, endpoint: str):
        """Verificação HTTP/HTTPS ultra-rápida"""
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Testa HTTPS e HTTP em paralelo
        async def test_protocol(protocol):
            try:
                connector = aiohttp.TCPConnector(ssl=ssl_context if protocol == "https" else None)
                timeout = aiohttp.ClientTimeout(total=3, connect=1.5)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(f"{protocol}://{endpoint}/", allow_redirects=True) as resp:
                        return resp.status < 500
            except:
                return False
        
        # Executa HTTPS e HTTP em paralelo
        https_task = asyncio.create_task(test_protocol("https"))
        http_task = asyncio.create_task(test_protocol("http"))
        
        try:
            done, pending = await asyncio.wait(
                [https_task, http_task], 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=3.5
            )
            
            # Cancela pendentes
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Retorna se alguma teve sucesso
            for task in done:
                try:
                    if await task:
                        return True
                except:
                    pass
        except asyncio.TimeoutError:
            # Cancela em caso de timeout
            for task in [https_task, http_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        
        return False
    
    async def _quick_tcp_check(self, endpoint: str):
        """Verificação de portas TCP rápida"""
        priority_ports = [443, 80]  # Apenas as 2 mais importantes para velocidade
        
        async def test_port(port):
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(endpoint, port), timeout=2)
                writer.close()
                await writer.wait_closed()
                return True
            except:
                return False
        
        # Testa as 2 portas em paralelo
        tasks = [asyncio.create_task(test_port(port)) for port in priority_ports]
        
        try:
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=2.5
            )
            
            # Cancela pendentes
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Retorna se alguma teve sucesso
            for task in done:
                try:
                    if await task:
                        return True
                except:
                    pass
        except asyncio.TimeoutError:
            # Cancela em caso de timeout
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        
        return False
    
    async def _robust_fallback_check(self, endpoint: str):
        """Fallback robusto para casos difíceis (ex: dgg.gg)"""
        import ssl
        
        # Configurações mais robustas mas ainda rápidas
        protocols = [
            ("https", 6),  # HTTPS com timeout maior
            ("http", 5),   # HTTP com timeout médio
        ]
        
        for protocol, timeout_val in protocols:
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                connector = aiohttp.TCPConnector(ssl=ssl_context if protocol == "https" else None)
                timeout = aiohttp.ClientTimeout(total=timeout_val, connect=timeout_val//2)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    # Tenta GET e HEAD em sequência rápida
                    for method in ['GET', 'HEAD']:
                        try:
                            request_method = session.get if method == 'GET' else session.head
                            async with request_method(
                                f"{protocol}://{endpoint}/",
                                allow_redirects=True,
                                headers={'User-Agent': 'InfraWatch/1.0'}
                            ) as resp:
                                if resp.status < 500:
                                    if self.logger:
                                        logger.debug(f"Fallback {endpoint}: {protocol.upper()} {method} {resp.status} - SUCCESS")
                                    return True
                        except asyncio.TimeoutError:
                            continue  # Tenta próximo método
                        except Exception:
                            break  # Protocolo não funciona, tenta próximo
                            
            except Exception:
                continue  # Tenta próximo protocolo
        
        return False

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
            "1.3.6.1.2.1.2.2.1",     # ifTable (includes ifOperStatus, ifInOctets, ifOutOctets)
            "1.3.6.1.2.1.4.20.1",    # ipAddrTable
        ]
        return any(oid.startswith(pattern) for pattern in table_patterns)

    async def _get_values_from_snmp_tables(self, engine, auth_data, ip: str, port: int, base_oid: str):
        """Obtém todos os valores de uma tabela SNMP usando next_cmd (SNMP walk)"""
        
        values = []
        try:
            # Criar o transport target primeiro
            transport_target = await UdpTransportTarget.create((ip, port), timeout=3.0, retries=2)
            # Começar do OID base
            current_oid = ObjectIdentity(base_oid)
            while True:
                try:
                    error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                        next_cmd(engine, auth_data, transport_target, ContextData(),
                        ObjectType(current_oid), lexicographicMode=False),
                        timeout=5.0  # Timeout geral maior
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
                        
                        if not oid_str.startswith(base_oid) or value in ['', 'None', 'noSuchInstance']:
                            break  # Saímos da tabela
                        
                        # Extrair o índice do OID (parte após o OID base)
                        index = oid_str[len(base_oid):].lstrip('.')
                        values.append({'index': index, 'value': value})

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

            return values if values else None

        except Exception as e:
            if self.logger:
                logger.debug(f"Error getting table values for {base_oid}: {e}")
            return None

    async def _perform_snmp_check(self, ip: str, force_new: bool = False):
        """Executa uma verificação SNMP e mede o tempo de resposta"""
        import time
        
        async with get_snmp_engine(force_new) as engine:
            auth_data = select_snmp_authentication(self.hosts_status[ip])
            oids_values = self.hosts_status[ip].oids.values() or []
            oids_keys = list(self.hosts_status[ip].oids.keys())
            port = self.hosts_status[ip].port or 161
            result = {}
            
            # Iniciar medição do tempo total
            snmp_start_time = time.perf_counter()

            if self.logger:
                logger.debug(f"SNMP {ip}: Iniciando verificação de {len(oids_values)} OIDs (timeout=3.0s, retries=2)")

            for idx, oid in enumerate(oids_values):
                try:
                    # Verificar se é uma tabela
                    if self._is_table_oid(oid):
                        # Usar next_cmd para tabelas (SNMP walk)
                        values = await self._get_values_from_snmp_tables(engine, auth_data, ip, port, oid)
                        result[oids_keys[idx]] = str(values) if values else None
                        if self.logger and values:
                            logger.debug(f"OID de tabela {oid} retornou {len(values)} entradas para {ip}")
                    else:
                        # Usar get_cmd para valores únicos
                        error_indication, error_status, error_index, var_binds = await asyncio.wait_for(
                            get_cmd(engine, auth_data,
                                await UdpTransportTarget.create((ip, port), timeout=3.0, retries=2),
                                ContextData(), ObjectType(ObjectIdentity(oid))), 
                            timeout=5.0  # Timeout geral maior
                        )

                        if not (error_indication or error_status or error_index):
                            result[oids_keys[idx]] = str(var_binds[0][1]) if var_binds[0][1] else None
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
                    # Não fazer raise aqui para permitir tentar outros OIDs
            
            # Calcular tempo total de resposta SNMP
            snmp_end_time = time.perf_counter()
            snmp_rtt = (snmp_end_time - snmp_start_time) * 1000  # Converter para milissegundos
            
            # Atualizar o tempo de resposta no host_status
            self.hosts_status[ip].snmp_rtt = snmp_rtt
            
            # Log final do resultado
            if self.logger:
                successful_oids = sum(1 for v in result.values() if v is not None)
                total_oids = len(result)
                logger.debug(f"SNMP check {ip}: {successful_oids}/{total_oids} OIDs responderam em {snmp_rtt:.1f}ms")
            
            return result

    async def check_single_host(self, host_status: HostStatus) -> HostStatus:
        """Verificação completa com controle de falhas consecutivas"""

        # Ping check
        snmp_data = None
        ip = host_status.ip
        ping_results = await self.fast_ping_check([ip])
        is_alive, rtt = ping_results.get(ip, (False, 0.0))


        if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            # Tenta SNMP com retry
            snmp_data = await self.fast_snmp_check_with_retry(ip)
        else:
            # Fallback TCP
            # Iniciar medição do tempo total
            ip_start_time = time.perf_counter()
            is_alive = await self.fast_tcp_check(ip)
            rtt = (time.perf_counter() - ip_start_time) * 1000
            if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
                snmp_data = await self.fast_snmp_check_with_retry(ip)


        # CORREÇÃO: Atualiza contadores de ping baseado APENAS no resultado do ping inicial
        if is_alive:
            self.hosts_status[ip].consecutive_ping_failures = 0
        elif self.hosts_status[ip].consecutive_ping_failures < self.max_consecutive_ping_failures + 1:
            self.hosts_status[ip].consecutive_ping_failures += 1


        # Atualiza contadores de SNMP separadamente
        if is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            if is_snmp_data_valid(snmp_data):
                self.hosts_status[ip].consecutive_snmp_failures = 0
                # Guardar dados anteriores para comparação de performance
                if hasattr(self.hosts_status[ip], 'snmp_data') and self.hosts_status[ip].snmp_data:
                    self.hosts_status[ip].previous_snmp_data = self.hosts_status[ip].snmp_data
                
                if self.logger:
                    successful_oids = sum(1 for v in snmp_data.values() if v is not None and str(v).strip())
                    total_oids = len(snmp_data)
                    logger.debug(f"SNMP {ip}: {successful_oids}/{total_oids} OIDs retornaram dados válidos")
            else:
                self.hosts_status[ip].consecutive_snmp_failures += 1
                self.global_failure_count += 1
                
                if self.logger:
                    if snmp_data:
                        failed_oids = [k for k, v in snmp_data.items() if v is None or not str(v).strip()]
                        logger.debug(f"SNMP {ip}: Falha na validação. OIDs falharam: {failed_oids}")
                    else:
                        logger.debug(f"SNMP {ip}: Nenhum dado retornado")
        elif is_alive and check_ip_for_snmp(self.hosts_status[ip]):
            # Host vivo mas sem dados SNMP (pode ser problema de conectividade SNMP)
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

    async def _check_performance_alerts(self, result: HostStatus, session_factory):
        """Verifica alertas de performance (CPU, Memória, Disco, Rede)"""
        if not result.snmp_data:
            return
        
        session = session_factory()
        try:
            alerts = []
            
            # CPU Alert
            cpu_alert, cpu_severity, cpu_msg = should_alert_cpu(result.snmp_data.get('hrProcessorLoad'), session)
            if cpu_alert:
                alerts.append(('cpu', cpu_severity, cpu_msg))
            
            # Memory Alert
            mem_alert, mem_severity, mem_msg = should_alert_memory(
                result.snmp_data.get('memTotalReal'),
                result.snmp_data.get('memAvailReal'),
                session
            )
            if mem_alert:
                alerts.append(('memory', mem_severity, mem_msg))
            
            # Storage Alert
            storage_alert, storage_severity, storage_msg = should_alert_storage(
                result.snmp_data.get('hrStorageSize'),
                result.snmp_data.get('hrStorageUsed'),
                result.snmp_data.get('hrStorageDescr'),
                session
            )
            if storage_alert:
                alerts.append(('storage', storage_severity, storage_msg))
            
            # Network Alert
            network_alert, network_severity, network_msg = should_alert_network(
                result.snmp_data.get('ifOperStatus'),
                result.snmp_data.get('ifInOctets'),
                result.snmp_data.get('ifOutOctets'),
                getattr(result, 'previous_snmp_data', None),
                session
            )
            if network_alert:
                alerts.append(('network', network_severity, network_msg))
            
            # Enviar alertas encontrados
            for alert_type, severity, message in alerts:
                await self._send_performance_alert(session_factory, result, alert_type, severity, message)
                
        except Exception as e:
            if self.logger:
                logger.error(f"Error checking performance alerts for {result.ip}: {e}")
        finally:
            session.close()

    async def _send_performance_alert(self, session_factory, result, alert_type, severity, message):
        """Envia alerta de performance específico"""
        alert_config = {
            'cpu': {
                'title': f'🔴 CPU Alta - {result.nickname or result.ip}',
                'category': 'performance'
            },
            'memory': {
                'title': f'🟠 Memória Alta - {result.nickname or result.ip}',
                'category': 'performance'
            },
            'storage': {
                'title': f'🟡 Disco Cheio - {result.nickname or result.ip}',
                'category': 'performance'
            },
            'network': {
                'title': f'🔵 Problema de Rede - {result.nickname or result.ip}',
                'category': 'network'
            }
        }
        
        config = alert_config[alert_type]
        
        # Verificar se já não enviamos alerta recente do mesmo tipo
        if not self._should_send_performance_alert(result.ip, alert_type):
            return
        
        try:
            # Criar alerta no banco de dados
            session = session_factory()
            try:
                create_alert(
                    title=config['title'],
                    description=message,
                    severity=severity,
                    category=config['category'],
                    system="monitoring",
                    impact=f"{alert_type} performance issue",
                    id_endpoint=result._id,
                    id_user_created=1,  # Sistema
                    assignee="admin",
                    session=session
                )
            finally:
                session.close()

            # Email
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.alert_email.send_alert_email,
                config['title'],
                result.nickname or result.ip,
                result.ip,
                f"{alert_type.upper()} ALERT",
                datetime.now(),
                message
            )

            # Webhook
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.alert_webhook.send_alert_webhook,
                result.nickname or result.ip,
                result.ip,
                f"{alert_type.upper()} ALERT",
                datetime.now(),
                message
            )
            
        except Exception as e:
            if self.logger:
                logger.error(f"Error sending {alert_type} alert for {result.ip}: {e}")

    def _should_send_performance_alert(self, ip: str, alert_type: str) -> bool:
        """Evita spam de alertas - só envia a cada 30 minutos"""
        key = f"{ip}_{alert_type}"
        now = datetime.now()
        
        last_sent = self._last_performance_alerts.get(key)
        if last_sent and (now - last_sent).seconds < 1800:  # 30 minutos
            return False
        
        self._last_performance_alerts[key] = now
        return True

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
            not is_snmp_data_valid(result.snmp_data) and
            not getattr(host_data, 'snmp_informed', False)):
            await self._process_alert(session_factory, "snmp_down", result, snmp_failures)
            host_data.consecutive_snmp_failures = 0
            host_data.snmp_informed = True
    
        # 4. Verificar snmp up (snmp voltou a responder)
        elif (result.is_alive and
              check_ip_for_snmp(host_data) and
              is_snmp_data_valid(result.snmp_data) and
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
        if check_ip_for_snmp(result) and is_snmp_data_valid(result.snmp_data):
            name = result.snmp_data.get('sysName')
            if not name and result.snmp_data.get('sysDescr'):
                name = result.snmp_data['sysDescr'].split(' ')[0]
            else:
                name = result.nickname if result.nickname else ip

        try:
            self.alert_email.send_alert_email(
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
                id_user_created=DEFAULT_SYSTEM_USER_ID,
                assignee=DEFAULT_SYSTEM_USER_ID,
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

        session_factory = init_session_monitor
        last_engine_refresh = datetime.now()

        while True:
            start_time = asyncio.get_event_loop().time()
            async for result in self.monitoring_cycle():
                if result:
                    interval = int(result.interval) if result.interval else interval
                    await asyncio.gather(
                        self.send_alert(session_factory, result),
                        self._check_performance_alerts(result, session_factory),
                        self.insert_snmp_data_async(session_factory, result),
                        self.sla_collector.collect_sla_metrics(result, session_factory),
                        return_exceptions=True
                    )

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
    if len(sys.argv) > 1:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor(logger=True)
        asyncio.run(monitor.run_monitoring(interval=30.0))
    else:
        print("⚡ Modo OTIMIZADO ativado!")
        monitor = OptimizedMonitor()
        asyncio.run(monitor.run_monitoring(interval=30.0))

