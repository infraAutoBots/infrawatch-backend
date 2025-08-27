#!/usr/bin/env python3
"""
Script para testar as rotas de usuários da API InfraWatch
Execute com: python test_users_api.py
"""

import requests
import json
import sys
from pprint import pprint
from datetime import datetime

# Configuração da API
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
USERS_ENDPOINT = f"{API_BASE}/users"

# Credenciais de teste (assumindo que existe um admin)
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class APITester:
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
    
    def test_list_users(self):
        """Testa a listagem de usuários"""
        print("\n🔍 Testando listagem de usuários...")
        
        try:
            # Teste básico de listagem
            response = self.session.get(USERS_ENDPOINT)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Listagem básica funcionando")
                print(f"   Total de usuários: {data.get('total', 0)}")
                print(f"   Página atual: {data.get('page', 1)}")
                print(f"   Total de páginas: {data.get('pages', 1)}")
                
                # Testar paginação
                response_page2 = self.session.get(f"{USERS_ENDPOINT}?page=2&limit=5")
                if response_page2.status_code == 200:
                    print(f"✅ Paginação funcionando")
                
                # Testar busca
                response_search = self.session.get(f"{USERS_ENDPOINT}?search=admin")
                if response_search.status_code == 200:
                    print(f"✅ Busca funcionando")
                
                # Testar filtros
                response_filter = self.session.get(f"{USERS_ENDPOINT}?status=active&access_level=ADMIN")
                if response_filter.status_code == 200:
                    print(f"✅ Filtros funcionando")
                
                return True
            else:
                print(f"❌ Falha na listagem: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste de listagem: {e}")
            return False
    
    def test_create_user(self):
        """Testa a criação de usuário"""
        print("\n➕ Testando criação de usuário...")
        
        test_user = {
            "name": "Usuário Teste",
            "email": f"teste_{datetime.now().strftime('%Y%m%d_%H%M%S')}@exemplo.com",
            "password": "senha123",
            "access_level": "MONITOR",
            "state": True
        }
        
        try:
            response = self.session.post(USERS_ENDPOINT, json=test_user)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Usuário criado com sucesso")
                print(f"   ID: {data.get('user', {}).get('id')}")
                print(f"   Nome: {data.get('user', {}).get('name')}")
                return data.get('user', {}).get('id')
            else:
                print(f"❌ Falha na criação: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na criação de usuário: {e}")
            return None
    
    def test_get_user(self, user_id):
        """Testa a obtenção de um usuário específico"""
        if not user_id:
            return False
            
        print(f"\n👤 Testando obtenção do usuário {user_id}...")
        
        try:
            response = self.session.get(f"{USERS_ENDPOINT}/{user_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Usuário obtido com sucesso")
                print(f"   Nome: {data.get('name')}")
                print(f"   Email: {data.get('email')}")
                return True
            else:
                print(f"❌ Falha ao obter usuário: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter usuário: {e}")
            return False
    
    def test_update_user(self, user_id):
        """Testa a atualização de usuário"""
        if not user_id:
            return False
            
        print(f"\n✏️ Testando atualização do usuário {user_id}...")
        
        update_data = {
            "name": "Usuário Teste Atualizado"
        }
        
        try:
            response = self.session.put(f"{USERS_ENDPOINT}/{user_id}", json=update_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Usuário atualizado com sucesso")
                print(f"   Novo nome: {data.get('user', {}).get('name')}")
                return True
            else:
                print(f"❌ Falha na atualização: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na atualização: {e}")
            return False
    
    def test_update_user_status(self, user_id):
        """Testa a alteração de status do usuário"""
        if not user_id:
            return False
            
        print(f"\n🔄 Testando alteração de status do usuário {user_id}...")
        
        try:
            # Desativar usuário
            response = self.session.patch(
                f"{USERS_ENDPOINT}/{user_id}/status",
                json={"state": False}
            )
            print(f"Status (desativar): {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Status alterado para inativo")
                
                # Reativar usuário
                response = self.session.patch(
                    f"{USERS_ENDPOINT}/{user_id}/status",
                    json={"state": True}
                )
                
                if response.status_code == 200:
                    print(f"✅ Status alterado para ativo")
                    return True
            
            print(f"❌ Falha na alteração de status: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Erro na alteração de status: {e}")
            return False
    
    def test_get_stats(self):
        """Testa a obtenção de estatísticas"""
        print("\n📊 Testando obtenção de estatísticas...")
        
        try:
            response = self.session.get(f"{USERS_ENDPOINT}/stats/summary")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Estatísticas obtidas com sucesso")
                print(f"   Total de usuários: {data.get('total_users')}")
                print(f"   Administradores: {data.get('admins')}")
                print(f"   Monitores: {data.get('monitors')}")
                print(f"   Visualizadores: {data.get('viewers')}")
                return True
            else:
                print(f"❌ Falha ao obter estatísticas: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return False
    
    def test_delete_user(self, user_id):
        """Testa a exclusão de usuário"""
        if not user_id:
            return False
            
        print(f"\n🗑️ Testando exclusão do usuário {user_id}...")
        
        try:
            response = self.session.delete(f"{USERS_ENDPOINT}/{user_id}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Usuário excluído com sucesso")
                return True
            else:
                print(f"❌ Falha na exclusão: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na exclusão: {e}")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 Iniciando testes da API de Usuários...")
        print(f"🔗 API Base: {API_BASE}")
        
        # Autenticar
        if not self.authenticate():
            print("\n❌ Não foi possível autenticar. Verifique se a API está rodando e as credenciais estão corretas.")
            return False
        
        # Executar testes
        results = []
        
        # Teste de listagem
        results.append(("Listagem", self.test_list_users()))
        
        # Teste de criação
        user_id = self.test_create_user()
        results.append(("Criação", user_id is not None))
        
        if user_id:
            # Testes que dependem de ter um usuário criado
            results.append(("Obter usuário", self.test_get_user(user_id)))
            results.append(("Atualizar usuário", self.test_update_user(user_id)))
            results.append(("Alterar status", self.test_update_user_status(user_id)))
            results.append(("Excluir usuário", self.test_delete_user(user_id)))
        
        # Teste de estatísticas
        results.append(("Estatísticas", self.test_get_stats()))
        
        # Relatório final
        print("\n" + "="*50)
        print("📋 RELATÓRIO FINAL DOS TESTES")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
        
        print(f"\n📈 Resumo: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 Todos os testes passaram com sucesso")
        else:
            print("⚠️ Alguns testes falharam. Verifique a implementação.")
        
        return passed == total


def main():
    """Função principal"""
    print("🧪 Testador da API de Usuários - InfraWatch")
    print("-" * 50)
    
    tester = APITester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
