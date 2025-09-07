#!/usr/bin/env python3
"""
Script de debug para identificar problemas na verificação SNMP do monitor
"""
import asyncio
import sys
import os
from datetime import datetime
from pprint import pprint

# Adicionar o diretório monitor ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'monitor'))

from monitor.utils import HostStatus, check_ip_for_snmp, select_snmp_authentication
from monitor.dependencies import init_session
from monitor.models import EndPoints, EndPointOIDs

def test_check_ip_for_snmp():
    """Testa a função check_ip_for_snmp com diferentes cenários"""
    print("=== Testando check_ip_for_snmp ===")
    
    # Caso 1: Host sem configuração SNMP
    host1 = HostStatus(
        ip="192.168.1.1",
        interval=30,
        # Sem configurações SNMP
    )
    print(f"Host sem SNMP: {check_ip_for_snmp(host1)}")
    
    # Caso 2: Host com configuração SNMP v2c
    host2 = HostStatus(
        ip="192.168.1.2",
        interval=30,
        version="2c",
        community="public",
        port=161
    )
    print(f"Host com SNMP v2c: {check_ip_for_snmp(host2)}")
    
    # Caso 3: Host com configuração SNMP v3
    host3 = HostStatus(
        ip="192.168.1.3",
        interval=30,
        version="3",
        user="snmpuser",
        authKey="authkey123",
        privKey="privkey123",
        port=161
    )
    print(f"Host com SNMP v3: {check_ip_for_snmp(host3)}")

def test_snmp_data_validation():
    """Testa como o sistema valida dados SNMP"""
    print("\n=== Testando validação de dados SNMP ===")
    
    # Caso 1: Dados SNMP válidos
    snmp_data1 = {
        'sysDescr': 'Linux server 5.4.0',
        'sysUpTime': '12345',
        'hrProcessorLoad': '25'
    }
    print(f"Dados válidos: {snmp_data1}")
    print(f"any(values): {any(snmp_data1.values())}")
    
    # Caso 2: Dados SNMP com valores None
    snmp_data2 = {
        'sysDescr': None,
        'sysUpTime': None,
        'hrProcessorLoad': None
    }
    print(f"Dados com None: {snmp_data2}")
    print(f"any(values): {any(snmp_data2.values())}")
    
    # Caso 3: Dados SNMP mistos
    snmp_data3 = {
        'sysDescr': 'Linux server 5.4.0',
        'sysUpTime': None,
        'hrProcessorLoad': None
    }
    print(f"Dados mistos: {snmp_data3}")
    print(f"any(values): {any(snmp_data3.values())}")
    
    # Caso 4: Dados SNMP vazios
    snmp_data4 = {}
    print(f"Dados vazios: {snmp_data4}")
    print(f"any(values): {any(snmp_data4.values())}")

def test_database_configuration():
    """Verifica as configurações SNMP no banco de dados"""
    print("\n=== Verificando configurações no banco ===")
    
    session = init_session()
    try:
        endpoints = session.query(EndPoints).limit(5).all()
        for endpoint in endpoints:
            print(f"\nEndpoint: {endpoint.ip}")
            print(f"  Nickname: {endpoint.nickname}")
            print(f"  Version: {endpoint.version}")
            print(f"  Community: {endpoint.community}")
            print(f"  Port: {endpoint.port}")
            print(f"  User: {endpoint.user}")
            print(f"  AuthKey: {'***' if endpoint.authKey else None}")
            print(f"  PrivKey: {'***' if endpoint.privKey else None}")
            
            # Testar check_ip_for_snmp
            host_status = HostStatus(
                _id=endpoint.id,
                ip=endpoint.ip,
                nickname=endpoint.nickname,
                interval=endpoint.interval,
                version=endpoint.version,
                community=endpoint.community,
                port=endpoint.port,
                user=endpoint.user,
                authKey=endpoint.authKey,
                privKey=endpoint.privKey
            )
            
            snmp_enabled = check_ip_for_snmp(host_status)
            print(f"  SNMP habilitado: {snmp_enabled}")
            
            if snmp_enabled:
                try:
                    auth_data = select_snmp_authentication(host_status)
                    print(f"  Auth data: {type(auth_data).__name__}")
                except Exception as e:
                    print(f"  Erro auth: {e}")
                    
            # Verificar OIDs
            oids = session.query(EndPointOIDs).filter_by(id_endpoint=endpoint.id).all()
            print(f"  OIDs configurados: {len(oids)}")
            for oid in oids:
                print(f"    {oid.name}: {oid.oid}")
                
    except Exception as e:
        print(f"Erro ao consultar banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("🔍 Debug do Monitor SNMP")
    print("=" * 50)
    
    test_check_ip_for_snmp()
    test_snmp_data_validation()
    test_database_configuration()
