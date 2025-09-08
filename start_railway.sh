#!/bin/bash

# Startup script para Railway
echo "🚀 Iniciando aplicação InfraWatch..."
echo "📁 Diretório atual: $(pwd)"
echo "🐍 Versão do Python: $(python --version)"
echo "📦 Pacotes instalados:"
pip list | head -10

echo "🔍 Verificando estrutura do projeto..."
ls -la

echo "🔍 Verificando diretório api..."
ls -la api/

echo "🧪 Testando importação da aplicação..."
python -c "from api.app import app; print('✅ Aplicação importada com sucesso!')"

echo "🌐 Iniciando servidor..."
exec uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8000}
