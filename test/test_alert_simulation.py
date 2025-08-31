#!/usr/bin/env python3
"""
Teste de simulação de alertas - InfraWatch
Simula mudanças de status para testar o envio de alertas
"""

import os
import sys
import time
from datetime import datetime

# Adicionar paths necessários
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'monitor'))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
monitor_env = os.path.join(os.path.dirname(__file__), 'monitor', '.env')
if os.path.exists(monitor_env):
    load_dotenv(monitor_env)

from notifications.alert_manager import AlertManager

def test_alert_simulation():
    """
    Simula cenários reais de mudança de status para testar alertas
    """
    print("🚀 InfraWatch - Simulação de Alertas")
    print("=" * 50)
    
    # Inicializar o gerenciador de alertas
    alert_manager = AlertManager()
    
    print(f"📧 Destinatários configurados: {alert_manager.default_recipients}")
    print(f"🔧 Serviço de email habilitado: {alert_manager.email_service.enabled}")
    
    if not alert_manager.default_recipients:
        print("❌ Nenhum destinatário configurado!")
        return
    
    if not alert_manager.email_service.enabled:
        print("❌ Serviço de email desabilitado!")
        return
    
    # Teste de conexão SMTP
    print("\n🔍 Testando conexão SMTP...")
    if not alert_manager.test_email_service():
        print("❌ Falha na conexão SMTP!")
        return
    print("✅ Conexão SMTP OK")
    
    # Simular endpoints de teste
    test_endpoints = [
        {"ip": "192.168.1.100", "name": "Servidor Web"},
        {"ip": "192.168.1.101", "name": "Servidor Database"},
        {"ip": "10.0.0.50", "name": "Router Principal"}
    ]
    
    print("\n" + "=" * 50)
    print("📊 SIMULAÇÃO DE CENÁRIOS DE ALERTA")
    print("=" * 50)
    
    for i, endpoint in enumerate(test_endpoints, 1):
        ip = endpoint["ip"]
        name = endpoint["name"]
        
        print(f"\n🔄 Cenário {i}: {name} ({ip})")
        print("-" * 30)
        
        # Simular endpoint inicialmente UP
        print("   1️⃣ Status inicial: UP")
        alert_manager.check_and_send_alerts(ip, True, {
            "name": name,
            "snmp_data": {
                "sysDescr": f"Sistema {name}",
                "sysName": name.replace(" ", "-").lower()
            }
        })
        
        time.sleep(2)  # Pequena pausa
        
        # Simular endpoint ficando DOWN
        print("   2️⃣ Mudança para: DOWN (🚨 DEVE ENVIAR ALERTA)")
        alert_manager.check_and_send_alerts(ip, False, {
            "name": name,
            "snmp_data": {
                "sysDescr": f"Sistema {name}",
                "sysName": name.replace(" ", "-").lower()
            }
        })
        
        time.sleep(3)  # Pausa para processamento do email
        
        # Simular endpoint voltando UP
        print("   3️⃣ Recuperação para: UP (🎉 DEVE ENVIAR ALERTA DE RECUPERAÇÃO)")
        alert_manager.check_and_send_alerts(ip, True, {
            "name": name,
            "snmp_data": {
                "sysDescr": f"Sistema {name}",
                "sysName": name.replace(" ", "-").lower(),
                "sysUpTime": "2 days, 14:30:25"
            }
        })
        
        time.sleep(3)  # Pausa para processamento do email
        
        print(f"   ✅ Cenário {i} concluído")
    
    print("\n" + "=" * 50)
    print("🎯 TESTE DE EMAIL DIRETO")
    print("=" * 50)
    
    # Enviar um email de teste direto
    test_email = input("\n📧 Digite um email para teste direto (ou Enter para usar padrão): ").strip()
    if not test_email:
        test_email = alert_manager.default_recipients[0]
    
    print(f"📤 Enviando email de teste para: {test_email}")
    
    if alert_manager.send_test_alert(test_email):
        print("✅ Email de teste enviado com sucesso!")
    else:
        print("❌ Falha ao enviar email de teste!")
    
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    print(f"✅ {len(test_endpoints)} cenários de mudança de status simulados")
    print(f"✅ {len(test_endpoints) * 2} alertas deveriam ter sido enviados")
    print("✅ 1 email de teste direto enviado")
    print(f"📧 Total esperado: {len(test_endpoints) * 2 + 1} emails")
    print("\n🔍 Verifique sua caixa de entrada nos emails configurados:")
    for email in alert_manager.default_recipients:
        print(f"   📬 {email}")
    
    print("\n🎉 Simulação concluída!")
    print("💡 Se não recebeu os emails, verifique:")
    print("   - Pasta de spam/lixo eletrônico")
    print("   - Configurações SMTP no arquivo .env")
    print("   - Credenciais de email (senha de app para Gmail)")

if __name__ == "__main__":
    test_alert_simulation()