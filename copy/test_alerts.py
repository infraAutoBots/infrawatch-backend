#!/usr/bin/env python3
"""
Script de teste para o sistema de alertas do InfraWatch
"""

import os
from alert_email_service import EmailService
from alert_manager import AlertManager
from dotenv import load_dotenv



load_dotenv()


def test_email_service():
    """Testa o serviço de email"""
    print("🧪 Testando serviço de email...")
    
    email_service = EmailService()
    
    print(f"   SMTP Server: {email_service.smtp_server}:{email_service.smtp_port}")
    print(f"   Username: {email_service.smtp_username}")
    print(f"   From Email: {email_service.from_email}")
    print(f"   Enabled: {email_service.enabled}")

    if email_service.enabled:
        print("   Testando conexão SMTP...")
        if email_service.test_connection():
            print("   ✅ Conexão SMTP OK")
            return True
        else:
            print("   ❌ Falha na conexão SMTP")
            return False
    else:
        print("   ⚠️  Serviço de email desabilitado")
        return False

def test_alert_manager():
    """Testa o gerenciador de alertas"""
    print("\n🧪 Testando gerenciador de alertas...")
    
    alert_manager = AlertManager()
    
    print(f"   Destinatários padrão: {alert_manager.default_recipients}")
    
    # Simula mudança de status
    print("   Simulando mudança de status UP -> DOWN...")
    alert_manager.check_and_send_alerts("192.168.1.100", True)  # Primeiro status UP
    alert_manager.check_and_send_alerts("192.168.1.100", False)  # Mudança para DOWN
    
    print("   Simulando mudança de status DOWN -> UP...")
    alert_manager.check_and_send_alerts("192.168.1.100", True)  # Mudança para UP
    
    return True

def send_test_email():
    """Envia um email de teste"""
    print("\n📧 Enviando email de teste...")
    
    test_email = input("Digite o email para teste (ou Enter para usar padrão): ").strip()
    if not test_email:
        test_email = os.getenv("DEFAULT_ALERT_RECIPIENTS", "").split(",")[0].strip()
        if not test_email:
            print("❌ Nenhum email configurado para teste")
            return False
    
    alert_manager = AlertManager()
    
    if alert_manager.send_test_alert(test_email):
        print(f"✅ Email de teste enviado para {test_email}")
        return True
    else:
        print(f"❌ Falha ao enviar email para {test_email}")
        return False

def check_environment():
    """Verifica as variáveis de ambiente"""
    print("🔧 Verificando configuração do ambiente...")
    
    required_vars = [
        "EMAIL_ALERTS_ENABLED",
        "SMTP_SERVER", 
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "DEFAULT_ALERT_RECIPIENTS"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mascarar senha
            display_value = "***" if "PASSWORD" in var else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NÃO CONFIGURADO")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Variáveis faltando: {', '.join(missing_vars)}")
        print("   Configure no arquivo .env do módulo monitor/")
        return False
    
    return True

def main():
    """Função principal"""
    print("🚀 InfraWatch - Teste do Sistema de Alertas")
    print("=" * 50)
    
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    
    # Tentar carregar .env do monitor
    monitor_env = os.path.join(os.path.dirname(__file__), 'monitor', '.env')
    if os.path.exists(monitor_env):
        load_dotenv(monitor_env)
        print(f"📁 Carregado: {monitor_env}")
    else:
        print(f"⚠️  Arquivo .env não encontrado em: {monitor_env}")
        print("   Copie monitor/.env.example para monitor/.env e configure")
    
    # Verificar configuração
    if not check_environment():
        print("\n❌ Configuração incompleta. Configure as variáveis de ambiente primeiro.")
        return
    
    # Testes
    print("\n" + "=" * 50)
    
    # Teste 1: Serviço de email
    email_ok = test_email_service()
    
    # Teste 2: Gerenciador de alertas
    alert_ok = test_alert_manager()
    
    # Teste 3: Email de teste (opcional)
    if email_ok:
        send_test = input("\n📧 Deseja enviar um email de teste? (s/N): ").strip().lower()
        if send_test in ['s', 'sim', 'y', 'yes']:
            send_test_email()
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")
    
    if email_ok and alert_ok:
        print("🎉 Sistema de alertas está funcionando corretamente!")
    else:
        print("⚠️  Alguns problemas foram encontrados. Verifique a configuração.")

if __name__ == "__main__":
    main()