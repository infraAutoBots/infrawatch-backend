#!/usr/bin/env python3
"""
Script de teste para verificar se as APIs de SLA estão funcionando corretamente.
"""
import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """Testa se a API está respondendo"""
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        print(f"✅ API Status: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ API não está respondendo: {e}")
        return False

def test_sla_endpoints():
    """Testa os endpoints de SLA (sem autenticação por enquanto)"""
    endpoints = [
        "/sla/summary",
        "/sla/compliance",
        # "/sla/endpoint/1",  # Só testa se houver endpoints cadastrados
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔍 Testando {endpoint}...")
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
            
            if response.status_code == 401:
                print(f"🔐 Endpoint requer autenticação (esperado): {response.status_code}")
            elif response.status_code == 200:
                print(f"✅ Endpoint funcionando: {response.status_code}")
                # Tentar parsear JSON
                try:
                    data = response.json()
                    print(f"📊 Dados retornados: {len(str(data))} caracteres")
                except json.JSONDecodeError:
                    print("⚠️ Resposta não é JSON válido")
            else:
                print(f"❌ Erro no endpoint: {response.status_code}")
                print(f"📄 Resposta: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de conexão: {e}")

def check_database_tables():
    """Verifica se as tabelas foram criadas no banco"""
    import sqlite3
    import os
    
    db_path = "/home/ubuntu/Code/infrawatch/infrawatch-backend/database.db"
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas de SLA
        tables = ['sla_metrics', 'incidents', 'performance_metrics']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Tabela {table}: existe ({count} registros)")
            else:
                print(f"❌ Tabela {table}: não existe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")

def main():
    print("🚀 TESTE DAS FUNCIONALIDADES DE SLA")
    print("=" * 50)
    
    print("\n1. Verificando tabelas do banco de dados...")
    check_database_tables()
    
    print("\n2. Testando conectividade da API...")
    if test_api_health():
        print("\n3. Testando endpoints de SLA...")
        test_sla_endpoints()
    else:
        print("❌ API não está acessível. Verifique se está rodando.")
    
    print("\n" + "=" * 50)
    print("🏁 Teste concluído!")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
