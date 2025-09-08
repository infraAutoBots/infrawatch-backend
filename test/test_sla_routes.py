#!/usr/bin/env python3
"""
Script para testar as rotas de SLA da API InfraWatch
Execute com: python test_sla_routes.py
"""

import requests
import json
import sys
from pprint import pprint
from datetime import datetime, timedelta

# Configuração da API
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
SLA_ENDPOINT = f"{API_BASE}/sla"

# Credenciais de teste
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class SLARouteTester:
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

    def test_sla_summary(self):
        """Testa o endpoint de resumo SLA"""
        print("\n📊 Testando endpoint de resumo SLA...")
        
        try:
            # Teste básico - últimos 30 dias
            response = self.session.get(f"{SLA_ENDPOINT}/summary")
            print(f"Status (30 dias): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resumo SLA obtido com sucesso")
                print(f"   - Endpoints encontrados: {len(data.get('endpoints', []))}")
                print(f"   - Métricas SLA: {len(data.get('sla_metrics', []))}")
                print(f"   - Incidentes: {len(data.get('incidents', []))}")
                print(f"   - Dados de performance: {len(data.get('performance_data', []))}")
                print(f"   - Alertas: {len(data.get('alerts', []))}")
            else:
                print(f"❌ Erro ao obter resumo SLA: {response.text}")
                return False
            
            # Teste com diferentes períodos
            for days in [7, 15, 60, 90]:
                response = self.session.get(f"{SLA_ENDPOINT}/summary?days={days}")
                print(f"Status ({days} dias): {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ Resumo para {days} dias obtido com sucesso")
                else:
                    print(f"❌ Erro para {days} dias: {response.text}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    def test_sla_endpoint_specific(self):
        """Testa o endpoint de SLA específico por endpoint"""
        print("\n🎯 Testando endpoint específico por endpoint...")
        
        try:
            # Primeiro, vamos tentar endpoint_id = 1
            response = self.session.get(f"{SLA_ENDPOINT}/endpoint/1")
            print(f"Status (endpoint 1): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SLA do endpoint 1 obtido com sucesso")
                print(f"   - Chaves disponíveis: {list(data.keys()) if isinstance(data, dict) else 'Dados não estruturados'}")
            elif response.status_code == 404:
                print(f"⚠️ Endpoint 1 não encontrado (esperado se não houver dados)")
            else:
                print(f"❌ Erro ao obter SLA do endpoint: {response.text}")
                return False
            
            # Tentar outros IDs
            for endpoint_id in [2, 3]:
                response = self.session.get(f"{SLA_ENDPOINT}/endpoint/{endpoint_id}")
                print(f"Status (endpoint {endpoint_id}): {response.status_code}")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    def test_sla_incidents_summary(self):
        """Testa o endpoint de resumo de incidentes"""
        print("\n� Testando resumo de incidentes...")
        
        try:
            response = self.session.get(f"{SLA_ENDPOINT}/incidents/summary")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resumo de incidentes obtido com sucesso")
                if isinstance(data, dict):
                    print(f"   - Chaves disponíveis: {list(data.keys())}")
                else:
                    print(f"   - Estrutura dos dados: {type(data)}")
            else:
                print(f"❌ Erro ao obter resumo de incidentes: {response.text}")
                return False
            
            # Teste com parâmetros
            test_params = [
                {"days": 7},
                {"days": 30},
                {"endpoint_id": 1}
            ]
            
            for params in test_params:
                response = self.session.get(f"{SLA_ENDPOINT}/incidents/summary", params=params)
                print(f"Status (filtro {params}): {response.status_code}")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    def test_sla_performance_metrics(self):
        """Testa o endpoint de métricas de performance"""
        print("\n📈 Testando métricas de performance...")
        
        try:
            response = self.session.get(f"{SLA_ENDPOINT}/performance-metrics")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Métricas de performance obtidas com sucesso")
                if isinstance(data, list):
                    print(f"   - Total de registros: {len(data)}")
                    if data:
                        print(f"   - Campos disponíveis: {list(data[0].keys()) if data else 'Nenhum'}")
                elif isinstance(data, dict):
                    print(f"   - Chaves disponíveis: {list(data.keys())}")
                else:
                    print(f"   - Estrutura dos dados: {type(data)}")
            else:
                print(f"❌ Erro ao obter métricas de performance: {response.text}")
                return False
            
            # Teste com parâmetros
            test_params = [
                {"endpoint_id": 1},
                {"days": 7},
                {"days": 30}
            ]
            
            for params in test_params:
                response = self.session.get(f"{SLA_ENDPOINT}/performance-metrics", params=params)
                print(f"Status (filtro {params}): {response.status_code}")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    def test_sla_compliance(self):
        """Testa o endpoint de compliance SLA"""
        print("\n✅ Testando endpoint de compliance...")
        
        try:
            response = self.session.get(f"{SLA_ENDPOINT}/compliance")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Compliance SLA obtido com sucesso")
                if isinstance(data, list):
                    print(f"   - Total de endpoints avaliados: {len(data)}")
                    if data:
                        compliant = sum(1 for item in data if item.get('sla_compliance', False))
                        print(f"   - Endpoints em compliance: {compliant}/{len(data)}")
                else:
                    print(f"   - Estrutura dos dados: {type(data)}")
            else:
                print(f"❌ Erro ao obter compliance: {response.text}")
                return False
            
            # Teste com diferentes targets SLA
            for target in [99.0, 99.5, 99.9, 99.95]:
                response = self.session.get(f"{SLA_ENDPOINT}/compliance?sla_target={target}")
                print(f"Status (target {target}%): {response.status_code}")
                
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")
            return False

    def run_all_tests(self):
        """Executa todos os testes de SLA"""
        print("🧪 Iniciando testes das rotas de SLA...")
        print("=" * 50)
        
        if not self.authenticate():
            print("❌ Falha na autenticação. Não é possível continuar.")
            return False
        
        tests = [
            ("SLA Summary", self.test_sla_summary),
            ("SLA Endpoint Specific", self.test_sla_endpoint_specific),
            ("SLA Incidents Summary", self.test_sla_incidents_summary),
            ("SLA Performance Metrics", self.test_sla_performance_metrics),
            ("SLA Compliance", self.test_sla_compliance),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Executando: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} - PASSOU")
                else:
                    print(f"❌ {test_name} - FALHOU")
            except Exception as e:
                print(f"❌ {test_name} - ERRO: {e}")
        
        print(f"\n" + "=" * 50)
        print(f"📊 RESUMO DOS TESTES DE SLA:")
        print(f"   Total: {total}")
        print(f"   Passou: {passed}")
        print(f"   Falhou: {total - passed}")
        print(f"   Taxa de sucesso: {(passed/total)*100:.1f}%")
        print("=" * 50)
        
        return passed == total


def main():
    """Função principal"""
    # Verificar se a API está rodando
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não está acessível em {API_BASE}")
            print("Execute: python api/app.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print(f"❌ Não foi possível conectar à API em {API_BASE}")
        print("Execute: python api/app.py")
        sys.exit(1)
    
    print(f"✅ API está rodando em {API_BASE}")
    
    # Executar testes
    tester = SLARouteTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
