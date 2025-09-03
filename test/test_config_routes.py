#!/usr/bin/env python3
"""
Script para testar as rotas de configuração da API InfraWatch
Execute com: python test_config_routes.py
"""

import requests
import json
import sys
from pprint import pprint
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
CONFIG_ENDPOINT = f"{API_BASE}/config"

# Credenciais de teste (assumindo que existe um admin)
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class ConfigAPITester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
    
    def authenticate(self):
        """Faz login e obtém o token de autenticação"""
        try:
            response = self.session.post(AUTH_ENDPOINT, json=TEST_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Autenticação realizada com sucesso")
                return True
            else:
                print(f"❌ Falha na autenticação: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão durante autenticação: {e}")
            return False

#!/usr/bin/env python3
"""
Script para testar as rotas de configuração da API InfraWatch
Execute com: python test_config_routes.py
"""

import requests
import json
import sys
from pprint import pprint
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
CONFIG_ENDPOINT = f"{API_BASE}/config"

# Credenciais de teste (assumindo que existe um admin)
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class ConfigAPITester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
    
    def authenticate(self):
        """Faz login e obtém o token de autenticação"""
        try:
            response = self.session.post(AUTH_ENDPOINT, json=TEST_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Autenticação realizada com sucesso")
                return True
            else:
                print(f"❌ Falha na autenticação: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão durante autenticação: {e}")
            return False

    # ========== TESTES DE WEBHOOK ==========
    
    def test_create_webhook(self):
        """Testa a criação de webhook"""
        print("\n➕ Testando criação de webhook...")
        
        test_webhook = {
            "url": f"https://hooks.slack.com/services/TEST/{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "active": True
        }
        
        try:
            response = self.session.post(f"{CONFIG_ENDPOINT}/webhook", json=test_webhook)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook criado com sucesso")
                print(f"   ID: {data.get('id')}")
                print(f"   URL: {data.get('url')}")
                return data.get('id')
            else:
                print(f"❌ Falha na criação: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na criação de webhook: {e}")
            return None
    
    def test_list_webhooks(self):
        """Testa a listagem de webhooks"""
        print("\n🔍 Testando listagem de webhooks...")
        
        try:
            response = self.session.get(f"{CONFIG_ENDPOINT}/webhook")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Listagem funcionando")
                print(f"   Webhooks encontrados: {len(data)}")
                
                for webhook in data:
                    print(f"   ID: {webhook.get('id')}, URL: {webhook.get('url')}, Ativo: {webhook.get('active')}")
                
                return True
            else:
                print(f"❌ Falha na listagem: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de listagem: {e}")
            return False
    
    def test_get_webhook(self, webhook_id):
        """Testa a obtenção de um webhook específico"""
        if not webhook_id:
            return False
            
        print(f"\n🔗 Testando obtenção do webhook {webhook_id}...")
        
        try:
            response = self.session.get(f"{CONFIG_ENDPOINT}/webhook/{webhook_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook obtido com sucesso")
                print(f"   URL: {data.get('url')}")
                print(f"   Ativo: {data.get('active')}")
                return True
            else:
                print(f"❌ Falha ao obter webhook: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter webhook: {e}")
            return False
    
    def test_update_webhook(self, webhook_id):
        """Testa a atualização de webhook"""
        if not webhook_id:
            return False
            
        print(f"\n✏️ Testando atualização do webhook {webhook_id}...")
        
        update_data = {
            "url": "https://hooks.slack.com/services/UPDATED/WEBHOOK/URL",
            "active": False
        }
        
        try:
            response = self.session.put(f"{CONFIG_ENDPOINT}/webhook/{webhook_id}", json=update_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook atualizado com sucesso")
                print(f"   Nova URL: {data.get('url')}")
                print(f"   Ativo: {data.get('active')}")
                return True
            else:
                print(f"❌ Falha na atualização: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            return False
    
    def test_delete_webhook(self, webhook_id):
        """Testa a exclusão de webhook"""
        if not webhook_id:
            return False
            
        print(f"\n🗑️ Testando exclusão do webhook {webhook_id}...")
        
        try:
            response = self.session.delete(f"{CONFIG_ENDPOINT}/webhook/{webhook_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Webhook excluído com sucesso")
                return True
            else:
                print(f"❌ Falha na exclusão: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na exclusão: {e}")
            return False

    # ========== TESTES DE EMAIL ==========
    
    def test_create_email_config(self):
        """Testa a criação de configuração de email"""
        print("\n➕ Testando criação de configuração de email...")
        
        test_email = {
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@company.com",
            "password": "senha_teste_123",
            "port": 587,
            "server": "smtp.gmail.com",
            "active": True
        }
        
        try:
            response = self.session.post(f"{CONFIG_ENDPOINT}/email", json=test_email)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuração de email criada com sucesso")
                print(f"   ID: {data.get('id')}")
                print(f"   Email: {data.get('email')}")
                print(f"   Servidor: {data.get('server')}:{data.get('port')}")
                return data.get('id')
            else:
                print(f"❌ Falha na criação: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na criação de email: {e}")
            return None
    
    def test_list_email_configs(self):
        """Testa a listagem de configurações de email"""
        print("\n📧 Testando listagem de configurações de email...")
        
        try:
            response = self.session.get(f"{CONFIG_ENDPOINT}/email")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Listagem funcionando")
                print(f"   Configurações encontradas: {len(data)}")
                
                for config in data:
                    print(f"   ID: {config.get('id')}, Email: {config.get('email')}, Servidor: {config.get('server')}")
                
                return True
            else:
                print(f"❌ Falha na listagem: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de listagem: {e}")
            return False
    
    def test_update_email_config(self, email_id):
        """Testa a atualização de configuração de email"""
        if not email_id:
            return False
            
        print(f"\n✏️ Testando atualização da configuração de email {email_id}...")
        
        update_data = {
            "email": "updated_email@company.com",
            "port": 465,
            "server": "smtp.outlook.com"
        }
        
        try:
            response = self.session.put(f"{CONFIG_ENDPOINT}/email/{email_id}", json=update_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuração de email atualizada com sucesso")
                print(f"   Novo email: {data.get('email')}")
                print(f"   Novo servidor: {data.get('server')}:{data.get('port')}")
                return True
            else:
                print(f"❌ Falha na atualização: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            return False
    
    def test_delete_email_config(self, email_id):
        """Testa a exclusão de configuração de email"""
        if not email_id:
            return False
            
        print(f"\n🗑️ Testando exclusão da configuração de email {email_id}...")
        
        try:
            response = self.session.delete(f"{CONFIG_ENDPOINT}/email/{email_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Configuração de email excluída com sucesso")
                return True
            else:
                print(f"❌ Falha na exclusão: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na exclusão: {e}")
            return False

    # ========== TESTES DE LIMITES DE FALHAS ==========
    
    def test_create_failure_threshold(self):
        """Testa a criação de configuração de limites de falhas"""
        print("\n➕ Testando criação de configuração de limites de falhas...")
        
        test_threshold = {
            "consecutive_snmp_failures": 3,
            "consecutive_ping_failures": 5,
            "active": True
        }
        
        try:
            response = self.session.post(f"{CONFIG_ENDPOINT}/failure-threshold", json=test_threshold)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuração de limites criada com sucesso")
                print(f"   ID: {data.get('id')}")
                print(f"   Falhas SNMP: {data.get('consecutive_snmp_failures')}")
                print(f"   Falhas Ping: {data.get('consecutive_ping_failures')}")
                return data.get('id')
            else:
                print(f"❌ Falha na criação: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na criação de limites: {e}")
            return None
    
    def test_list_failure_thresholds(self):
        """Testa a listagem de configurações de limites"""
        print("\n⚠️ Testando listagem de configurações de limites...")
        
        try:
            response = self.session.get(f"{CONFIG_ENDPOINT}/failure-threshold")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Listagem funcionando")
                print(f"   Configurações encontradas: {len(data)}")
                
                for config in data:
                    print(f"   ID: {config.get('id')}, SNMP: {config.get('consecutive_snmp_failures')}, Ping: {config.get('consecutive_ping_failures')}")
                
                return True
            else:
                print(f"❌ Falha na listagem: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de listagem: {e}")
            return False
    
    def test_update_failure_threshold(self, threshold_id):
        """Testa a atualização de configuração de limites"""
        if not threshold_id:
            return False
            
        print(f"\n✏️ Testando atualização da configuração de limites {threshold_id}...")
        
        update_data = {
            "consecutive_snmp_failures": 5,
            "consecutive_ping_failures": 3
        }
        
        try:
            response = self.session.put(f"{CONFIG_ENDPOINT}/failure-threshold/{threshold_id}", json=update_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configuração de limites atualizada com sucesso")
                print(f"   Novas falhas SNMP: {data.get('consecutive_snmp_failures')}")
                print(f"   Novas falhas Ping: {data.get('consecutive_ping_failures')}")
                return True
            else:
                print(f"❌ Falha na atualização: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            return False
    
    def test_delete_failure_threshold(self, threshold_id):
        """Testa a exclusão de configuração de limites"""
        if not threshold_id:
            return False
            
        print(f"\n🗑️ Testando exclusão da configuração de limites {threshold_id}...")
        
        try:
            response = self.session.delete(f"{CONFIG_ENDPOINT}/failure-threshold/{threshold_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Configuração de limites excluída com sucesso")
                return True
            else:
                print(f"❌ Falha na exclusão: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na exclusão: {e}")
            return False

    # ========== TESTE DE CONFIGURAÇÕES ATIVAS ==========
    
    def test_get_active_configs(self):
        """Testa a obtenção de configurações ativas"""
        print("\n🔍 Testando obtenção de configurações ativas...")
        
        try:
            response = self.session.get(f"{CONFIG_ENDPOINT}/active")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Configurações ativas obtidas com sucesso")
                
                webhook = data.get("webhook")
                email = data.get("email")
                threshold = data.get("failure_threshold")
                
                print(f"   Webhook ativo: {'Sim' if webhook else 'Não'}")
                print(f"   Email ativo: {'Sim' if email else 'Não'}")
                print(f"   Limites ativos: {'Sim' if threshold else 'Não'}")
                
                return True
            else:
                print(f"❌ Falha ao obter configurações ativas: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter configurações ativas: {e}")
            return False

    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes da API de Configuração...")
        print(f"🔗 API Base: {API_BASE}")
        
        # Autenticar
        if not self.authenticate():
            print("\n❌ Não foi possível autenticar. Verifique se a API está rodando e as credenciais estão corretas.")
            return False
        
        # Executar testes
        results = []
        
        # ========== TESTES DE WEBHOOK ==========
        print("\n" + "="*60)
        print("🔗 EXECUTANDO TESTES DE WEBHOOK")
        print("="*60)
        
        # Teste de listagem de webhooks
        results.append(("Listar Webhooks", self.test_list_webhooks()))
        
        # Teste de criação de webhook
        webhook_id = self.test_create_webhook()
        results.append(("Criar Webhook", webhook_id is not None))
        
        if webhook_id:
            # Testes que dependem de ter um webhook criado
            results.append(("Obter Webhook", self.test_get_webhook(webhook_id)))
            results.append(("Atualizar Webhook", self.test_update_webhook(webhook_id)))
            results.append(("Excluir Webhook", self.test_delete_webhook(webhook_id)))

        # ========== TESTES DE EMAIL ==========
        print("\n" + "="*60)
        print("📧 EXECUTANDO TESTES DE EMAIL")
        print("="*60)
        
        # Teste de listagem de emails
        results.append(("Listar Emails", self.test_list_email_configs()))
        
        # Teste de criação de email
        email_id = self.test_create_email_config()
        results.append(("Criar Email", email_id is not None))
        
        if email_id:
            # Testes que dependem de ter um email criado
            results.append(("Atualizar Email", self.test_update_email_config(email_id)))
            results.append(("Excluir Email", self.test_delete_email_config(email_id)))

        # ========== TESTES DE LIMITES ==========
        print("\n" + "="*60)
        print("⚠️ EXECUTANDO TESTES DE LIMITES DE FALHAS")
        print("="*60)
        
        # Teste de listagem de limites
        results.append(("Listar Limites", self.test_list_failure_thresholds()))
        
        # Teste de criação de limites
        threshold_id = self.test_create_failure_threshold()
        results.append(("Criar Limites", threshold_id is not None))
        
        if threshold_id:
            # Testes que dependem de ter limites criados
            results.append(("Atualizar Limites", self.test_update_failure_threshold(threshold_id)))
            results.append(("Excluir Limites", self.test_delete_failure_threshold(threshold_id)))

        # ========== TESTE DE CONFIGURAÇÕES ATIVAS ==========
        print("\n" + "="*60)
        print("🔍 EXECUTANDO TESTE DE CONFIGURAÇÕES ATIVAS")
        print("="*60)
        
        results.append(("Configurações Ativas", self.test_get_active_configs()))

        # Relatório final
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DOS TESTES")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name:<25} {status}")
            if result:
                passed += 1
        
        print(f"\n📈 Resumo: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 Todos os testes passaram com sucesso!")
        else:
            print("⚠️ Alguns testes falharam. Verifique a implementação.")
        
        return passed == total


def main():
    """Função principal"""
    print("🧪 Testador da API de Configuração - InfraWatch")
    print("-" * 60)
    
    tester = ConfigAPITester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
