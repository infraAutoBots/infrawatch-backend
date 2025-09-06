#!/usr/bin/env python3
"""
Script para atualizar endpoints existentes com os novos OIDs de interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import EndPoints, EndPointOIDs, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar banco de dados
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

def update_existing_endpoints():
    """
    Atualiza endpoints existentes com os novos OIDs de interface
    """
    print("=== Atualizando Endpoints Existentes ===\n")
    
    # OIDs padrão para interfaces de rede
    default_interface_oids = {
        "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
        "ifInOctets": "1.3.6.1.2.1.2.2.1.10", 
        "ifOutOctets": "1.3.6.1.2.1.2.2.1.16"
    }
    
    # Buscar todas as configurações de OIDs existentes
    all_oids = session.query(EndPointOIDs).all()
    
    updated_count = 0
    for oid_config in all_oids:
        endpoint = session.query(EndPoints).filter(EndPoints.id == oid_config.id_end_point).first()
        
        if endpoint:
            print(f"Atualizando endpoint: {endpoint.ip}")
            
            # Atualizar apenas se os campos estão vazios
            if not oid_config.ifOperStatus:
                oid_config.ifOperStatus = default_interface_oids["ifOperStatus"]
                print(f"  + ifOperStatus: {default_interface_oids['ifOperStatus']}")
            
            if not oid_config.ifInOctets:
                oid_config.ifInOctets = default_interface_oids["ifInOctets"]
                print(f"  + ifInOctets: {default_interface_oids['ifInOctets']}")
            
            if not oid_config.ifOutOctets:
                oid_config.ifOutOctets = default_interface_oids["ifOutOctets"]
                print(f"  + ifOutOctets: {default_interface_oids['ifOutOctets']}")
            
            updated_count += 1
    
    # Commit das mudanças
    session.commit()
    print(f"\n✅ {updated_count} endpoints atualizados com sucesso!")

if __name__ == "__main__":
    try:
        update_existing_endpoints()
    except Exception as e:
        print(f"\n❌ Erro durante a atualização: {e}")
        session.rollback()
    finally:
        session.close()
