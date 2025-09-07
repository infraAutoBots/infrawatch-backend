#!/usr/bin/env python3
"""
Script de exemplo demonstrando como usar os novos serviços de alerta.
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório api ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from alert_service import AlertService
from webhook_service import WebhookService
from alert_email_service import EmailService

def test_email_service():
    """Testa o serviço de email"""
    print("\n" + "="*60)
    print("📧 TESTANDO EMAIL SERVICE")
    print("="*60)
    
    email_service = EmailService()
    
    # Testar status
    status = email_service.get_status()
    print(f"Status do serviço: {status}")
    
    # Testar conexão
    connection_ok = email_service.test_connection()
    print(f"Conexão SMTP: {'✅ OK' if connection_ok else '❌ Falhou'}")
    
    if connection_ok:
        # Enviar email de teste
        test_emails = ["ndondadaniel2020@gmail.com"]  # Substitua pelo seu email
        
        success = email_service.send_alert_email(
            to_emails=test_emails,
            subject="Teste InfraWatch - Email Service",
            endpoint_name="Servidor de Teste",
            endpoint_ip="192.168.1.100",
            status="DOWN",
            timestamp=datetime.now(),
            additional_info="Este é um teste do novo EmailService"
        )
        
        print(f"Envio de email: {'✅ Sucesso' if success else '❌ Falhou'}")

def test_webhook_service():
    """Testa o serviço de webhook"""
    print("\n" + "="*60)
    print("🔗 TESTANDO WEBHOOK SERVICE")
    print("="*60)
    
    webhook_service = WebhookService()
    
    # Configurar URL de teste (substitua por uma URL real de webhook)
    test_webhook_url = "https://httpbin.org/post"  # URL de teste
    webhook_service.set_webhook_url(test_webhook_url)
    
    # Testar status
    status = webhook_service.get_status()
    print(f"Status do serviço: {status}")
    
    # Testar conexão
    connection_ok = webhook_service.test_connection()
    print(f"Conexão Webhook: {'✅ OK' if connection_ok else '❌ Falhou'}")
    
    if connection_ok:
        # Enviar webhook de alerta
        success = webhook_service.send_alert_webhook(
            webhook_url=test_webhook_url,
            endpoint_name="Servidor de Teste",
            endpoint_ip="192.168.1.100",
            status="DOWN",
            timestamp=datetime.now(),
            additional_info="Este é um teste do novo WebhookService"
        )
        
        print(f"Envio de webhook de alerta: {'✅ Sucesso' if success else '❌ Falhou'}")
        
        # Enviar webhook de status do sistema
        system_status = {
            "total_endpoints": 5,
            "up_endpoints": 3,
            "down_endpoints": 1,
            "snmp_down_endpoints": 1,
            "uptime": "2 days, 3 hours"
        }
        
        success = webhook_service.send_system_status_webhook(
            webhook_url=test_webhook_url,
            system_status=system_status,
            timestamp=datetime.now()
        )
        
        print(f"Envio de webhook de sistema: {'✅ Sucesso' if success else '❌ Falhou'}")

def test_alert_service():
    """Testa o serviço de alertas unificado"""
    print("\n" + "="*60)
    print("🚨 TESTANDO ALERT SERVICE UNIFICADO")
    print("="*60)
    
    # Inicializar sem sessão de banco (usará configurações de ambiente)
    alert_service = AlertService()
    
    # Testar status
    status = alert_service.get_service_status()
    print(f"Status dos serviços:")
    print(f"  Email: {status['email_service']}")
    print(f"  Webhook: {status['webhook_service']}")
    print(f"  Limites: {status['failure_thresholds']}")
    
    # Testar conectividade
    test_results = alert_service.test_services()
    print(f"\nTestes de conectividade:")
    print(f"  Email: {'✅ OK' if test_results['email_connection'] else '❌ Falhou'}")
    print(f"  Webhook: {'✅ OK' if test_results['webhook_connection'] else '❌ Falhou'}")
    
    # Testar critérios de envio
    print(f"\nTeste de critérios de envio:")
    print(f"  SNMP com 2 falhas: {'✅ Enviar' if alert_service.should_send_alert('snmp', 2) else '❌ Não enviar'}")
    print(f"  SNMP com 3 falhas: {'✅ Enviar' if alert_service.should_send_alert('snmp', 3) else '❌ Não enviar'}")
    print(f"  Ping com 4 falhas: {'✅ Enviar' if alert_service.should_send_alert('ping', 4) else '❌ Não enviar'}")
    print(f"  Ping com 5 falhas: {'✅ Enviar' if alert_service.should_send_alert('ping', 5) else '❌ Não enviar'}")
    
    # Enviar alerta de teste
    print(f"\nEnviando alerta de teste...")
    results = alert_service.send_test_alert()
    print(f"  Email: {'✅ Enviado' if results['email_sent'] else '❌ Falhou'}")
    print(f"  Webhook: {'✅ Enviado' if results['webhook_sent'] else '❌ Falhou'}")

def test_with_database():
    """Testa os serviços com conexão ao banco de dados"""
    print("\n" + "="*60)
    print("🗃️  TESTANDO COM BANCO DE DADOS")
    print("="*60)
    
    try:
        from models import db
        from sqlalchemy.orm import sessionmaker
        
        # Criar sessão do banco
        Session = sessionmaker(bind=db)
        session = Session()
        
        # Inicializar serviço com sessão do banco
        alert_service = AlertService(session)
        
        # Verificar se configurações foram carregadas do banco
        status = alert_service.get_service_status()
        
        print(f"Conexão com banco: {'✅ Conectado' if status['database_connected'] else '❌ Desconectado'}")
        print(f"Configurações carregadas do banco:")
        print(f"  Email configurado: {'✅ Sim' if status['email_service']['enabled'] else '❌ Não'}")
        print(f"  Webhook configurado: {'✅ Sim' if status['webhook_service']['enabled'] else '❌ Não'}")
        print(f"  Admins encontrados: {status['email_service']['admin_count']}")
        
        # Fechar sessão
        session.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar com banco: {e}")
        print("Certifique-se de que o banco está configurado e as migrações foram executadas")

def main():
    """Função principal"""
    print("🧪 TESTADOR DOS SERVIÇOS DE ALERTA - InfraWatch")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Testes básicos
        test_email_service()
        test_webhook_service() 
        test_alert_service()
        
        # Teste com banco de dados
        test_with_database()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS!")
        print("="*60)
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Configure as variáveis de ambiente para email (SMTP_SERVER, SMTP_USERNAME, etc.)")
        print("2. Execute as migrações do banco: alembic upgrade head")
        print("3. Configure webhooks e emails através da API /config")
        print("4. Integre o AlertService no seu sistema de monitoramento")
        
    except KeyboardInterrupt:
        print("\n❌ Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
