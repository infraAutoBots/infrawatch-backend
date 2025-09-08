#!/usr/bin/env python3
"""
Teste rápido para verificar dgg.gg com o monitor real
"""
import asyncio
import sys
import os

# Adicionar o diretório do monitor ao path
sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend/monitor')

from monitor import OptimizedMonitor

async def test_dgg_with_monitor():
    monitor = OptimizedMonitor(logger=True)
    
    print("=== Teste com monitor real ===")
    print("Testando dgg.gg...")
    
    result = await monitor.fast_tcp_check("dgg.gg")
    print(f"Resultado: {'✅ ONLINE' if result else '❌ OFFLINE'}")
    
    # Testar alguns outros hosts para comparação
    test_hosts = ["google.com", "github.com", "fake-host-999.com"]
    
    for host in test_hosts:
        print(f"Testando {host}...")
        result = await monitor.fast_tcp_check(host)
        print(f"Resultado: {'✅ ONLINE' if result else '❌ OFFLINE'}")

if __name__ == "__main__":
    asyncio.run(test_dgg_with_monitor())
