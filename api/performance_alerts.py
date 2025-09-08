from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from sqlalchemy.orm import Session
from .models import PerformanceThresholds


def parse_snmp_list_data(data) -> List[Dict[str, str]]:
    """
    Converte dados SNMP de string JSON para lista de dicts
    """
    if not data:
        return []
    
    if isinstance(data, str):
        try:
            # Corrigir aspas simples para duplas
            json_str = data.replace("'", '"')
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    elif isinstance(data, list):
        return data
    
    return []


def get_thresholds(session: Session, metric_type: str) -> Tuple[int, int]:
    """
    Busca os limites de warning e critical para uma métrica específica
    """
    threshold = session.query(PerformanceThresholds).filter(
        PerformanceThresholds.metric_type == metric_type,
        PerformanceThresholds.enabled == True
    ).first()
    
    if threshold:
        return threshold.warning_threshold, threshold.critical_threshold
    
    # Valores padrão se não configurado
    defaults = {
        'cpu': (80, 90),
        'memory': (85, 95),
        'storage': (85, 95),
        'network': (80, 95)
    }
    return defaults.get(metric_type, (80, 90))


def should_alert_cpu(cpu_data, session: Session) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica se deve alertar sobre CPU
    Returns: (should_alert, severity, message)
    """
    if not cpu_data:
        return False, None, None
    
    warning_threshold, critical_threshold = get_thresholds(session, 'cpu')
    cpu_list = parse_snmp_list_data(cpu_data)
    
    if not cpu_list:
        return False, None, None
    
    # Calcular média de CPU de todos os cores
    total_cpu = sum(int(core['value']) for core in cpu_list if core.get('value', '').isdigit())
    avg_cpu = total_cpu / len(cpu_list) if cpu_list else 0
    
    if avg_cpu >= critical_threshold:
        return True, "critical", f"CPU CRÍTICA: {avg_cpu:.1f}% (limite: {critical_threshold}%)"
    elif avg_cpu >= warning_threshold:
        return True, "high", f"CPU ALTA: {avg_cpu:.1f}% (limite: {warning_threshold}%)"
    
    return False, None, None


def should_alert_memory(mem_total, mem_avail, session: Session) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica se deve alertar sobre Memória
    Returns: (should_alert, severity, message)
    """
    if not mem_total or not mem_avail:
        return False, None, None
    
    try:
        total = int(mem_total)
        available = int(mem_avail)
        
        if total <= 0:
            return False, None, None
            
        used_percent = ((total - available) / total) * 100
        warning_threshold, critical_threshold = get_thresholds(session, 'memory')
        
        if used_percent >= critical_threshold:
            return True, "critical", f"MEMÓRIA CRÍTICA: {used_percent:.1f}% usada (limite: {critical_threshold}%)"
        elif used_percent >= warning_threshold:
            return True, "medium", f"MEMÓRIA ALTA: {used_percent:.1f}% usada (limite: {warning_threshold}%)"
        
    except (ValueError, TypeError):
        return False, None, None
    
    return False, None, None


def should_alert_storage(storage_size, storage_used, storage_descr, session: Session) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica se deve alertar sobre Disco
    Returns: (should_alert, severity, message)
    """
    if not storage_size or not storage_used:
        return False, None, None
    
    warning_threshold, critical_threshold = get_thresholds(session, 'storage')
    size_list = parse_snmp_list_data(storage_size)
    used_list = parse_snmp_list_data(storage_used)
    descr_list = parse_snmp_list_data(storage_descr)

    if not size_list or not used_list or not descr_list:
        return False, None, None
    
    alerts = []
    max_severity = None
    
    for i, size_entry in enumerate(size_list):
        if i < len(used_list) and i < len(descr_list):
            try:
                size = int(size_entry['value'])
                used = int(used_list[i]['value'])
                descr = descr_list[i]['value']

                if size > 0:  # Evitar divisão por zero
                    used_percent = (used / size) * 100
                    
                    if used_percent >= critical_threshold:
                        alerts.append(f"Disco {size_entry['index']} {descr}: {used_percent:.1f}% CRÍTICO")
                        max_severity = "critical"
                    elif used_percent >= warning_threshold:
                        alerts.append(f"Disco {size_entry['index']} {descr}: {used_percent:.1f}% ALTO")
                        if max_severity != "critical":
                            max_severity = "medium"
            except (ValueError, TypeError):
                continue
    
    if alerts:
        return True, max_severity, "; ".join(alerts)
    
    return False, None, None


def should_alert_network(if_status, if_in_octets, if_out_octets, previous_data, session: Session) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Verifica se deve alertar sobre Rede
    Returns: (should_alert, severity, message)
    """
    alerts = []
    max_severity = None
    
    # Verificar interfaces DOWN
    status_list = parse_snmp_list_data(if_status)
    for interface in status_list:
        if interface.get('value') != '1':  # 1 = up, 2 = down
            alerts.append(f"Interface {interface['index']} está DOWN")
            max_severity = "critical"

    # Verificar utilização alta de rede (se temos dados anteriores)
    if previous_data and if_in_octets and if_out_octets:
        warning_threshold, critical_threshold = get_thresholds(session, 'network')
        in_octets_list = parse_snmp_list_data(if_in_octets)
        out_octets_list = parse_snmp_list_data(if_out_octets)
        prev_in_list = parse_snmp_list_data(previous_data.get('ifInOctets'))
        prev_out_list = parse_snmp_list_data(previous_data.get('ifOutOctets'))
        
        if in_octets_list and out_octets_list and prev_in_list and prev_out_list:
            time_diff = 30  # Intervalo de monitoramento em segundos

            for i, in_octets in enumerate(in_octets_list):
                if i < len(out_octets_list) and i < len(prev_in_list) and i < len(prev_out_list):
                    try:
                        current_in = int(in_octets['value'])
                        current_out = int(out_octets_list[i]['value'])
                        prev_in = int(prev_in_list[i]['value'])
                        prev_out = int(prev_out_list[i]['value'])
                        
                        # Calcular bytes por segundo
                        in_bps = max(0, (current_in - prev_in) / time_diff)
                        out_bps = max(0, (current_out - prev_out) / time_diff)
                        
                        # Assumindo link de 1Gbps = 125MB/s (125,000,000 bytes/s)
                        link_capacity = 125_000_000
                        in_percent = (in_bps / link_capacity) * 100
                        out_percent = (out_bps / link_capacity) * 100
                        
                        max_percent = max(in_percent, out_percent)
                        
                        if max_percent >= critical_threshold:
                            alerts.append(f"Interface {in_octets['index']}: Tráfego CRÍTICO ({max_percent:.1f}%)")
                            if max_severity != "critical":
                                max_severity = "critical"
                        elif max_percent >= warning_threshold:
                            alerts.append(f"Interface {in_octets['index']}: Tráfego ALTO ({max_percent:.1f}%)")
                            if max_severity not in ["critical"]:
                                max_severity = "medium"
                                
                    except (ValueError, TypeError):
                        continue
    
    if alerts:
        return True, max_severity or "medium", "; ".join(alerts)
    
    return False, None, None


def initialize_default_thresholds(session: Session):
    """
    Inicializa os limites padrão se não existirem
    """
    default_thresholds = [
        ('cpu', 80, 90),
        ('memory', 85, 95),
        ('storage', 85, 95),
        ('network', 80, 95)
    ]
    
    for metric_type, warning, critical in default_thresholds:
        existing = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.metric_type == metric_type
        ).first()
        
        if not existing:
            threshold = PerformanceThresholds(
                metric_type=metric_type,
                warning_threshold=warning,
                critical_threshold=critical,
                enabled=True
            )
            session.add(threshold)
    
    session.commit()

