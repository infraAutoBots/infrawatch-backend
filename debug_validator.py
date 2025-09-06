#!/usr/bin/env python3
"""
Debug do field_validator
"""

import json

def debug_validator():
    test_values = [
        "[{'index': '1', 'value': '23'}, {'index': '2', 'value': '31'}]",
        [{'index': '1', 'value': '23'}],
        "",
        "[]",
        None
    ]
    
    for i, v in enumerate(test_values, 1):
        print(f"\n🔍 Teste {i}: {repr(v)}")
        
        if v is None:
            print("   → Retorna None (é None)")
            continue
            
        if isinstance(v, str):
            print("   → É string")
            if v.strip() == "" or v.strip() == "[]":
                print("   → String vazia ou array vazio, retorna None")
                continue
            try:
                parsed = json.loads(v)
                print(f"   → JSON parse sucesso: {parsed}")
                if isinstance(parsed, list):
                    print(f"   → É lista, retorna: {parsed}")
                else:
                    print("   → Não é lista, retorna None")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"   → JSON parse falhou: {e}")
                continue
        elif isinstance(v, list):
            print(f"   → É lista, retorna: {v}")
        else:
            print("   → Tipo desconhecido, retorna None")

if __name__ == "__main__":
    debug_validator()
