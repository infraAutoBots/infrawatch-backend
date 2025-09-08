#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para PostgreSQL
"""
import sqlite3
import os
import sys
import dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adicionar caminho do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import *


dotenv.load_dotenv()


def migrate_data():
    """Migra dados do SQLite para PostgreSQL"""
    
    # Conexão SQLite (origem)
    sqlite_path = os.path.join(os.path.dirname(__file__), 'database.db')
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
        
    # Conexão PostgreSQL (destino)
    postgres_url = os.getenv("DATABASE_URL")
    print(f"🔄 Conectando ao PostgreSQL em <{postgres_url}>...")
    if not postgres_url:
        print("❌ DATABASE_URL não configurada")
        return
    
    pg_engine = create_engine(postgres_url)
    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()
    
    try:
        print("🔄 Iniciando migração de dados...")
        
        # Migrar usuários
        print("👥 Migrando usuários...")
        cursor = sqlite_conn.execute("SELECT * FROM users")
        for row in cursor.fetchall():
            user = Users(
                id=row['id'],
                name=row['name'],
                email=row['email'],
                password=row['password'],
                access_level=row['access_level'],
                state=row['state'],
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at')
            )
            pg_session.merge(user)
        
        # Migrar endpoints
        print("🌐 Migrando endpoints...")
        cursor = sqlite_conn.execute("SELECT * FROM endpoints")
        for row in cursor.fetchall():
            endpoint = EndPoints(
                id=row['id'],
                ip=row['ip'],
                interval=row['interval'],
                version=row['version'],
                community=row['community'],
                port=row['port'],
                nickname=row.get('nickname'),
                id_usuario=row.get('id_usuario')
            )
            pg_session.merge(endpoint)
        
        # Migrar dados de endpoints
        print("📊 Migrando dados de endpoints...")
        cursor = sqlite_conn.execute("SELECT * FROM endpoints_data")
        for row in cursor.fetchall():
            endpoint_data = EndPointsData(
                id=row['id'],
                id_end_point=row['id_end_point'],
                status=row['status'],
                sysDescr=row.get('sysDescr'),
                sysName=row.get('sysName'),
                sysUpTime=row.get('sysUpTime'),
                last_updated=row.get('last_updated')
                # ... adicionar outros campos conforme necessário
            )
            pg_session.merge(endpoint_data)
        
        # Commit das mudanças
        pg_session.commit()
        print("✅ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        pg_session.rollback()
        
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate_data()