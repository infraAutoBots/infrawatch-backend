#!/usr/bin/env python3
"""
Script para testar as rotas de autenticação da API InfraWatch
Execute com: python test_auth_api.py
"""

import requests
from pprint import pprint

API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
LOGIN_FORM_ENDPOINT = f"{API_BASE}/auth/login-form"
REFRESH_ENDPOINT = f"{API_BASE}/auth/refresh"

TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

class AuthTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()

    def test_login_json(self):
        print("\n🔑 Testando login via JSON...")
        response = self.session.post(AUTH_ENDPOINT, json=TEST_CREDENTIALS)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            print(f"✅ Login JSON bem-sucedido. Token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Falha no login JSON: {response.text}")
            return False

    def test_login_form(self):
        print("\n📝 Testando login via formulário...")
        data = {"username": TEST_CREDENTIALS["email"], "password": TEST_CREDENTIALS["password"]}
        response = self.session.post(LOGIN_FORM_ENDPOINT, data=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login formulário bem-sucedido. Token: {data.get('access_token', '')[:20]}...")
            return True
        else:
            print(f"❌ Falha no login formulário: {response.text}")
            return False

    def test_refresh_token(self):
        print("\n🔄 Testando refresh token...")
        if not self.token:
            print("⚠️ Token não disponível para refresh.")
            return False
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        response = self.session.get(REFRESH_ENDPOINT)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Refresh token bem-sucedido. Novo token: {data.get('access_token', '')[:20]}...")
            return True
        else:
            print(f"❌ Falha no refresh token: {response.text}")
            return False

    def run_all_tests(self):
        print("\n🚀 Iniciando testes de autenticação...")
        results = []
        results.append(("Login JSON", self.test_login_json()))
        results.append(("Login Formulário", self.test_login_form()))
        results.append(("Refresh Token", self.test_refresh_token()))
        print("\n📋 RELATÓRIO FINAL")
        for name, result in results:
            print(f"{name:<20} {'✅' if result else '❌'}")
        return all(r for _, r in results)

if __name__ == "__main__":
    tester = AuthTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
