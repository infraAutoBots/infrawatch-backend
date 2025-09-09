#!/usr/bin/env python3
"""
Script para inicializar o banco de dados PostgreSQL no Railway
Cria tabelas e dados iniciais necessários
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import Base, db, Users, get_database_url
from api.encryption import bcrypt_context
from sqlalchemy.orm import sessionmaker

def init_database():
    """Inicializa o banco de dados com tabelas e dados básicos."""
    
    print("🗄️ Inicializando banco de dados...")
    
    try:
        # Mostrar qual banco está sendo usado
        db_url = get_database_url()
        print(f"📊 Usando banco: {db_url[:50]}...")
        
        # Criar todas as tabelas
        print("📋 Criando tabelas...")
        Base.metadata.create_all(bind=db)
        print("✅ Tabelas criadas com sucesso!")
        
        # Criar sessão
        SessionLocal = sessionmaker(bind=db)
        session = SessionLocal()
        
        try:
            # Verificar se já existe usuário admin
            admin_user = session.query(Users).filter(Users.username == "admin").first()
            
            if not admin_user:
                print("👤 Criando usuário admin padrão...")
                
                # Criar usuário admin padrão
                hashed_password = bcrypt_context.hash("admin123")
                admin_user = Users(
                    username="admin",
                    email="admin@infrawatch.com",
                    first_name="Admin",
                    last_name="System",
                    hashed_password=hashed_password,
                    is_active=True,
                    access_level="ADMIN"
                )
                
                session.add(admin_user)
                session.commit()
                print("✅ Usuário admin criado!")
                print("   Username: admin")
                print("   Password: admin123")
                print("   ⚠️  ALTERE A SENHA EM PRODUÇÃO!")
            else:
                print("👤 Usuário admin já existe")
                
        except Exception as e:
            print(f"⚠️ Erro ao criar dados iniciais: {e}")
            session.rollback()
        finally:
            session.close()
            
        print("🎉 Inicialização do banco concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
