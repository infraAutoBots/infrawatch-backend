#!/bin/bash

echo "🔍 Debug do Deploy Railway"
echo "=========================="

echo "📍 Diretório atual: $(pwd)"
echo "🐍 Versão Python: $(python --version)"
echo "📦 Pip version: $(pip --version)"

echo ""
echo "📁 Estrutura de arquivos:"
ls -la

echo ""
echo "📁 Estrutura API:"
ls -la api/

echo ""
echo "🧪 Teste de importação simples:"
python -c "print('Python funcionando!')"

echo ""
echo "🧪 Teste de importação FastAPI:"
python -c "from fastapi import FastAPI; print('FastAPI OK')"

echo ""
echo "🧪 Teste de importação da app simples:"
python -c "from api.simple_app import app; print('Simple App OK')"

echo ""
echo "🧪 Teste de importação da app principal:"
python -c "from api.app import app; print('Main App OK')" || echo "❌ Erro na app principal"

echo ""
echo "🌐 Testando servidor simples por 5 segundos..."
timeout 5s python -m uvicorn api.simple_app:app --host 0.0.0.0 --port 8000 || echo "Timeout atingido"

echo ""
echo "✅ Debug concluído!"
