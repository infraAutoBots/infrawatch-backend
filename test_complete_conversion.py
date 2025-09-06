#!/usr/bin/env python3
"""
Teste completo de conversão automática
"""

from api.schemas import EndPointsDataSchemas
from datetime import datetime

def test_complete_conversion():
    print("🎯 Teste Completo: Simulando dados do monitor.py\n")

    # Simulando dados como viriam do monitor.py
    snmp_data_from_monitor = {
        'id_end_point': 1,
        'status': True,
        'sysDescr': 'Linux Ubuntu 20.04.3 LTS',
        'sysName': 'server-prod-01',
        'sysUpTime': '1234567890',
        'hrProcessorLoad': "[{'index': '1', 'value': '23'}, {'index': '2', 'value': '31'}, {'index': '3', 'value': '18'}, {'index': '4', 'value': '45'}]",
        'memTotalReal': '16777216',  # 16GB em KB
        'memAvailReal': '8388608',   # 8GB em KB  
        'hrStorageSize': "[{'index': '1', 'value': '500000000'}, {'index': '2', 'value': '1000000000'}]",
        'hrStorageUsed': "[{'index': '1', 'value': '250000000'}, {'index': '2', 'value': '750000000'}]",
        'last_updated': datetime.now()
    }

    try:
        # Testando conversão
        result = EndPointsDataSchemas(**snmp_data_from_monitor)
        
        print("✅ Conversão bem-sucedida!")
        print(f"📊 Processadores ({len(result.hrProcessorLoad)} cores):")
        for cpu in result.hrProcessorLoad:
            print(f"   Core {cpu['index']}: {cpu['value']}% de uso")
            
        print(f"\n💾 Storages ({len(result.hrStorageSize)} discos):")
        for i, storage in enumerate(result.hrStorageSize):
            used = result.hrStorageUsed[i] if i < len(result.hrStorageUsed) else {'value': '0'}
            size_gb = int(storage['value']) / 1000000  # Conversão simplificada
            used_gb = int(used['value']) / 1000000
            usage_percent = (used_gb / size_gb * 100) if size_gb > 0 else 0
            print(f"   Disco {storage['index']}: {used_gb:.1f}GB / {size_gb:.1f}GB ({usage_percent:.1f}%)")
            
        print(f"\n🖥️  Sistema: {result.sysName} - {result.sysDescr}")
        print(f"⏰ Uptime: {result.sysUpTime} segundos")
        print(f"💾 RAM: {int(result.memAvailReal)/1024/1024:.1f}GB disponível de {int(result.memTotalReal)/1024/1024:.1f}GB total")
        
        print("\n🎉 SUCESSO: A conversão automática String ↔ Dict está funcionando perfeitamente!")
        print("✅ Os dados do monitor.py serão convertidos automaticamente pelo Pydantic!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conversão: {e}")
        return False

if __name__ == "__main__":
    test_complete_conversion()
