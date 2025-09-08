#!/usr/bin/env python3
"""
Script para testar as rotas de alertas da API InfraWatch
Execute com: python test_alerts_routes.py
"""

import requests
import time
import json
from pprint import pprint
from datetime import datetime

API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login-form"
ALERTS_ENDPOINT = f"{API_BASE}/alerts"

# Credenciais de teste
TEST_CREDENTIALS = {
    "username": "admin@infrawatch.com",
    "password": "admin123"
}

class AlertsRouteTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.created_alert_id = None

    def retry_request(self, method, url, max_retries=3, **kwargs):
        """Executa requisição com retry em caso de falha"""
        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, **kwargs)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, **kwargs)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, **kwargs)
                else:
                    return None
                
                # Se não for erro de conexão, retornar
                if response.status_code != 500:
                    return response
                    
            except Exception as e:
                print(f"   ⚠️ Tentativa {attempt + 1} falhou: {e}")
                
            if attempt < max_retries - 1:
                time.sleep(1)  # Aguardar 1 segundo antes de tentar novamente
                
        return None


    def authenticate(self):
        """Realiza autenticação e obtém token"""
        print("🔐 Fazendo autenticação...")
        data = {"username": TEST_CREDENTIALS["username"], "password": TEST_CREDENTIALS["password"]}
        response = self.session.post(AUTH_ENDPOINT, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.token = token_data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Autenticação bem-sucedida. Token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Falha na autenticação: {response.text}")
            return False

    def test_create_alert(self):
        """Testa criação de alerta"""
        print("\n📝 Testando criação de alerta...")
        
        alert_data = {
            "title": f"Teste de Alerta - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Este é um alerta de teste criado automaticamente",
            "severity": "medium",
            "category": "infrastructure",
            "system": "test-system-001",
            "impact": "low",
            "assignee": "admin",
            "id_endpoint": 1
        }
        
        response = self.session.post(ALERTS_ENDPOINT, json=alert_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:  # API retorna 200, não 201
            created_alert = response.json()
            self.created_alert_id = created_alert.get("id")
            print("✅ Alerta criado com sucesso!")
            print(f"   ID: {created_alert.get('id')}")
            print(f"   Título: {created_alert.get('title')}")
            print(f"   Status: {created_alert.get('status')}")
            print(f"   Criado em: {created_alert.get('created_at')}")
            return True
        else:
            print(f"❌ Falha na criação do alerta: {response.text}")
            return False

    def test_list_alerts(self):
        """Testa listagem de alertas"""
        print("\n📋 Testando listagem de alertas...")
        
        # Teste sem parâmetros
        response = self.session.get(ALERTS_ENDPOINT)
        print(f"Status (sem parâmetros): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Listagem básica bem-sucedida!")
            print(f"   Total de alertas: {data.get('pagination', {}).get('total', 0)}")
            print(f"   Página atual: {data.get('pagination', {}).get('page', 1)}")
            print(f"   Alertas retornados: {len(data.get('data', []))}")
            
            # Exibir primeiro alerta se existir
            if data.get('data'):
                first_alert = data['data'][0]
                print(f"   Primeiro alerta - ID: {first_alert.get('id')}, Título: {first_alert.get('title')}")
        else:
            print(f"❌ Falha na listagem: {response.text}")
            return False

        # Teste com parâmetros de paginação e ordenação
        params = {
            "page": 1,
            "size": 5,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        response = self.session.get(ALERTS_ENDPOINT, params=params)
        print(f"Status (com parâmetros): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Listagem com parâmetros bem-sucedida!")
            print(f"   Total: {data.get('pagination', {}).get('total', 0)}")
            print(f"   Páginas: {data.get('pagination', {}).get('pages', 0)}")
            return True
        else:
            print(f"❌ Falha na listagem com parâmetros: {response.text}")
            return False

    def test_get_alert_details(self):
        """Testa obtenção de detalhes de um alerta"""
        print("\n🔍 Testando detalhes de alerta...")
        
        if not self.created_alert_id:
            print("⚠️  Nenhum alerta criado para testar. Usando ID 1...")
            alert_id = 1
        else:
            alert_id = self.created_alert_id
            
        response = self.session.get(f"{ALERTS_ENDPOINT}/{alert_id}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            alert = response.json()
            print("✅ Detalhes do alerta obtidos com sucesso!")
            print(f"   ID: {alert.get('id')}")
            print(f"   Título: {alert.get('title')}")
            print(f"   Status: {alert.get('status')}")
            print(f"   Severidade: {alert.get('severity')}")
            print(f"   Sistema: {alert.get('system')}")
            print(f"   Duração: {alert.get('duration')}")
            print(f"   Logs: {len(alert.get('alert_logs', []))} entradas")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Alerta {alert_id} não encontrado")
            return False
        else:
            print(f"❌ Falha ao obter detalhes: {response.text}")
            return False

    def test_update_alert(self):
        """Testa atualização de alerta"""
        print("\n✏️ Testando atualização de alerta...")
        
        if not self.created_alert_id:
            print("⚠️  Nenhum alerta criado para testar atualização")
            return False
            
        update_data = {
            "status": "acknowledged",
            "assignee": "admin-updated",
            "description": "Descrição atualizada pelo teste automatizado"
        }
        
        response = self.session.put(f"{ALERTS_ENDPOINT}/{self.created_alert_id}", json=update_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            updated_alert = response.json()
            print("✅ Alerta atualizado com sucesso!")
            print(f"   ID: {updated_alert.get('id')}")
            print(f"   Status: {updated_alert.get('status')}")
            print(f"   Assignee: {updated_alert.get('assignee')}")
            print(f"   Descrição: {updated_alert.get('description')}")
            return True
        else:
            print(f"❌ Falha na atualização: {response.text}")
            return False

    def test_filter_alerts(self):
        """Testa filtros de alertas"""
        print("\n🔍 Testando filtros de alertas...")
        
        # Teste filtro por status
        params = {"status": "active"}
        response = self.session.get(ALERTS_ENDPOINT, params=params)
        print(f"Status (filtro por status ativo): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro por status: {len(data.get('data', []))} alertas ativos")
        
        # Teste filtro por severidade
        params = {"severity": "medium"}
        response = self.session.get(ALERTS_ENDPOINT, params=params)
        print(f"Status (filtro por severidade): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro por severidade: {len(data.get('data', []))} alertas médios")
        
        # Teste filtro por categoria
        params = {"category": "infrastructure"}
        response = self.session.get(ALERTS_ENDPOINT, params=params)
        print(f"Status (filtro por categoria): {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro por categoria: {len(data.get('data', []))} alertas de infraestrutura")
            return True
        else:
            print(f"❌ Falha nos filtros: {response.text}")
            return False

    def test_error_cases(self):
        """Testa casos de erro"""
        print("\n❌ Testando casos de erro...")
        
        # Teste alerta não encontrado
        response = self.session.get(f"{ALERTS_ENDPOINT}/999999")
        print(f"Status (alerta inexistente): {response.status_code}")
        if response.status_code == 404:
            print("✅ Erro 404 para alerta inexistente funcionando corretamente")
        
        # Teste criação com dados inválidos
        invalid_data = {
            "title": "",  # título vazio
            "severity": "invalid",  # severidade inválida
        }
        response = self.session.post(ALERTS_ENDPOINT, json=invalid_data)
        print(f"Status (dados inválidos): {response.status_code}")
        if response.status_code == 422:
            print("✅ Validação de dados inválidos funcionando corretamente")
        
        return True

    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes das rotas de alertas...")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Falha na autenticação. Abortando testes.")
            return False
        
        tests = [
            ("Criação de Alerta", self.test_create_alert),
            ("Listagem de Alertas", self.test_list_alerts),
            ("Detalhes do Alerta", self.test_get_alert_details),
            ("Atualização de Alerta", self.test_update_alert),
            ("Filtros de Alertas", self.test_filter_alerts),
            ("Casos de Erro", self.test_error_cases),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                print("-" * 40)
            except Exception as e:
                print(f"❌ Erro no teste '{test_name}': {e}")
                results.append((test_name, False))
                print("-" * 40)
        
        # Relatório final
        print("\n📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 60)
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"Total: {len(results)} | Passou: {passed} | Falhou: {failed}")
        
        if failed == 0:
            print("🎉 Todos os testes passaram!")
        else:
            print(f"⚠️  {failed} teste(s) falharam")
        
        return failed == 0


if __name__ == "__main__":
    tester = AlertsRouteTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
