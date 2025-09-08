#!/usr/bin/env python3
"""
Script simples para criar dados de teste SLA usando SQL direto - versão corrigida
"""

import sqlite3
from datetime import datetime, timedelta
import random

def create_test_data():
    """Cria dados de teste para demonstrar o sistema SLA"""
    
    # Conectar ao banco
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("🔄 Criando dados de teste para o sistema SLA...")
    
    # Obter endpoints existentes
    cursor.execute("SELECT id, ip, nickname FROM endpoints LIMIT 3")
    endpoints = cursor.fetchall()
    
    if not endpoints:
        print("❌ Nenhum endpoint encontrado!")
        return
    
    print(f"🔍 Usando {len(endpoints)} endpoints para dados de teste")
    
    # Criar dados SLA para os últimos 7 dias
    start_date = datetime.now() - timedelta(days=7)
    
    for endpoint_id, ip, nickname in endpoints:
        nickname_display = nickname if nickname else "Sem nome"
        print(f"📊 Criando dados SLA para {ip} ({nickname_display})")
        
        for day in range(7):
            current_timestamp = start_date + timedelta(days=day, hours=random.randint(0, 23))
            
            # Simular dados de SLA realísticos
            availability = 99.9 - (day * 0.1) - random.uniform(0, 0.5)
            uptime_sec = int(86400 * (availability / 100))  # segundos em um dia
            downtime_sec = 86400 - uptime_sec
            
            # Métricas de tempo de resposta
            avg_response = 50.0 + (day * 5) + random.uniform(-10, 10)
            min_response = max(1.0, avg_response - random.uniform(10, 30))
            max_response = avg_response + random.uniform(20, 100)
            
            # Inserir métricas SLA
            cursor.execute("""
                INSERT INTO sla_metrics 
                (endpoint_id, timestamp, availability_percentage, uptime_seconds, 
                 downtime_seconds, mttr_minutes, mtbf_hours, incidents_count,
                 sla_target, sla_compliance, sla_breach_minutes,
                 avg_response_time, max_response_time, min_response_time, measurement_period_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                current_timestamp.isoformat(),
                availability,
                uptime_sec,
                downtime_sec,
                random.uniform(5, 30),  # MTTR
                random.uniform(100, 500),  # MTBF
                1 if availability < 99.5 else 0,  # incidents count
                99.9,  # SLA target
                1 if availability >= 99.9 else 0,  # compliance
                max(0, (99.9 - availability) * 14.4),  # breach minutes
                avg_response,
                max_response,
                min_response,
                24  # measurement period
            ))
            
            # Criar incidentes para endpoints com problemas
            if availability < 99.5:
                severity_map = {"high": availability < 98, "medium": availability < 99.2, "low": True}
                severity = next(s for s, condition in severity_map.items() if condition)
                
                start_time = current_timestamp + timedelta(hours=random.randint(1, 10))
                duration_minutes = random.randint(5, int(downtime_sec / 60))
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                cursor.execute("""
                    INSERT INTO incidents 
                    (endpoint_id, incident_type, severity, status, start_time, end_time, 
                     duration_seconds, impact_description, detected_by, 
                     response_time_minutes, resolution_time_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint_id,
                    "connectivity",
                    severity,
                    "resolved",
                    start_time.isoformat(),
                    end_time.isoformat(),
                    duration_minutes * 60,
                    f"Connectividade degradada - disponibilidade: {availability:.1f}%",
                    "monitor_system",
                    random.uniform(1, 5),  # response time
                    duration_minutes  # resolution time
                ))
            
            # Dados de performance
            cursor.execute("""
                INSERT INTO performance_metrics 
                (endpoint_id, timestamp, response_time_p50, response_time_p90, 
                 response_time_p95, response_time_p99, response_time_p99_9,
                 response_time_avg, response_time_max, response_time_min,
                 error_rate_percentage, total_requests, failed_requests,
                 measurement_period_minutes, sample_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                current_timestamp.isoformat(),
                avg_response * 0.8,  # p50
                avg_response * 1.2,  # p90
                avg_response * 1.5,  # p95
                avg_response * 2.0,  # p99
                max_response,        # p99.9
                avg_response,
                max_response,
                min_response,
                (100 - availability) / 10,  # error rate
                random.randint(1000, 5000),  # total requests
                int(random.randint(1000, 5000) * ((100 - availability) / 100)),  # failed requests
                60,  # measurement period
                random.randint(100, 500)  # sample count
            ))
    
    conn.commit()
    
    # Verificar os dados criados
    cursor.execute("SELECT COUNT(*) FROM sla_metrics")
    sla_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM incidents")
    incident_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM performance_metrics")
    perf_count = cursor.fetchone()[0]
    
    print(f"\n✅ Dados de teste criados com sucesso!")
    print(f"\n📈 Resumo dos dados criados:")
    print(f"   - Métricas SLA: {sla_count}")
    print(f"   - Incidentes: {incident_count}")
    print(f"   - Métricas de Performance: {perf_count}")
    
    # Mostrar algumas métricas de exemplo
    cursor.execute("""
        SELECT e.ip, s.availability_percentage, s.sla_compliance 
        FROM sla_metrics s 
        JOIN endpoints e ON s.endpoint_id = e.id 
        ORDER BY s.timestamp DESC LIMIT 5
    """)
    
    print(f"\n🔍 Exemplos de métricas recentes:")
    for ip, availability, compliance in cursor.fetchall():
        status = "✅ Conforme" if compliance else "❌ Não conforme"
        print(f"   - {ip}: {availability:.2f}% disponibilidade ({status})")
    
    conn.close()

if __name__ == "__main__":
    create_test_data()
    print("🎉 Processo concluído!")
