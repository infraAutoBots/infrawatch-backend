#!/usr/bin/env python3
"""
Análise simplificada dos problemas na verificação SNMP
"""

def analyze_check_ip_for_snmp():
    """Analisa a função check_ip_for_snmp"""
    print("=== PROBLEMA 1: Lógica incorreta em check_ip_for_snmp ===")
    
    # Simulação da função atual
    def check_ip_for_snmp_current(host):
        """Função atual com lógica problemática"""
        if (host and host.get('ip') and host.get('interval') and not host.get('port') 
            and not host.get('version') and not host.get('community')
            and not host.get('user') and not host.get('authKey') 
            and not host.get('privKey')):
            return False
        return True
    
    # Teste com diferentes cenários
    scenarios = [
        {
            'name': 'Host só com ping (sem SNMP)',
            'host': {'ip': '192.168.1.1', 'interval': 30},
            'should_have_snmp': False
        },
        {
            'name': 'Host com SNMP v2c',
            'host': {'ip': '192.168.1.2', 'interval': 30, 'version': '2c', 'community': 'public', 'port': 161},
            'should_have_snmp': True
        },
        {
            'name': 'Host com SNMP v3',
            'host': {'ip': '192.168.1.3', 'interval': 30, 'version': '3', 'user': 'admin', 'authKey': 'auth123', 'port': 161},
            'should_have_snmp': True
        }
    ]
    
    for scenario in scenarios:
        result = check_ip_for_snmp_current(scenario['host'])
        expected = scenario['should_have_snmp']
        status = "✅ CORRETO" if result == expected else "❌ ERRO"
        
        print(f"{scenario['name']}: {result} (esperado: {expected}) {status}")
    
    print("\nA função atual retorna True para hosts SEM configuração SNMP!")
    print("Isso causa tentativas desnecessárias de SNMP em hosts que só fazem ping.")

def analyze_snmp_validation():
    """Analisa como os dados SNMP são validados"""
    print("\n=== PROBLEMA 2: Validação de dados SNMP ===")
    
    # O sistema usa: if snmp_data and any(snmp_data.values())
    test_cases = [
        {'name': 'Dados válidos', 'data': {'sysDescr': 'Linux', 'sysUpTime': '12345'}, 'expected': True},
        {'name': 'Dados com None', 'data': {'sysDescr': None, 'sysUpTime': None}, 'expected': False},
        {'name': 'Dados mistos', 'data': {'sysDescr': 'Linux', 'sysUpTime': None}, 'expected': True},
        {'name': 'Dados vazios', 'data': {}, 'expected': False},
        {'name': 'Dados com strings vazias', 'data': {'sysDescr': '', 'sysUpTime': ''}, 'expected': False},
        {'name': 'Dados com "0" (valor válido)', 'data': {'sysDescr': 'Linux', 'hrProcessorLoad': '0'}, 'expected': True},
    ]
    
    for case in test_cases:
        data = case['data']
        result = bool(data and any(data.values()))
        expected = case['expected']
        status = "✅" if result == expected else "❌"
        
        print(f"{case['name']}: {result} (esperado: {expected}) {status}")

def proposed_fixes():
    """Propõe correções para os problemas"""
    print("\n=== SOLUÇÕES PROPOSTAS ===")
    
    print("1. CORRIGIR check_ip_for_snmp:")
    print("""
def check_ip_for_snmp(host: HostStatus):
    \"\"\"Verifica se o host tem configuração SNMP válida\"\"\"
    if not host or not host.ip:
        return False
    
    # Verifica se tem pelo menos uma configuração SNMP válida
    has_v1_v2c = host.version in ["1", "2c"] and host.community
    has_v3 = host.version == "3" and host.user
    
    return has_v1_v2c or has_v3
    """)
    
    print("2. MELHORAR validação de dados SNMP:")
    print("""
def is_snmp_data_valid(snmp_data):
    \"\"\"Valida se os dados SNMP são úteis\"\"\"
    if not snmp_data:
        return False
    
    # Conta valores não-None e não-vazios
    valid_values = [v for v in snmp_data.values() 
                   if v is not None and str(v).strip() != '']
    
    # Considera válido se pelo menos 50% dos OIDs retornaram dados
    return len(valid_values) >= len(snmp_data) * 0.5
    """)
    
    print("3. ADICIONAR logs detalhados para debug:")
    print("""
# No _perform_snmp_check, adicionar:
if self.logger:
    successful_oids = sum(1 for v in result.values() if v is not None)
    total_oids = len(result)
    logger.debug(f"SNMP {ip}: {successful_oids}/{total_oids} OIDs retornaram dados")
    """)

if __name__ == "__main__":
    print("🔍 ANÁLISE DOS PROBLEMAS NO MONITOR SNMP")
    print("=" * 60)
    
    analyze_check_ip_for_snmp()
    analyze_snmp_validation()
    proposed_fixes()
