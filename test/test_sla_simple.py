#!/usr/bin/env python3
"""
Script simples para criar dados de teste SLA usando SQL direto
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
    
    # Verificar se há endpoints
    cursor.execute("SELECT COUNT(*) FROM endpoints")
    endpoint_count = cursor.fetchone()[0]
    
    if endpoint_count == 0:
        print("❌ Nenhum endpoint encontrado. Criando alguns de teste...")
        # Criar endpoints de teste
        test_endpoints = [
            ("8.8.8.8", "public", 60, "2c", 161, "Google DNS"),
            ("1.1.1.1", "public", 60, "2c", 161, "Cloudflare DNS"), 
            ("192.168.1.1", "public", 60, "2c", 161, "Gateway Local")
        ]
        
        for ip, community, interval, version, port, nickname in test_endpoints:
            cursor.execute("""
                INSERT INTO endpoints (ip, community, interval, version, port, nickname)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ip, community, interval, version, port, nickname))
        
        conn.commit()
        print("✅ Endpoints de teste criados")
    
    # Obter endpoints para criar dados
    cursor.execute("SELECT id, ip, nickname FROM endpoints LIMIT 3")
    endpoints = cursor.fetchall()
    
    print(f"🔍 Usando {len(endpoints)} endpoints para dados de teste")
    
    # Criar dados SLA para os últimos 7 dias
    start_date = datetime.now() - timedelta(days=7)
    
    for endpoint_id, ip, nickname in endpoints:
        print(f"📊 Criando dados SLA para {ip} ({nickname})")
        
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            
            # Simular dados de SLA com variação realística
            uptime = 99.9 - (day * 0.1) - random.uniform(0, 0.5)
            downtime_minutes = (1440 * (100 - uptime)) / 100
            successful_checks = int(1440 * (uptime / 100))
            failed_checks = 1440 - successful_checks
            
            # Inserir métricas SLA
            cursor.execute("""
                INSERT INTO sla_metrics 
                (endpoint_id, period_start, period_end, uptime_percentage, 
                 downtime_minutes, total_checks, successful_checks, failed_checks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                current_date.isoformat(),
                (current_date + timedelta(days=1)).isoformat(),
                uptime,
                downtime_minutes,
                1440,
                successful_checks,
                failed_checks
            ))
            
            # Criar incidentes para endpoints com problemas
            if uptime < 99.5:
                severity = "high" if uptime < 98 else "medium"
                start_time = current_date + timedelta(hours=2)
                end_time = start_time + timedelta(minutes=int(downtime_minutes))
                
                cursor.execute("""
                    INSERT INTO incidents 
                    (endpoint_id, incident_type, start_time, end_time, 
                     severity, description, resolution_time_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint_id,
                    "connectivity",
                    start_time.isoformat(),
                    end_time.isoformat(),
                    severity,
                    f"Conectividade degradada - uptime: {uptime:.1f}%",
                    int(downtime_minutes)
                ))
            
            # Dados de performance - Response Time
            cursor.execute("""
                INSERT INTO performance_metrics 
                (endpoint_id, metric_type, timestamp, value, percentile_95, percentile_99)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                "response_time",
                current_date.isoformat(),
                50.0 + (day * 5) + random.uniform(-10, 10),
                75.0 + (day * 7) + random.uniform(-5, 15),
                90.0 + (day * 10) + random.uniform(-5, 20)
            ))
            
            # CPU Usage
            cursor.execute("""
                INSERT INTO performance_metrics 
                (endpoint_id, metric_type, timestamp, value, percentile_95, percentile_99)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                endpoint_id,
                "cpu_usage",
                current_date.isoformat(),
                60.0 + (day * 3) + random.uniform(-10, 15),
                80.0 + (day * 2) + random.uniform(-5, 10),
                95.0 + day + random.uniform(-2, 5)
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
    
    conn.close()

if __name__ == "__main__":
    create_test_data()
    print("🎉 Processo concluído!")
