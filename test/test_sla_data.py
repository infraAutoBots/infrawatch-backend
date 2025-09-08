#!/usr/bin/env python3
"""
Script para criar dados de teste para o sistema SLA
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Adicionar o caminho do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitor'))

from monitor.models import SLAMetrics, IncidentTracking, PerformanceMetrics, EndPoints
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_test_data():
    """Cria dados de teste para demonstrar o sistema SLA"""
    # Conectar ao banco de dados diretamente
    engine = create_engine('sqlite:///database.db')
    session_factory = sessionmaker(bind=engine)
    
    with session_factory() as session:
        # Verificar se há endpoints
        endpoints = session.query(EndPoints).limit(3).all()
        if not endpoints:
            print("❌ Nenhum endpoint encontrado. Criando alguns de teste...")
            # Criar endpoints de teste
            test_endpoints = [
                EndPoints(ip="8.8.8.8", community="public", interval=60, version="2c", port=161, nickname="Google DNS"),
                EndPoints(ip="1.1.1.1", community="public", interval=60, version="2c", port=161, nickname="Cloudflare DNS"),
                EndPoints(ip="192.168.1.1", community="public", interval=60, version="2c", port=161, nickname="Gateway Local")
            ]
            for endpoint in test_endpoints:
                session.add(endpoint)
            session.commit()
            endpoints = test_endpoints
            print("✅ Endpoints de teste criados")
        
        print(f"🔍 Usando {len(endpoints)} endpoints para dados de teste")
        
        # Criar dados SLA para os últimos 7 dias
        start_date = datetime.now() - timedelta(days=7)
        
        for endpoint in endpoints:
            print(f"📊 Criando dados SLA para {endpoint.ip} ({endpoint.nickname})")
            
            for day in range(7):
                current_date = start_date + timedelta(days=day)
                
                # Simular dados de SLA com variação realística
                uptime = 99.9 - (day * 0.1)  # Degradação gradual
                downtime_minutes = (1440 * (100 - uptime)) / 100  # Total de minutos em um dia
                
                sla_metric = SLAMetrics(
                    endpoint_id=endpoint.id,
                    period_start=current_date,
                    period_end=current_date + timedelta(days=1),
                    uptime_percentage=uptime,
                    downtime_minutes=downtime_minutes,
                    total_checks=1440,  # Checks a cada minuto
                    successful_checks=int(1440 * (uptime / 100)),
                    failed_checks=1440 - int(1440 * (uptime / 100))
                )
                session.add(sla_metric)
                
                # Criar alguns incidentes para endpoints com problemas
                if uptime < 99.5:
                    incident = IncidentTracking(
                        endpoint_id=endpoint.id,
                        incident_type="connectivity",
                        start_time=current_date + timedelta(hours=2),
                        end_time=current_date + timedelta(hours=2, minutes=int(downtime_minutes)),
                        severity="medium" if uptime > 98 else "high",
                        description=f"Conectividade degradada - uptime: {uptime:.1f}%",
                        resolution_time_minutes=int(downtime_minutes)
                    )
                    session.add(incident)
                
                # Dados de performance
                performance = PerformanceMetrics(
                    endpoint_id=endpoint.id,
                    metric_type="response_time",
                    timestamp=current_date,
                    value=50.0 + (day * 5),  # Response time crescendo
                    percentile_95=75.0 + (day * 7),
                    percentile_99=90.0 + (day * 10)
                )
                session.add(performance)
                
                # CPU metrics
                cpu_metric = PerformanceMetrics(
                    endpoint_id=endpoint.id,
                    metric_type="cpu_usage",
                    timestamp=current_date,
                    value=60.0 + (day * 3),
                    percentile_95=80.0 + (day * 2),
                    percentile_99=95.0 + day
                )
                session.add(cpu_metric)
        
        session.commit()
        print("✅ Dados de teste criados com sucesso!")
        
        # Verificar os dados criados
        sla_count = session.query(SLAMetrics).count()
        incident_count = session.query(IncidentTracking).count()
        perf_count = session.query(PerformanceMetrics).count()
        
        print(f"\n📈 Resumo dos dados criados:")
        print(f"   - Métricas SLA: {sla_count}")
        print(f"   - Incidentes: {incident_count}")
        print(f"   - Métricas de Performance: {perf_count}")


if __name__ == "__main__":
    print("🔄 Criando dados de teste para o sistema SLA...")
    create_test_data()
    print("🎉 Processo concluído!")
