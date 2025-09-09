#!/bin/bash

# Script para alternar entre configurações locais e de produção

case "$1" in
    "local")
        echo "🏠 Configurando para ambiente LOCAL..."
        if [ -f .env.local ]; then
            cp .env.local .env
            echo "✅ Configuração local ativada (.env.local -> .env)"
            echo "📄 Banco: PostgreSQL local ou SQLite"
        else
            echo "❌ Arquivo .env.local não encontrado!"
            exit 1
        fi
        ;;
    "railway")
        echo "🚂 Configurando para ambiente RAILWAY..."
        if [ -f .env.railway ]; then
            cp .env.railway .env
            echo "✅ Configuração Railway ativada (.env.railway -> .env)"
        else
            echo "⚠️ Arquivo .env.railway não encontrado, criando..."
            # Criar configuração Railway
            cat > .env.railway << 'EOF'
SECRET_KEY=`xfTtVORL]z~gZYbZ&q@T3ti4es?QF*FONZM*bnCjQdncY`Z%>`/?k:6Jd&[GC]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurações da API
API_HOST=0.0.0.0
API_PORT=8000
MONITORING_INTERVAL=60

# Configurações SNMP
SNMP_VERSION=2c
SNMP_COMMUNITY=public
SNMP_PORT=161
SNMP_TIMEOUT=10.0
SNMP_RETRIES=2
SNMP_USER=meuUser
SNMP_AUTH_KEY=
SNMP_PRIV_KEY=

# Configurações TCP
TCP_TIMEOUT=3.0
TCP_PORTS=80,443,3306,5432,53,161

# Configurações de Logging
LOG_LEVEL=INFO
LOG_FILE=app.log

# Configuração PostgreSQL Railway (Produção)
DATABASE_URL=postgresql://postgres:hfpSwbMqZLZGRTZxQBNxMxSXNrbNXFGW@postgres.railway.internal:5432/railway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=hfpSwbMqZLZGRTZxQBNxMxSXNrbNXFGW
POSTGRES_HOST=postgres.railway.internal
POSTGRES_PORT=5432
POSTGRES_DB=railway

# Manter SQLite para backup local
SQLITE_DATABASE_URL=sqlite:///database.db
EOF
            cp .env.railway .env
            echo "✅ Configuração Railway criada e ativada"
        fi
        echo "🐘 Banco: PostgreSQL Railway"
        ;;
    "status")
        echo "📊 Status atual da configuração:"
        if [ -f .env ]; then
            if grep -q "railway.internal" .env; then
                echo "🚂 Configuração: RAILWAY"
                echo "🐘 Banco: PostgreSQL Railway"
            elif grep -q "localhost:5432" .env; then
                echo "🏠 Configuração: LOCAL (PostgreSQL)"
                echo "🐘 Banco: PostgreSQL local"
            else
                echo "🏠 Configuração: LOCAL (SQLite)"
                echo "📄 Banco: SQLite"
            fi
        else
            echo "❌ Arquivo .env não encontrado!"
        fi
        ;;
    *)
        echo "🔧 Script de configuração de ambiente"
        echo ""
        echo "Uso: $0 {local|railway|status}"
        echo ""
        echo "  local    - Configura para desenvolvimento local"
        echo "  railway  - Configura para produção Railway"
        echo "  status   - Mostra configuração atual"
        echo ""
        echo "Exemplos:"
        echo "  $0 local     # Usar PostgreSQL local ou SQLite"
        echo "  $0 railway   # Usar PostgreSQL Railway"
        echo "  $0 status    # Ver configuração atual"
        exit 1
        ;;
esac
