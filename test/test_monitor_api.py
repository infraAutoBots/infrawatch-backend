#!/usr/bin/env python3
"""
Script para testar as rotas de monitoramento da API InfraWatch
Execute com: python test_monitor_api.py
"""

import requests
from pprint import pprint

API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
MONITOR_ENDPOINT = f"{API_BASE}/monitor"
STATUS_ENDPOINT = f"{MONITOR_ENDPOINT}/status"

TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class MonitorTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()

    def authenticate(self):
        print("\n🔐 Autenticando para testes de monitor...")
        response = self.session.post(AUTH_ENDPOINT, json=TEST_CREDENTIALS)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Autenticado. Token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Falha na autenticação: {response.text}")
            return False

    def test_add_ip(self):
        print("\n➕ Testando adição de endpoint...")
        # Primeiro verifica se o endpoint já existe e remove se necessário
        test_ip = "192.168.1.100"  # Usando um IP único para teste
        check_response = self.session.get(f"{MONITOR_ENDPOINT}/{test_ip}")
        if check_response.status_code == 200:
            print(f"⚠️  Endpoint {test_ip} já existe, pulando teste de adição")
            return True
        
        payload = {
            "ip": test_ip,
            "nickname": "Test Endpoint",  # Campo obrigatório que estava faltando
            "interval": 30,
            "version": "2c",
            "community": "public",
            "port": 161,
            "user": "",
            "authKey": "",
            "privKey": "",
            "sysDescr": "1.3.6.1.2.1.1.1.0",
            "sysName": "1.3.6.1.2.1.1.5.0",
            "sysUpTime": "1.3.6.1.2.1.1.3.0",
            "hrProcessorLoad": "1.3.6.1.2.1.25.3.3.1.2",
            "memTotalReal": "1.3.6.1.4.1.2021.4.5.0",
            "memAvailReal": "1.3.6.1.4.1.2021.4.6.0",
            "hrStorageSize": "1.3.6.1.2.1.25.2.3.1.5",
            "hrStorageUsed": "1.3.6.1.2.1.25.2.3.1.6",
            "hrStorageDescr": "1.3.6.1.2.1.25.2.3.1.3",
            "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
            "ifInOctets": "1.3.6.1.2.1.2.2.1.10",
            "ifOutOctets": "1.3.6.1.2.1.2.2.1.16"
        }
        response = self.session.post(MONITOR_ENDPOINT + "/", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Endpoint adicionado com sucesso")
            return True
        else:
            print(f"❌ Falha ao adicionar endpoint: {response.text}")
            return False

    def test_get_status(self):
        print("\n📊 Testando obtenção de status dos endpoints...")
        response = self.session.get(STATUS_ENDPOINT)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Status dos endpoints obtido com sucesso")
            pprint(response.json())
            return True
        else:
            print(f"❌ Falha ao obter status: {response.text}")
            return False

    def test_get_ip_info(self):
        print("\n🔍 Testando obtenção de info de endpoint...")
        # Primeiro obtemos a lista de endpoints para usar um IP existente
        status_response = self.session.get(STATUS_ENDPOINT)
        if status_response.status_code == 200:
            monitors = status_response.json().get('monitors', [])
            if monitors:
                # Usa o primeiro endpoint disponível
                test_ip = monitors[0]['endpoint']
                response = self.session.get(f"{MONITOR_ENDPOINT}/{test_ip}")
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ Info do endpoint {test_ip} obtida com sucesso")
                    pprint(response.json())
                    return True
                else:
                    print(f"❌ Falha ao obter info do endpoint {test_ip}: {response.text}")
                    return False
            else:
                print("⚠️  Nenhum endpoint encontrado para teste")
                return True  # Não é falha do teste, apenas não há dados
        else:
            print("❌ Não foi possível obter lista de endpoints para teste")
            return False

    def run_all_tests(self):
        print("\n🚀 Iniciando testes de monitoramento...")
        if not self.authenticate():
            print("❌ Não autenticado. Abortando testes.")
            return False
        results = []
        results.append(("Adicionar endpoint", self.test_add_ip()))
        results.append(("Obter status endpoints", self.test_get_status()))
        results.append(("Obter info endpoint", self.test_get_ip_info()))
        print("\n📋 RELATÓRIO FINAL")
        for name, result in results:
            print(f"{name:<25} {'✅' if result else '❌'}")
        return all(r for _, r in results)

if __name__ == "__main__":
    tester = MonitorTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
