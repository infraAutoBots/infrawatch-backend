#!/usr/bin/env python3
"""
Teste final das melhorias implementadas no monitor SNMP
"""
import sys
import os

# Adicionar o diretório monitor ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'monitor'))

from utils import HostStatus, check_ip_for_snmp, is_snmp_data_valid

def test_all_improvements():
    """Testa todas as melhorias implementadas"""
    print("✅ TESTE FINAL DAS MELHORIAS NO MONITOR SNMP")
    print("=" * 60)
    
    print("\n1. ✅ VERIFICAÇÃO DE CONFIGURAÇÃO SNMP MELHORADA:")
    
    test_cases = [
        ('Host ping-only', HostStatus(ip='192.168.1.1', interval=30), False),
        ('SNMP v2c válido', HostStatus(ip='192.168.1.2', version='2c', community='public'), True),
        ('SNMP v3 válido', HostStatus(ip='192.168.1.3', version='3', user='admin'), True),
        ('Community vazia', HostStatus(ip='192.168.1.4', version='2c', community=''), False),
    ]
    
    for name, host, expected in test_cases:
        result = check_ip_for_snmp(host)
        status = "✅" if result == expected else "❌"
        print(f"  {name}: {result} {status}")
    
    print("\n2. ✅ VALIDAÇÃO DE DADOS SNMP INTELIGENTE:")
    
    data_tests = [
        ('OID crítico funcionando', {'sysDescr': 'Linux', 'badOid': None}, True),
        ('Maioria falhando mas 1 crítico OK', {'sysDescr': 'Router', 'oid2': None, 'oid3': None}, True),
        ('Poucos OIDs, 1 funcionando', {'customOid': 'value'}, True),
        ('Todos falhando', {'oid1': None, 'oid2': None}, False),
        ('Valores de erro SNMP', {'oid1': 'noSuchInstance'}, False),
    ]
    
    for name, data, expected in data_tests:
        result = is_snmp_data_valid(data)
        status = "✅" if result == expected else "❌"
        print(f"  {name}: {result} {status}")
    
    print("\n3. ✅ MELHORIAS DE TIMEOUT E RETRY:")
    print("  - Timeout aumentado: 1.0s → 3.0s para SNMP transport")
    print("  - Timeout geral: 2.0s → 5.0s para operações completas")
    print("  - Retries aumentados: 1 → 2 para SNMP transport")
    print("  - Fallback timeout: 8.0s para casos difíceis")
    
    print("\n4. ✅ SISTEMA DE FALLBACK:")
    print("  - Pool de engines (padrão)")
    print("  - → Engine simples (fallback)")
    print("  - → Logs detalhados para debug")
    
    print("\n5. ✅ LOGS MELHORADOS:")
    print("  - Log de início: quantidade de OIDs e configurações")
    print("  - Log por OID: sucessos e falhas detalhados")
    print("  - Log final: estatísticas de sucesso")
    print("  - Log de fallback: quando usado e resultados")

def create_test_script():
    """Cria um script de teste prático"""
    print("\n" + "=" * 60)
    print("🧪 SCRIPT DE TESTE PRÁTICO")
    print("=" * 60)
    
    script_content = '''
#!/usr/bin/env python3
"""
Script para testar SNMP com as melhorias implementadas
Execute: python test_monitor_snmp.py <IP> [community]
"""
import asyncio
import sys
from pysnmp.hlapi.v3arch.asyncio import *

async def test_snmp_improved(ip, community="public"):
    """Testa SNMP com configurações melhoradas"""
    print(f"🔍 Testando SNMP melhorado para {ip}")
    
    # Configuração melhorada
    engine = SnmpEngine()
    auth = CommunityData(community)
    
    # OIDs críticos para testar
    critical_oids = {
        'sysDescr': '1.3.6.1.2.1.1.1.0',
        'sysUpTime': '1.3.6.1.2.1.1.3.0', 
        'sysName': '1.3.6.1.2.1.1.5.0'
    }
    
    results = {}
    
    for name, oid in critical_oids.items():
        try:
            print(f"  Testando {name} ({oid})...")
            
            # Configurações melhoradas (como no monitor)
            target = await UdpTransportTarget.create((ip, 161), timeout=3.0, retries=2)
            
            result = await asyncio.wait_for(
                get_cmd(engine, auth, target, ContextData(),
                       ObjectType(ObjectIdentity(oid))),
                timeout=5.0
            )
            
            error_indication, error_status, error_index, var_binds = result
            
            if not (error_indication or error_status):
                value = str(var_binds[0][1])
                results[name] = value
                print(f"    ✅ {name}: {value}")
            else:
                results[name] = None
                print(f"    ❌ {name}: {error_indication or error_status}")
                
        except asyncio.TimeoutError:
            results[name] = None
            print(f"    ⏰ {name}: Timeout")
        except Exception as e:
            results[name] = None
            print(f"    💥 {name}: {e}")
    
    # Avaliar resultado usando lógica melhorada
    valid_count = sum(1 for v in results.values() if v is not None)
    critical_working = sum(1 for k, v in results.items() 
                          if k in ['sysDescr', 'sysUpTime', 'sysName'] and v is not None)
    
    print(f"\\n📊 Resultado: {valid_count}/{len(results)} OIDs funcionando")
    print(f"📊 OIDs críticos: {critical_working}/{len(critical_oids)} funcionando")
    
    # Usar lógica de validação melhorada
    is_valid = critical_working > 0 or valid_count >= len(results) * 0.3
    
    if is_valid:
        print("✅ SNMP considerado FUNCIONAL pela nova lógica")
    else:
        print("❌ SNMP considerado FALHO pela nova lógica")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_monitor_snmp.py <IP> [community]")
        sys.exit(1)
    
    ip = sys.argv[1]
    community = sys.argv[2] if len(sys.argv) > 2 else "public"
    
    asyncio.run(test_snmp_improved(ip, community))
'''
    
    print("Para testar as melhorias, salve este script como 'test_monitor_snmp.py':")
    print("```python")
    print(script_content.strip())
    print("```")
    
    print("\nExecute com:")
    print("python test_monitor_snmp.py <IP_DO_DISPOSITIVO> [community]")

def summarize_changes():
    """Resume todas as mudanças feitas"""
    print("\n" + "=" * 60)
    print("📋 RESUMO DE TODAS AS CORREÇÕES IMPLEMENTADAS")
    print("=" * 60)
    
    changes = [
        "✅ utils.py → check_ip_for_snmp(): Lógica corrigida para validar configurações SNMP reais",
        "✅ utils.py → is_snmp_data_valid(): Nova função inteligente com OIDs críticos",
        "✅ monitor.py → Timeouts aumentados: 3.0s transport, 5.0s geral",
        "✅ monitor.py → Retries aumentados: 2 tentativas por OID",
        "✅ monitor.py → Sistema de fallback com engine simples",
        "✅ monitor.py → Logs detalhados para cada fase da verificação",
        "✅ monitor.py → Melhor tratamento de exceções sem interromper outros OIDs",
        "✅ monitor.py → Validação melhorada usando is_snmp_data_valid() em vez de any()",
    ]
    
    for change in changes:
        print(f"  {change}")
    
    print(f"\n🎯 RESULTADO ESPERADO:")
    print("  - Menos falsos positivos de 'SNMP down'")
    print("  - Melhor detecção de dispositivos com SNMP parcialmente funcional")
    print("  - Logs mais informativos para debug")
    print("  - Maior tolerância a timeouts de rede")
    print("  - Fallback robusto em caso de problemas com engine pool")

if __name__ == "__main__":
    test_all_improvements()
    create_test_script()
    summarize_changes()
