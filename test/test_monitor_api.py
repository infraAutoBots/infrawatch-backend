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
        payload = {
            "ip": "192.168.56.123",
            "interval": 30,
            "version": "2c",
            "community": "public",
            "port": 161,
            "user": "",
            "authKey": "",
            "privKey": "",
            "webhook": "",
            "sysDescr": "desc",
            "sysName": "name",
            "sysUpTime": "up",
            "hrProcessorLoad": "1",
            "memTotalReal": "1",
            "memAvailReal": "1",
            "hrStorageSize": "1",
            "hrStorageUsed": "1"
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
        ip = "192.168.56.123"
        response = self.session.get(f"{MONITOR_ENDPOINT}/{ip}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Info do endpoint obtida com sucesso")
            pprint(response.json())
            return True
        else:
            print(f"❌ Falha ao obter info do endpoint: {response.text}")
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
