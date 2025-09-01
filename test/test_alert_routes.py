#!/usr/bin/env python3
"""
Script para testar todas as rotas de alertas da API InfraWatch
Execute com: python test_alert_routes.py
"""

import requests
import json
import sys
from pprint import pprint
from datetime import datetime, timedelta
import time

# Configuração da API
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
ALERTS_ENDPOINT = f"{API_BASE}/alerts"

# Credenciais de teste (assumindo que existe um admin)
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class AlertAPITester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.created_alert_ids = []  # Para cleanup
    
    def authenticate(self):
        """Faz login e obtém o token de autenticação"""
        print("🔑 Realizando autenticação...")
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
    
    def test_create_alert(self):
        """Testa a criação de alertas"""
        print("\n➕ Testando criação de alertas...")
        
        test_alerts = [
            {
                "title": "Teste CPU Alta - Servidor Web",
                "description": "CPU acima de 95% no servidor web-01",
                "severity": "critical",
                "category": "performance",
                "system": "web-01.test.local",
                "impact": "high",
                "assignee": "Admin Teste"
            },
            {
                "title": "Teste Memoria Baixa - DB Server",
                "description": "Memória disponível abaixo de 10%",
                "severity": "high",
                "category": "performance",
                "system": "db-01.test.local",
                "impact": "medium"
            },
            {
                "title": "Teste Acesso Negado - Security",
                "description": "Múltiplas tentativas de login inválido detectadas",
                "severity": "medium",
                "category": "security",
                "system": "auth-service",
                "impact": "low",
                "assignee": "Security Team"
            },
            {
                "title": "Teste Rede Lenta - Network",
                "description": "Latência elevada entre datacenters",
                "severity": "low",
                "category": "network",
                "system": "network-core",
                "impact": "medium"
            }
        ]
        
        created_count = 0
        for i, alert_data in enumerate(test_alerts):
            try:
                response = self.session.post(ALERTS_ENDPOINT, json=alert_data)
                print(f"   Alert {i+1} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    alert_id = data.get("id")
                    if alert_id:
                        self.created_alert_ids.append(alert_id)
                        created_count += 1
                        print(f"   ✅ Alerta criado com ID: {alert_id}")
                    else:
                        print(f"   ⚠️ Alerta criado mas ID não retornado")
                        print(f"   Resposta: {data}")
                else:
                    print(f"   ❌ Falha na criação do alerta {i+1}: {response.text}")
                
            except Exception as e:
                print(f"   ❌ Erro ao criar alerta {i+1}: {e}")
        
        print(f"✅ {created_count}/{len(test_alerts)} alertas criados com sucesso")
        return created_count > 0
    
    def test_list_alerts(self):
        """Testa a listagem de alertas com paginação e filtros"""
        print("\n📋 Testando listagem de alertas...")
        
        tests = [
            # Teste básico
            ("Listagem básica", ""),
            # Teste de paginação
            ("Paginação - página 1", "?page=1&size=2"),
            ("Paginação - página 2", "?page=2&size=2"),
            # Teste de filtros
            ("Filtro por severidade crítica", "?severity=critical"),
            ("Filtro por severidade alta", "?severity=high"),
            ("Filtro por status ativo", "?status=active"),
            ("Filtro por categoria performance", "?category=performance"),
            ("Filtro por categoria security", "?category=security"),
            ("Filtro por impacto alto", "?impact=high"),
            # Teste de busca
            ("Busca por 'CPU'", "?search=CPU"),
            ("Busca por 'web-01'", "?search=web-01"),
            ("Busca por 'teste'", "?search=teste"),
            # Teste de ordenação
            ("Ordenação por título", "?sort_by=title&sort_order=asc"),
            ("Ordenação por data", "?sort_by=created_at&sort_order=desc"),
            # Teste de filtros múltiplos
            ("Múltiplos filtros", "?severity=critical&severity=high&category=performance"),
            # Teste de combinação complexa
            ("Filtros complexos", "?search=teste&severity=critical&status=active&page=1&size=5")
        ]
        
        success_count = 0
        for test_name, query_params in tests:
            try:
                url = f"{ALERTS_ENDPOINT}{query_params}"
                response = self.session.get(url)
                print(f"   {test_name} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        pagination = data.get("pagination", {})
                        alerts_count = len(data.get("data", []))
                        print(f"   ✅ {alerts_count} alertas retornados, Total: {pagination.get('total', 0)}")
                        success_count += 1
                    else:
                        print(f"   ❌ Resposta indica falha: {data}")
                else:
                    print(f"   ❌ Falha: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Erro no teste '{test_name}': {e}")
        
        print(f"✅ {success_count}/{len(tests)} testes de listagem passaram")
        return success_count > len(tests) * 0.8  # 80% de sucesso
    
    def test_get_alert_stats(self):
        """Testa as estatísticas de alertas"""
        print("\n📊 Testando estatísticas de alertas...")
        
        try:
            response = self.session.get(f"{ALERTS_ENDPOINT}/stats")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Estatísticas obtidas com sucesso:")
                print(f"   Total de alertas: {data.get('total_alerts', 0)}")
                print(f"   Alertas críticos ativos: {data.get('critical_active', 0)}")
                print(f"   Reconhecidos: {data.get('acknowledged', 0)}")
                print(f"   Resolvidos hoje: {data.get('resolved_today', 0)}")
                print(f"   MTTR médio: {data.get('average_resolution_time', 'N/A')}")
                
                by_category = data.get('by_category', {})
                if by_category:
                    print(f"   Por categoria: {by_category}")
                
                by_system = data.get('by_system', {})
                if by_system:
                    print(f"   Por sistema: {dict(list(by_system.items())[:5])}")  # Top 5
                
                return True
            else:
                print(f"❌ Falha ao obter estatísticas: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao testar estatísticas: {e}")
            return False
    
    def test_get_alert_details(self):
        """Testa obtenção de detalhes de alertas específicos"""
        print("\n🔍 Testando detalhes de alertas...")
        
        if not self.created_alert_ids:
            print("⚠️ Nenhum alerta criado para testar detalhes")
            return False
        
        success_count = 0
        for alert_id in self.created_alert_ids[:3]:  # Testa os 3 primeiros
            try:
                response = self.session.get(f"{ALERTS_ENDPOINT}/{alert_id}")
                print(f"   Alerta {alert_id} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Detalhes obtidos: {data.get('title', 'N/A')}")
                    
                    # Verificar se tem logs
                    logs = data.get('alert_logs', [])
                    print(f"      Logs de ações: {len(logs)}")
                    
                    success_count += 1
                else:
                    print(f"   ❌ Falha ao obter detalhes: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar alerta {alert_id}: {e}")
        
        print(f"✅ {success_count}/{min(3, len(self.created_alert_ids))} detalhes obtidos")
        return success_count > 0
    
    def test_update_alert(self):
        """Testa atualização de alertas"""
        print("\n✏️ Testando atualização de alertas...")
        
        if not self.created_alert_ids:
            print("⚠️ Nenhum alerta criado para atualizar")
            return False
        
        alert_id = self.created_alert_ids[0]
        update_data = {
            "title": "Teste CPU Alta - Servidor Web [ATUALIZADO]",
            "description": "CPU acima de 95% no servidor web-01 [DESCRIÇÃO ATUALIZADA]",
            "severity": "high",  # Reduzindo severidade
            "impact": "medium",  # Reduzindo impacto
            "assignee": "Novo Responsável"
        }
        
        try:
            response = self.session.put(f"{ALERTS_ENDPOINT}/{alert_id}", json=update_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Alerta {alert_id} atualizado com sucesso")
                print(f"   Novo título: {data.get('title', 'N/A')}")
                print(f"   Nova severidade: {data.get('severity', 'N/A')}")
                return True
            else:
                print(f"❌ Falha na atualização: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao atualizar alerta: {e}")
            return False
    
    def test_alert_actions(self):
        """Testa ações nos alertas (acknowledge, resolve, assign)"""
        print("\n⚡ Testando ações nos alertas...")
        
        if len(self.created_alert_ids) < 3:
            print("⚠️ Alertas insuficientes para testar todas as ações")
            return False
        
        actions_tests = [
            ("acknowledge", {"action": "acknowledge", "comment": "Investigando o problema"}),
            ("assign", {"action": "assign", "assignee": "Especialista Rede", "comment": "Atribuído para especialista"}),
            ("resolve", {"action": "resolve", "comment": "Problema resolvido após reinicialização"})
        ]
        
        success_count = 0
        for i, (action_name, action_data) in enumerate(actions_tests):
            if i >= len(self.created_alert_ids):
                break
                
            alert_id = self.created_alert_ids[i]
            try:
                response = self.session.post(f"{ALERTS_ENDPOINT}/{alert_id}/actions", json=action_data)
                print(f"   Ação '{action_name}' no alerta {alert_id} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success", False):
                        print(f"   ✅ Ação '{action_name}' executada com sucesso")
                        success_count += 1
                    else:
                        print(f"   ❌ Ação '{action_name}' falhou: {data}")
                else:
                    print(f"   ❌ Falha na ação '{action_name}': {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Erro na ação '{action_name}': {e}")
        
        print(f"✅ {success_count}/{len(actions_tests)} ações executadas com sucesso")
        return success_count > 0
    
    def test_bulk_actions(self):
        """Testa ações em lote nos alertas"""
        print("\n📦 Testando ações em lote...")
        
        if len(self.created_alert_ids) < 2:
            print("⚠️ Alertas insuficientes para testar ações em lote")
            return False
        
        # Criar alguns alertas extras para teste de lote
        extra_alerts = [
            {
                "title": "Teste Bulk 1 - Disco Cheio",
                "description": "Disco em 98%",
                "severity": "high",
                "category": "infrastructure",
                "system": "storage-01",
                "impact": "high"
            },
            {
                "title": "Teste Bulk 2 - Serviço Offline",
                "description": "Serviço web não responde",
                "severity": "critical",
                "category": "infrastructure",
                "system": "web-02",
                "impact": "high"
            }
        ]
        
        bulk_alert_ids = []
        for alert_data in extra_alerts:
            try:
                response = self.session.post(ALERTS_ENDPOINT, json=alert_data)
                if response.status_code == 200:
                    data = response.json()
                    alert_id = data.get("id")
                    if alert_id:
                        bulk_alert_ids.append(alert_id)
                        self.created_alert_ids.append(alert_id)
            except Exception as e:
                print(f"   ⚠️ Erro ao criar alerta para teste de lote: {e}")
        
        if len(bulk_alert_ids) < 2:
            print("⚠️ Não foi possível criar alertas suficientes para teste de lote")
            return False
        
        # Teste de reconhecimento em lote
        bulk_data = {
            "action": "acknowledge",
            "comment": "Reconhecimento em lote - teste automatizado"
        }
        
        try:
            # Usar body JSON para alert_ids ao invés de query param
            payload = {**bulk_data, "alert_ids": bulk_alert_ids}
            response = self.session.post(f"{ALERTS_ENDPOINT}/bulk-actions", json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    updated_count = data.get("updated_count", 0)
                    print(f"✅ Ação em lote executada com sucesso: {updated_count} alertas atualizados")
                    return True
                else:
                    print(f"❌ Ação em lote falhou: {data}")
            else:
                print(f"❌ Falha na ação em lote: {response.text}")
                
        except Exception as e:
            print(f"❌ Erro na ação em lote: {e}")
        
        return False
    
    def test_invalid_operations(self):
        """Testa operações inválidas para verificar tratamento de erros"""
        print("\n🚫 Testando operações inválidas...")
        
        tests = [
            # Alert inexistente
            ("GET de alerta inexistente", "get", f"{ALERTS_ENDPOINT}/99999", None),
            ("UPDATE de alerta inexistente", "put", f"{ALERTS_ENDPOINT}/99999", {"title": "Test"}),
            ("DELETE de alerta inexistente", "delete", f"{ALERTS_ENDPOINT}/99999", None),
            ("AÇÃO em alerta inexistente", "post", f"{ALERTS_ENDPOINT}/99999/actions", {"action": "acknowledge"}),
            
            # Dados inválidos
            ("Criação com dados inválidos", "post", ALERTS_ENDPOINT, {"title": ""}),  # título vazio
            ("Criação sem campos obrigatórios", "post", ALERTS_ENDPOINT, {"description": "teste"}),  # sem título
            ("Ação inválida", "post", f"{ALERTS_ENDPOINT}/{self.created_alert_ids[0] if self.created_alert_ids else 1}/actions", {"action": "invalid_action"}),
            
            # Filtros inválidos
            ("Filtro com valor inválido", "get", f"{ALERTS_ENDPOINT}?severity=invalid", None),
            ("Paginação inválida", "get", f"{ALERTS_ENDPOINT}?page=0&size=-1", None),
        ]
        
        expected_errors = 0
        actual_errors = 0
        
        for test_name, method, url, data in tests:
            try:
                if method == "get":
                    response = self.session.get(url)
                elif method == "post":
                    response = self.session.post(url, json=data)
                elif method == "put":
                    response = self.session.put(url, json=data)
                elif method == "delete":
                    response = self.session.delete(url)
                
                expected_errors += 1
                
                if response.status_code >= 400:  # Erro esperado
                    actual_errors += 1
                    print(f"   ✅ {test_name} - Erro {response.status_code} (esperado)")
                else:
                    print(f"   ⚠️ {test_name} - Status {response.status_code} (erro esperado)")
                    
            except Exception as e:
                print(f"   ❌ Erro no teste '{test_name}': {e}")
        
        print(f"✅ {actual_errors}/{expected_errors} erros tratados corretamente")
        return actual_errors >= expected_errors * 0.7  # 70% dos erros tratados
    
    def cleanup(self):
        """Remove alertas criados durante os testes"""
        print("\n🧹 Limpando alertas de teste...")
        
        deleted_count = 0
        for alert_id in self.created_alert_ids:
            try:
                response = self.session.delete(f"{ALERTS_ENDPOINT}/{alert_id}")
                if response.status_code == 200:
                    deleted_count += 1
                    print(f"   ✅ Alerta {alert_id} removido")
                else:
                    print(f"   ⚠️ Falha ao remover alerta {alert_id}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Erro ao remover alerta {alert_id}: {e}")
        
        print(f"✅ {deleted_count}/{len(self.created_alert_ids)} alertas removidos")
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES COMPLETOS DA API DE ALERTAS")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Falha na autenticação. Abortando testes.")
            return False
        
        tests = [
            ("Criação de alertas", self.test_create_alert),
            ("Listagem e filtros", self.test_list_alerts),
            ("Estatísticas", self.test_get_alert_stats),
            ("Detalhes de alertas", self.test_get_alert_details),
            ("Atualização de alertas", self.test_update_alert),
            ("Ações nos alertas", self.test_alert_actions),
            ("Ações em lote", self.test_bulk_actions),
            ("Operações inválidas", self.test_invalid_operations),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                duration = end_time - start_time
                results.append((test_name, result, duration))
                
                status = "✅ PASSOU" if result else "❌ FALHOU"
                print(f"{status} ({duration:.2f}s)")
                
                # Pausa entre testes
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ ERRO CRÍTICO no teste '{test_name}': {e}")
                results.append((test_name, False, 0))
        
        # Cleanup
        self.cleanup()
        
        # Relatório final
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 60)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        total_time = sum(duration for _, _, duration in results)
        
        print(f"Testes executados: {total}")
        print(f"Testes aprovados: {passed}")
        print(f"Testes falharam: {total - passed}")
        print(f"Taxa de sucesso: {passed/total*100:.1f}%")
        print(f"Tempo total: {total_time:.2f}s")
        
        print("\nDetalhes por teste:")
        for test_name, result, duration in results:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name:<30} ({duration:.2f}s)")
        
        overall_success = passed >= total * 0.8  # 80% de sucesso
        print(f"\n🎯 Resultado geral: {'✅ SUCESSO' if overall_success else '❌ FALHA'}")
        
        return overall_success


def main():
    """Função principal"""
    print("🔧 Testador da API de Alertas - InfraWatch")
    print("=" * 50)
    
    # Verificar se a API está rodando
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não está respondendo corretamente: {response.status_code}")
            return
    except requests.exceptions.RequestException:
        print(f"❌ Não foi possível conectar à API em {API_BASE}")
        print("   Certifique-se de que o servidor está rodando")
        return
    
    print(f"✅ API está ativa em {API_BASE}")
    
    # Executar testes
    tester = AlertAPITester()
    success = tester.run_all_tests()
    
    # Código de saída
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
