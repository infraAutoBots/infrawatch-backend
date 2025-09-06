#!/usr/bin/env python3
"""
Script para testar as rotas de configuração de performance thresholds
"""

import requests
import json

BASE_URL = "http://localhost:8000"  # Ajuste conforme necessário
API_BASE = f"{BASE_URL}/config"

# Headers para autenticação (ajuste conforme seu sistema de auth)
HEADERS = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_TOKEN_HERE"  # Adicione token se necessário
}

def test_get_performance_thresholds():
    """Testa busca de thresholds de performance"""
    print("📋 Testando GET /config/performance-thresholds...")
    
    try:
        response = requests.get(f"{API_BASE}/performance-thresholds", headers=HEADERS)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data)} thresholds encontrados:")
            for threshold in data:
                print(f"  {threshold['metric_type']}: {threshold['warning_threshold']}%/{threshold['critical_threshold']}%")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_update_performance_threshold():
    """Testa atualização de threshold"""
    print("\n🔧 Testando PUT /config/performance-thresholds/1...")
    
    update_data = {
        "warning_threshold": 75,
        "critical_threshold": 85
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/performance-thresholds/1", 
            headers=HEADERS,
            json=update_data
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Threshold atualizado: {data['metric_type']} -> {data['warning_threshold']}%/{data['critical_threshold']}%")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_get_active_configs():
    """Testa busca de configurações ativas"""
    print("\n📊 Testando GET /config/active...")
    
    try:
        response = requests.get(f"{API_BASE}/active", headers=HEADERS)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Configurações ativas:")
            
            if data.get("performance_thresholds"):
                print(f"  Performance Thresholds: {len(data['performance_thresholds'])} configurados")
            
            if data.get("webhook"):
                print(f"  Webhook: {data['webhook']['url']}")
            
            if data.get("email"):
                print(f"  Email: {data['email']['email']}")
                
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def test_reset_defaults():
    """Testa reset para valores padrão"""
    print("\n🔄 Testando POST /config/performance-thresholds/reset-defaults...")
    
    try:
        response = requests.post(f"{API_BASE}/performance-thresholds/reset-defaults", headers=HEADERS)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

def main():
    print("🚀 Testando API de Performance Thresholds...\n")
    print("⚠️  Certifique-se de que o servidor está rodando em http://localhost:8000")
    print("⚠️  E que você tem permissões de administrador\n")
    
    test_get_performance_thresholds()
    test_get_active_configs()
    # test_update_performance_threshold()  # Descomente se quiser testar atualização
    # test_reset_defaults()  # Descomente se quiser testar reset
    
    print("\n📝 Exemplo de uso com curl:")
    print("""
# Buscar thresholds
curl -X GET http://localhost:8000/config/performance-thresholds

# Atualizar threshold de CPU
curl -X PUT http://localhost:8000/config/performance-thresholds/1 \\
  -H "Content-Type: application/json" \\
  -d '{"warning_threshold": 75, "critical_threshold": 85}'

# Reset para padrões
curl -X POST http://localhost:8000/config/performance-thresholds/reset-defaults
    """)

if __name__ == "__main__":
    main()
