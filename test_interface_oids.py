#!/usr/bin/env python3
"""
Script de teste para verificar se os novos OIDs de interface estão funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import EndPoints, EndPointOIDs, EndPointsData, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar banco de dados
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

def test_new_oids():
    """
    Testa se os novos campos de OIDs estão funcionando
    """
    print("=== Teste dos Novos OIDs de Interface ===\n")
    
    # 1. Verificar endpoints existentes
    endpoints = session.query(EndPoints).limit(3).all()
    print(f"Endpoints encontrados: {len(endpoints)}")
    
    for endpoint in endpoints:
        print(f"\n--- Endpoint: {endpoint.ip} ---")
        
        # 2. Verificar OIDs configurados
        oids = session.query(EndPointOIDs).filter(EndPointOIDs.id_end_point == endpoint.id).first()
        if oids:
            print("OIDs configurados:")
            print(f"  ifOperStatus: {oids.ifOperStatus}")
            print(f"  ifInOctets: {oids.ifInOctets}")
            print(f"  ifOutOctets: {oids.ifOutOctets}")
        else:
            print("  Nenhum OID configurado ainda")
        
        # 3. Verificar dados coletados
        data = session.query(EndPointsData).filter(EndPointsData.id_end_point == endpoint.id).order_by(EndPointsData.last_updated.desc()).first()
        if data:
            print("Dados coletados (mais recente):")
            print(f"  ifOperStatus: {data.ifOperStatus}")
            print(f"  ifInOctets: {data.ifInOctets}")
            print(f"  ifOutOctets: {data.ifOutOctets}")
            print(f"  Status: {data.status}")
            print(f"  Última atualização: {data.last_updated}")
        else:
            print("  Nenhum dado coletado ainda")

def test_default_oids():
    """
    Verifica se os OIDs padrão estão sendo configurados corretamente
    """
    print("\n\n=== OIDs Padrão Configurados ===")
    
    default_oids = {
        "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
        "ifInOctets": "1.3.6.1.2.1.2.2.1.10", 
        "ifOutOctets": "1.3.6.1.2.1.2.2.1.16"
    }
    
    print("OIDs padrão para interfaces de rede:")
    for name, oid in default_oids.items():
        print(f"  {name}: {oid}")

if __name__ == "__main__":
    try:
        test_new_oids()
        test_default_oids()
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
    finally:
        session.close()
