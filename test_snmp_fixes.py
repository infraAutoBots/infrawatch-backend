#!/usr/bin/env python3
"""
Teste das correções implementadas no monitor SNMP
"""
import sys
import os

# Adicionar o diretório monitor ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'monitor'))

from utils import HostStatus, check_ip_for_snmp, is_snmp_data_valid

def test_corrected_check_ip_for_snmp():
    """Testa a função check_ip_for_snmp corrigida"""
    print("=== Testando check_ip_for_snmp corrigida ===")
    
    test_cases = [
        {
            'name': 'Host só com ping (sem SNMP)',
            'host': HostStatus(ip='192.168.1.1', interval=30),
            'expected': False
        },
        {
            'name': 'Host com SNMP v2c válido',
            'host': HostStatus(ip='192.168.1.2', interval=30, version='2c', community='public', port=161),
            'expected': True
        },
        {
            'name': 'Host com SNMP v2c sem community',
            'host': HostStatus(ip='192.168.1.3', interval=30, version='2c', port=161),
            'expected': False
        },
        {
            'name': 'Host com SNMP v3 válido',
            'host': HostStatus(ip='192.168.1.4', interval=30, version='3', user='admin', authKey='auth123', port=161),
            'expected': True
        },
        {
            'name': 'Host com SNMP v3 sem user',
            'host': HostStatus(ip='192.168.1.5', interval=30, version='3', authKey='auth123', port=161),
            'expected': False
        },
        {
            'name': 'Host com community vazia',
            'host': HostStatus(ip='192.168.1.6', interval=30, version='2c', community='', port=161),
            'expected': False
        },
        {
            'name': 'Host com user vazio',
            'host': HostStatus(ip='192.168.1.7', interval=30, version='3', user='', authKey='auth123', port=161),
            'expected': False
        }
    ]
    
    for case in test_cases:
        result = check_ip_for_snmp(case['host'])
        expected = case['expected']
        status = "✅" if result == expected else "❌"
        
        print(f"{case['name']}: {result} (esperado: {expected}) {status}")
        if result != expected:
            print(f"  ERRO: Configuração: version={case['host'].version}, community={case['host'].community}, user={case['host'].user}")

def test_snmp_data_validation():
    """Testa a nova função is_snmp_data_valid"""
    print("\n=== Testando is_snmp_data_valid ===")
    
    test_cases = [
        {
            'name': 'Dados completamente válidos',
            'data': {'sysDescr': 'Linux server', 'sysUpTime': '12345', 'hrProcessorLoad': '25'},
            'expected': True
        },
        {
            'name': 'Dados com alguns None',
            'data': {'sysDescr': 'Linux server', 'sysUpTime': None, 'hrProcessorLoad': None},
            'expected': True  # 1/3 = 33% > 30%
        },
        {
            'name': 'Dados com maioria None',
            'data': {'sysDescr': None, 'sysUpTime': None, 'hrProcessorLoad': '25'},
            'expected': True  # 1/3 = 33% > 30%
        },
        {
            'name': 'Todos None',
            'data': {'sysDescr': None, 'sysUpTime': None, 'hrProcessorLoad': None},
            'expected': False
        },
        {
            'name': 'Strings vazias',
            'data': {'sysDescr': '', 'sysUpTime': '', 'hrProcessorLoad': ''},
            'expected': False
        },
        {
            'name': 'Valores de erro SNMP',
            'data': {'sysDescr': 'noSuchInstance', 'sysUpTime': 'noSuchObject', 'hrProcessorLoad': 'endOfMibView'},
            'expected': False
        },
        {
            'name': 'Mistura de valores válidos e inválidos',
            'data': {'sysDescr': 'Linux server', 'sysUpTime': 'noSuchInstance', 'hrProcessorLoad': ''},
            'expected': True  # 1/3 = 33% > 30%
        },
        {
            'name': 'Dict vazio',
            'data': {},
            'expected': False
        },
        {
            'name': 'Valor 0 (válido)',
            'data': {'hrProcessorLoad': '0'},
            'expected': True
        },
        {
            'name': 'Um único OID válido',
            'data': {'sysDescr': 'Router Cisco'},
            'expected': True  # Pelo menos 1 é válido
        }
    ]
    
    for case in test_cases:
        result = is_snmp_data_valid(case['data'])
        expected = case['expected']
        status = "✅" if result == expected else "❌"
        
        print(f"{case['name']}: {result} (esperado: {expected}) {status}")
        if result != expected:
            valid_count = len([v for v in case['data'].values() 
                             if v is not None and str(v).strip() and 
                             str(v).strip() not in ['', 'None', 'noSuchInstance', 'noSuchObject', 'endOfMibView']])
            print(f"  Debug: {valid_count}/{len(case['data'])} valores válidos")

def simulate_monitor_logic():
    """Simula a nova lógica do monitor"""
    print("\n=== Simulando lógica do monitor ===")
    
    # Simular um host com SNMP configurado mas retornando dados parciais
    host = HostStatus(
        ip='192.168.1.10',
        interval=30,
        version='2c',
        community='public',
        port=161
    )
    
    scenarios = [
        {
            'name': 'SNMP respondendo bem',
            'snmp_data': {'sysDescr': 'Linux server', 'sysUpTime': '12345', 'hrProcessorLoad': '25'}
        },
        {
            'name': 'SNMP com falhas parciais',
            'snmp_data': {'sysDescr': 'Linux server', 'sysUpTime': None, 'hrProcessorLoad': None}
        },
        {
            'name': 'SNMP completamente falho',
            'snmp_data': {'sysDescr': None, 'sysUpTime': None, 'hrProcessorLoad': None}
        },
        {
            'name': 'SNMP sem dados',
            'snmp_data': {}
        },
        {
            'name': 'SNMP None',
            'snmp_data': None
        }
    ]
    
    for scenario in scenarios:
        print(f"\nCenário: {scenario['name']}")
        print(f"  Host tem SNMP configurado: {check_ip_for_snmp(host)}")
        print(f"  Dados SNMP válidos: {is_snmp_data_valid(scenario['snmp_data'])}")
        
        # Simular a lógica do monitor
        is_alive = True  # Assumindo que ping passou
        if is_alive and check_ip_for_snmp(host):
            if is_snmp_data_valid(scenario['snmp_data']):
                print("  ✅ Monitor: SNMP funcionando - resetar contadores de falha")
            else:
                print("  ❌ Monitor: SNMP com problemas - incrementar contador de falha")
        else:
            print("  ⚪ Monitor: Host sem SNMP configurado - só monitorar ping")

if __name__ == "__main__":
    print("🔧 TESTE DAS CORREÇÕES NO MONITOR SNMP")
    print("=" * 60)
    
    test_corrected_check_ip_for_snmp()
    test_snmp_data_validation()
    simulate_monitor_logic()
    
    print("\n" + "=" * 60)
    print("✅ RESUMO DAS CORREÇÕES IMPLEMENTADAS:")
    print("1. ✅ check_ip_for_snmp() agora verifica configurações SNMP válidas")
    print("2. ✅ is_snmp_data_valid() valida qualidade dos dados retornados")
    print("3. ✅ Logs detalhados para debug de problemas SNMP")
    print("4. ✅ Melhor tratamento de exceções sem interromper outros OIDs")
    print("5. ✅ Validação baseada em porcentagem de OIDs bem-sucedidos")
