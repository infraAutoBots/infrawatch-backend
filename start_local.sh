#!/bin/bash

# Script para rodar a aplicação localmente com configurações locais
echo "🏠 Iniciando aplicação em modo LOCAL..."
echo "📋 Carregando configurações locais (.env.local)..."

# Verifica se o arquivo .env.local existe
if [ ! -f ".env.local" ]; then
    echo "❌ Arquivo .env.local não encontrado!"
    echo "📝 Criando arquivo .env.local com configurações padrão..."
    cp .env .env.local
    # Substitui as configurações do Railway pelas locais
    sed -i 's|postgres.railway.internal|localhost|g' .env.local
    sed -i 's|railway|infrawatch_db|g' .env.local
    sed -i 's|postgres:hfpSwbMqZLZGRTZxQBNxMxSXNrbNXFGW|infrawatch:infrawatch|g' .env.local
fi

# Exporta as variáveis do .env.local
export $(grep -v '^#' .env.local | xargs)

echo "🐘 Usando PostgreSQL local: postgresql://infrawatch:***@localhost:5432/infrawatch_db"
echo "🚀 Iniciando servidor..."

# Roda a aplicação usando o Python do ambiente virtual ou sistema
if [ -f "venv/bin/python3" ]; then
    echo "🐍 Usando Python do ambiente virtual"
    venv/bin/python3 main.py
elif [ -f "/usr/bin/python3" ]; then
    echo "🐍 Usando Python3 do sistema"
    /usr/bin/python3 main.py
else
    echo "❌ Python não encontrado!"
    exit 1
fi
