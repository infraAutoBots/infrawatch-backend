#!/bin/bash

# Script simples para executar testes de rotas - InfraWatch
# Para uma versão mais completa, use: run_route_tests.sh

API_BASE="http://localhost:8000"
TEST_DIR="/home/ubuntu/Code/infrawatch/infrawatch-backend/test"

echo "🧪 Executando testes de rotas da API InfraWatch..."
echo "API: $API_BASE"
echo "=========================================="

# Verificar se API está rodando
if ! curl -s -f "$API_BASE/docs" > /dev/null 2>&1; then
    echo "❌ API não está rodando em $API_BASE"
    echo "Execute: python api/app.py"
    exit 1
fi

echo "✅ API está rodando"
echo ""

cd "$TEST_DIR"

# Lista dos testes de rotas
ROUTE_TESTS=(
    "test_auth_api.py:Testes de Autenticação"
    "test_users_api.py:Testes de Usuários"
    "test_config_routes.py:Testes de Configuração"
    "test_alerts_routes.py:Testes de Alertas"
    "test_monitor_api.py:Testes de Monitoramento"
    "test_sla_routes.py:Testes de SLA"
)

PASSED=0
FAILED=0

# Executar cada teste
for test_info in "${ROUTE_TESTS[@]}"; do
    IFS=':' read -r test_file test_name <<< "$test_info"
    
    echo "▶ $test_name ($test_file)"
    
    if [ -f "$test_file" ]; then
        if python3 "$test_file"; then
            echo "✅ $test_name - SUCESSO"
            ((PASSED++))
        else
            echo "❌ $test_name - FALHOU"
            ((FAILED++))
        fi
    else
        echo "⚠️ Arquivo $test_file não encontrado"
        ((FAILED++))
    fi
    echo ""
done

# Executar teste bash se existir
if [ -f "test_routes.sh" ]; then
    echo "▶ Testes de Usuários (cURL)"
    if bash test_routes.sh; then
        echo "✅ Testes cURL - SUCESSO"
        ((PASSED++))
    else
        echo "❌ Testes cURL - FALHOU"
        ((FAILED++))
    fi
    echo ""
fi

# Resumo
TOTAL=$((PASSED + FAILED))
echo "=========================================="
echo "📊 RESUMO:"
echo "   Total: $TOTAL"
echo "   Passou: $PASSED"
echo "   Falhou: $FAILED"
echo "   Taxa de sucesso: $(( PASSED * 100 / TOTAL ))%"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo "🎉 Todos os testes passaram!"
    exit 0
else
    echo "⚠️ $FAILED teste(s) falharam"
    exit 1
fi
