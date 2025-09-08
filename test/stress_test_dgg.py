#!/usr/bin/env python3
"""
Teste ultra-robusto para dgg.gg simulando condições de produção
"""
import asyncio
import sys
import os
from datetime import datetime

# Adicionar o diretório do monitor ao path
sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend/monitor')

from monitor import OptimizedMonitor

async def stress_test_dgg():
    """Testa dgg.gg múltiplas vezes para verificar consistência"""
    monitor = OptimizedMonitor(logger=True)
    
    host = "dgg.gg"
    total_tests = 10
    successes = 0
    failures = 0
    
    print(f"=== Teste de Stress para {host} ===")
    print(f"Executando {total_tests} tentativas...\n")
    
    for i in range(1, total_tests + 1):
        print(f"Tentativa {i}/{total_tests}:")
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await monitor.fast_tcp_check(host)
            elapsed = asyncio.get_event_loop().time() - start_time
            
            if result:
                successes += 1
                print(f"  ✅ SUCCESS ({elapsed:.2f}s)")
            else:
                failures += 1
                print(f"  ❌ FAILED ({elapsed:.2f}s)")
                
        except Exception as e:
            failures += 1
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"  💥 ERROR: {e} ({elapsed:.2f}s)")
        
        # Pequena pausa entre tentativas para simular condições reais
        if i < total_tests:
            await asyncio.sleep(1)
    
    print(f"\n=== Resultados Finais ===")
    print(f"Sucessos: {successes}/{total_tests} ({successes/total_tests*100:.1f}%)")
    print(f"Falhas: {failures}/{total_tests} ({failures/total_tests*100:.1f}%)")
    
    if successes >= total_tests * 0.8:  # 80% de sucesso
        print("🎉 TESTE PASSOU - Sistema robusto!")
    else:
        print("⚠️  TESTE FALHOU - Necessita mais ajustes")
    
    return successes, failures

async def compare_with_other_hosts():
    """Compara dgg.gg com outros hosts conhecidos"""
    monitor = OptimizedMonitor(logger=False)  # Menos verbose para comparação
    
    hosts = {
        "dgg.gg": "Problemático",
        "google.com": "Confiável", 
        "github.com": "Confiável",
        "httpbin.org": "Confiável",
        "fake-host-999.com": "Deve falhar"
    }
    
    print(f"\n=== Comparação com outros hosts ===")
    
    for host, desc in hosts.items():
        try:
            result = await monitor.fast_tcp_check(host)
            status = "✅ ONLINE" if result else "❌ OFFLINE"
            print(f"{host:20} | {desc:12} | {status}")
        except Exception as e:
            print(f"{host:20} | {desc:12} | 💥 ERROR: {e}")

if __name__ == "__main__":
    async def main():
        # Teste principal
        successes, failures = await stress_test_dgg()
        
        # Comparação
        await compare_with_other_hosts()
        
        # Resumo final
        print(f"\n=== RESUMO EXECUTIVO ===")
        if failures == 0:
            print("🎯 PERFEITO: 100% de sucessos!")
        elif failures <= 2:
            print("✅ BOM: Poucas falhas, dentro do aceitável")
        else:
            print("⚠️  PROBLEMA: Muitas falhas, necessita investigação")
    
    asyncio.run(main())
