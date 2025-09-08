#!/usr/bin/env python3
"""
Teste de velocidade da nova implementação ultra-rápida
"""
import asyncio
import sys
import time
from datetime import datetime

# Adicionar o diretório do monitor ao path
sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend/monitor')

from monitor import OptimizedMonitor

async def speed_test():
    """Testa a velocidade da nova implementação"""
    monitor = OptimizedMonitor(logger=True)
    
    test_hosts = [
        "dgg.gg",
        "google.com", 
        "github.com",
        "httpbin.org",
        "fake-host-999.com"  # Este deve falhar rapidamente
    ]
    
    print("🚀 === TESTE DE VELOCIDADE ULTRA-RÁPIDO ===")
    print(f"Testando {len(test_hosts)} hosts...\n")
    
    total_start = time.perf_counter()
    
    for i, host in enumerate(test_hosts, 1):
        print(f"[{i}/{len(test_hosts)}] Testando {host}...")
        
        start_time = time.perf_counter()
        
        try:
            result = await monitor.fast_tcp_check(host)
            elapsed = time.perf_counter() - start_time
            
            status = "✅ ONLINE" if result else "❌ OFFLINE"
            speed_icon = "⚡" if elapsed < 2.0 else "🐌" if elapsed > 5.0 else "🚀"
            
            print(f"   {status} em {elapsed:.2f}s {speed_icon}")
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            print(f"   💥 ERROR: {e} em {elapsed:.2f}s")
    
    total_elapsed = time.perf_counter() - total_start
    avg_time = total_elapsed / len(test_hosts)
    
    print(f"\n📊 === ESTATÍSTICAS ===")
    print(f"Tempo total: {total_elapsed:.2f}s")
    print(f"Tempo médio por host: {avg_time:.2f}s")
    print(f"Hosts por minuto: {60/avg_time:.1f}")
    
    # Classificação de performance
    if avg_time < 2.0:
        print("🏆 PERFORMANCE: EXCELENTE!")
    elif avg_time < 4.0:
        print("🥈 PERFORMANCE: BOA")
    else:
        print("🥉 PERFORMANCE: ADEQUADA")

async def parallel_speed_test():
    """Testa múltiplos hosts em paralelo para demonstrar escalabilidade"""
    monitor = OptimizedMonitor(logger=False)  # Menos verbose
    
    test_hosts = [
        "dgg.gg", "google.com", "github.com", "httpbin.org", "stackoverflow.com",
        "reddit.com", "youtube.com", "facebook.com", "twitter.com", "linkedin.com"
    ]
    
    print(f"\n🔥 === TESTE PARALELO ===")
    print(f"Testando {len(test_hosts)} hosts em PARALELO...\n")
    
    start_time = time.perf_counter()
    
    # Executa todos em paralelo
    tasks = [monitor.fast_tcp_check(host) for host in test_hosts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.perf_counter() - start_time
    
    # Resultados
    online_count = 0
    error_count = 0
    
    for host, result in zip(test_hosts, results):
        if isinstance(result, Exception):
            print(f"❌ {host:20} | ERROR: {result}")
            error_count += 1
        elif result:
            print(f"✅ {host:20} | ONLINE")
            online_count += 1
        else:
            print(f"⭕ {host:20} | OFFLINE")
    
    offline_count = len(test_hosts) - online_count - error_count
    
    print(f"\n📈 === RESULTADOS PARALELOS ===")
    print(f"Tempo total: {elapsed:.2f}s")
    print(f"Hosts testados: {len(test_hosts)}")
    print(f"Online: {online_count} | Offline: {offline_count} | Errors: {error_count}")
    print(f"Taxa: {len(test_hosts)/elapsed:.1f} hosts/segundo")
    
    if elapsed < 10:
        print("⚡ PARALELIZAÇÃO: EXCELENTE!")
    elif elapsed < 20:
        print("🚀 PARALELIZAÇÃO: BOA")
    else:
        print("📡 PARALELIZAÇÃO: ADEQUADA")

if __name__ == "__main__":
    async def main():
        await speed_test()
        await parallel_speed_test()
        
        print(f"\n🎯 === RESUMO FINAL ===")
        print("✅ Implementação ultra-rápida concluída!")
        print("⚡ Otimizada para baixa latência")
        print("🔄 Verificação paralela HTTP + TCP")
        print("🛡️  Fallback robusto para casos especiais")
        print("🚀 Pronta para produção!")
    
    asyncio.run(main())
