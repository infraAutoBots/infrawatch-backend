#!/usr/bin/env python3
"""
Teste completo para validar o tratamento de filtros de alertas
com valores em português, inglês e inválidos.
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
ALERTS_ENDPOINT = f"{API_BASE}/alerts/"

TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com",
    "password": "ndondadaniel2020@gmail.com"
}

def get_auth_token():
    """Obtém token de autenticação"""
    response = requests.post(AUTH_ENDPOINT, json=TEST_CREDENTIALS)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Erro na autenticação: {response.text}")

def test_filter_values():
    """Testa diferentes valores de filtro"""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🧪 TESTE DE FILTROS DE ALERTAS - COMPATIBILIDADE MULTILÍNGUE")
    print("=" * 70)
    
    test_cases = [
        # Severity tests
        ("Severidade - Português 'alto'", {"severity": "alto"}),
        ("Severidade - Português 'crítico'", {"severity": "critico"}),
        ("Severidade - Português 'médio'", {"severity": "medio"}),
        ("Severidade - Português 'baixo'", {"severity": "baixo"}),
        ("Severidade - Inglês 'high'", {"severity": "high"}),
        ("Severidade - Inglês 'critical'", {"severity": "critical"}),
        ("Severidade - Inglês 'medium'", {"severity": "medium"}),
        ("Severidade - Inglês 'low'", {"severity": "low"}),
        ("Severidade - Valor inválido", {"severity": "inexistente"}),
        
        # Status tests  
        ("Status - Português 'aberto'", {"status": "aberto"}),
        ("Status - Português 'em_progresso'", {"status": "em_progresso"}),
        ("Status - Português 'resolvido'", {"status": "resolvido"}),
        ("Status - Inglês 'open'", {"status": "open"}),
        ("Status - Inglês 'in_progress'", {"status": "in_progress"}),
        ("Status - Valor inválido", {"status": "invalido"}),
        
        # Impact tests
        ("Impacto - Português 'alto'", {"impact": "alto"}),
        ("Impacto - Português 'médio'", {"impact": "medio"}),
        ("Impacto - Inglês 'high'", {"impact": "high"}),
        ("Impacto - Valor inválido", {"impact": "extremo"}),
        
        # Mixed tests
        ("Múltiplos filtros válidos", {"severity": "alto", "status": "aberto", "impact": "high"}),
        ("Múltiplos com inválidos", {"severity": "alto,inexistente,high", "status": "invalido,open"}),
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for test_name, params in test_cases:
        print(f"\n📋 {test_name}")
        print(f"   Parâmetros: {params}")
        
        try:
            response = requests.get(ALERTS_ENDPOINT, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                alerts_count = len(data.get("data", []))
                print(f"   ✅ Sucesso - Status: {response.status_code}")
                print(f"   📊 Alertas retornados: {alerts_count}")
                success_count += 1
            else:
                print(f"   ❌ Erro - Status: {response.status_code}")
                print(f"   📝 Resposta: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exceção: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 RESULTADO FINAL:")
    print(f"   Testes executados: {total_tests}")
    print(f"   Sucessos: {success_count}")
    print(f"   Falhas: {total_tests - success_count}")
    print(f"   Taxa de sucesso: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("   🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("   ⚠️  Alguns testes falharam")
        return False

if __name__ == "__main__":
    try:
        success = test_filter_values()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        exit(1)
