#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para PostgreSQL
Uso: python migrate_sqlite_to_postgres.py
"""
import os
import sqlite3
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar caminho do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import *

def migrate_data():
    """Migra dados do SQLite para PostgreSQL"""
    
    # Configurações
    sqlite_path = os.path.join(os.path.dirname(__file__), 'database.db')
    postgres_url = os.getenv("DATABASE_URL")
    
    if not os.path.exists(sqlite_path):
        print("❌ Arquivo SQLite não encontrado:", sqlite_path)
        return False
    
    if not postgres_url:
        print("❌ DATABASE_URL não configurada")
        return False
    
    print(f"🔄 Migrando dados de SQLite para PostgreSQL...")
    print(f"📂 SQLite: {sqlite_path}")
    print(f"🐘 PostgreSQL: {postgres_url}")
    
    try:
        # Conexão SQLite (origem)
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Conexão PostgreSQL (destino)
        pg_engine = create_engine(postgres_url)
        Session = sessionmaker(bind=pg_engine)
        pg_session = Session()
        
        # Migrar usuários
        print("\n👥 Migrando usuários...")
        cursor = sqlite_conn.execute("SELECT * FROM users")
        user_count = 0
        for row in cursor.fetchall():
            try:
                # Verificar se usuário já existe
                existing = pg_session.query(Users).filter(Users.email == row['email']).first()
                if existing:
                    print(f"  ⚠️  Usuário já existe: {row['email']}")
                    continue
                
                user = Users(
                    name=row['name'],
                    email=row['email'],
                    password=row['password'],
                    state=bool(row['state']),
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    access_level=row['access_level'],
                    url=row['url'] if 'url' in row.keys() else None,
                    alert=bool(row['alert']) if 'alert' in row.keys() else True
                )
                pg_session.add(user)
                user_count += 1
                print(f"  ✅ {row['name']} ({row['email']})")
            except Exception as e:
                print(f"  ❌ Erro ao migrar usuário {row.get('email', 'N/A')}: {e}")
        
        # Migrar endpoints
        print(f"\n🌐 Migrando endpoints...")
        cursor = sqlite_conn.execute("SELECT * FROM endpoints")
        endpoint_count = 0
        for row in cursor.fetchall():
            try:
                # Verificar se endpoint já existe
                existing = pg_session.query(EndPoints).filter(EndPoints.ip == row['ip']).first()
                if existing:
                    print(f"  ⚠️  Endpoint já existe: {row['ip']}")
                    continue
                
                endpoint = EndPoints(
                    ip=row['ip'],
                    interval=row['interval'],
                    version=row['version'],
                    community=row['community'],
                    port=row['port'],
                    user=row['user'] if 'user' in row.keys() else None,
                    authKey=row['authKey'] if 'authKey' in row.keys() else None,
                    privKey=row['privKey'] if 'privKey' in row.keys() else None,
                    nickname=row['nickname'],
                    id_usuario=row['id_usuario'],
                    active=bool(row['active'])
                )
                pg_session.add(endpoint)
                endpoint_count += 1
                print(f"  ✅ {row['ip']} ({row.get('nickname', 'N/A')})")
            except Exception as e:
                print(f"  ❌ Erro ao migrar endpoint {row.get('ip', 'N/A')}: {e}")
        
        # Commit das mudanças
        pg_session.commit()
        
        print(f"\n✅ Migração concluída com sucesso!")
        print(f"📊 Usuários migrados: {user_count}")
        print(f"📊 Endpoints migrados: {endpoint_count}")
        
        # Verificar dados no PostgreSQL
        total_users = pg_session.query(Users).count()
        total_endpoints = pg_session.query(EndPoints).count()
        print(f"📈 Total no PostgreSQL: {total_users} usuários, {total_endpoints} endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        pg_session.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_session.close()

def verify_migration():
    """Verifica se a migração foi bem-sucedida"""
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL não configurada")
        return
    
    try:
        pg_engine = create_engine(postgres_url)
        Session = sessionmaker(bind=pg_engine)
        pg_session = Session()
        
        print("\n🔍 Verificando dados migrados...")
        
        # Verificar usuários
        users = pg_session.query(Users).all()
        print(f"👥 Usuários ({len(users)}):")
        for user in users[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {user.name} ({user.email}) - {user.access_level}")
        if len(users) > 5:
            print(f"  ... e mais {len(users) - 5} usuários")
        
        # Verificar endpoints
        endpoints = pg_session.query(EndPoints).all()
        print(f"\n🌐 Endpoints ({len(endpoints)}):")
        for endpoint in endpoints[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {endpoint.ip} ({endpoint.nickname or 'Sem nome'})")
        if len(endpoints) > 5:
            print(f"  ... e mais {len(endpoints) - 5} endpoints")
            
        pg_session.close()
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🐘➡️📦 Migração SQLite → PostgreSQL")
    print("=" * 50)
    
    # Executar migração
    success = migrate_data()
    
    if success:
        # Verificar resultados
        verify_migration()
        print("\n🎉 Migração concluída! Você pode agora usar PostgreSQL.")
        print("💡 Para testar: python -c \"from api.models import *; print('OK')\"")
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
