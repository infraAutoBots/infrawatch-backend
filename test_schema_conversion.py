#!/usr/bin/env python3
"""
Teste de conversão automática String ↔ Dict no Pydantic
"""

from api.schemas import EndPointsDataSchemas
import json

def test_schema_conversion():
    print("🧪 Testando conversão automática String ↔ Dict...\n")

    # Teste 1: String JSON válida
    print("📋 Teste 1: String JSON → Lista de Dicts")
    data1 = {
        'id_end_point': 1,
        'status': True,
        'sysDescr': 'Test System',
        'sysName': 'test-host',
        'sysUpTime': '12345',
        'hrProcessorLoad': "[{'index': '1', 'value': '23'}, {'index': '2', 'value': '31'}]",
        'memTotalReal': '8192',
        'memAvailReal': '4096',
        'hrStorageSize': "[{'index': '1', 'value': '500000'}]",
        'hrStorageUsed': "[{'index': '1', 'value': '250000'}]",
        'last_updated': '2025-09-06T10:30:00'
    }

    try:
        result1 = EndPointsDataSchemas(**data1)
        print(f"✅ Sucesso! hrProcessorLoad: {result1.hrProcessorLoad}")
        print(f"   Tipo: {type(result1.hrProcessorLoad)}")
        print(f"   Primeiro item: {result1.hrProcessorLoad[0] if result1.hrProcessorLoad else 'None'}")
    except Exception as e:
        print(f"❌ Falhou: {e}")

    print("\n" + "="*60 + "\n")

    # Teste 2: Lista direta
    print("📋 Teste 2: Lista de Dicts → Lista de Dicts")
    data2 = {
        'id_end_point': 1,
        'status': True,
        'sysDescr': 'Test System',
        'sysName': 'test-host',
        'sysUpTime': '12345',
        'hrProcessorLoad': [{'index': '1', 'value': '23'}],
        'memTotalReal': '8192',
        'memAvailReal': '4096',
        'hrStorageSize': [{'index': '1', 'value': '500000'}],
        'hrStorageUsed': [{'index': '1', 'value': '250000'}],
        'last_updated': '2025-09-06T10:30:00'
    }

    try:
        result2 = EndPointsDataSchemas(**data2)
        print(f"✅ Sucesso! hrProcessorLoad: {result2.hrProcessorLoad}")
        print(f"   Tipo: {type(result2.hrProcessorLoad)}")
    except Exception as e:
        print(f"❌ Falhou: {e}")

    print("\n" + "="*60 + "\n")

    # Teste 3: String vazia
    print("📋 Teste 3: String Vazia → None")
    data3 = {
        'id_end_point': 1,
        'status': True,
        'sysDescr': 'Test System',
        'sysName': 'test-host',
        'sysUpTime': '12345',
        'hrProcessorLoad': '',
        'memTotalReal': '8192',
        'memAvailReal': '4096',
        'hrStorageSize': '',
        'hrStorageUsed': '[]',
        'last_updated': '2025-09-06T10:30:00'
    }

    try:
        result3 = EndPointsDataSchemas(**data3)
        print(f"✅ Sucesso! hrProcessorLoad: {result3.hrProcessorLoad}")
        print(f"   Tipo: {type(result3.hrProcessorLoad)}")
    except Exception as e:
        print(f"❌ Falhou: {e}")

if __name__ == "__main__":
    test_schema_conversion()
