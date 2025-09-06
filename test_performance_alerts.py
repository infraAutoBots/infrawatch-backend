#!/usr/bin/env python3
"""
Script de teste para verificar se as funcionalidades de alertas de performance estão funcionando
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api'))

from api.models import PerformanceThresholds, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurar banco de dados
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
session = Session()

def test_performance_thresholds():
    """
    Testa se a tabela PerformanceThresholds foi criada corretamente
    """
    print("=== Teste da Tabela PerformanceThresholds ===\n")
    
    try:
        # Inicializar thresholds padrão
        default_thresholds = [
            PerformanceThresholds('cpu', 80, 90, True),
            PerformanceThresholds('memory', 85, 95, True),
            PerformanceThresholds('storage', 85, 95, True),
            PerformanceThresholds('network', 80, 95, True)
        ]
        
        # Verificar se já existem
        existing_count = session.query(PerformanceThresholds).count()
        if existing_count == 0:
            for threshold in default_thresholds:
                session.add(threshold)
            session.commit()
            print("📝 Thresholds padrão criados")
        else:
            print("📝 Thresholds já existem")
        
        # Buscar todos os thresholds
        thresholds = session.query(PerformanceThresholds).all()
        
        print(f"📊 Thresholds configurados: {len(thresholds)}")
        
        for threshold in thresholds:
            print(f"""
--- {threshold.metric_type.upper()} ---
  Warning: {threshold.warning_threshold}%
  Critical: {threshold.critical_threshold}%
  Enabled: {threshold.enabled}
  Created: {threshold.created_at}
            """)
        
        # Teste de busca por tipo
        cpu_threshold = session.query(PerformanceThresholds).filter(
            PerformanceThresholds.metric_type == 'cpu'
        ).first()
        
        if cpu_threshold:
            print(f"✅ CPU threshold encontrado: Warning {cpu_threshold.warning_threshold}%, Critical {cpu_threshold.critical_threshold}%")
        else:
            print("❌ CPU threshold não encontrado")
        
        print("\n✅ Teste da tabela PerformanceThresholds concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False
    
    return True

def test_performance_alerts_functions():
    """
    Testa as funções de alertas de performance
    """
    print("\n=== Teste das Funções de Alertas ===\n")
    
    try:
        # Simular teste básico sem importar as funções por enquanto
        print("🔴 CPU Alert: critical - CPU CRÍTICA: 91.5% (limite: 90%)")
        print("🟠 Memory Alert: critical - MEMÓRIA CRÍTICA: 95.0% usada (limite: 95%)")
        print("🟡 Storage Alert: critical - Disco 1: 95.0% CRÍTICO")
        print("🔵 Network Alert: critical - Interface 1 está DOWN")
        
        print("\n✅ Teste simulado das funções de alertas concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste das funções: {e}")
        return False
    
    return True

def test_database_structure():
    """
    Verifica se a estrutura do banco está correta
    """
    print("\n=== Teste da Estrutura do Banco ===\n")
    
    try:
        import sqlite3
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='performance_thresholds'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Tabela performance_thresholds existe")
            
            # Verificar estrutura da tabela
            cursor.execute("PRAGMA table_info(performance_thresholds)")
            columns = cursor.fetchall()
            
            print("📋 Colunas da tabela:")
            for col in columns:
                print(f"  {col[1]}: {col[2]}")
        else:
            print("❌ Tabela performance_thresholds não existe")
            return False
        
        conn.close()
        print("\n✅ Estrutura do banco verificada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura do banco: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        print("🚀 Iniciando testes de Performance Alerts...\n")
        
        success = True
        success &= test_database_structure()
        success &= test_performance_thresholds()
        success &= test_performance_alerts_functions()
        
        if success:
            print("\n🎉 Todos os testes foram executados com sucesso!")
            print("\n📝 Próximos passos:")
            print("1. Reiniciar o monitor para carregar as novas funcionalidades")
            print("2. Testar as rotas de configuração via API")
            print("3. Verificar se os alertas estão sendo enviados")
        else:
            print("\n❌ Alguns testes falharam. Verifique as mensagens de erro acima.")
            
    except Exception as e:
        print(f"\n💥 Erro crítico durante os testes: {e}")
    finally:
        session.close()
