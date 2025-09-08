#!/bin/bash

# =============================================================================
# SCRIPT DE CORREÇÃO DE COMPATIBILIDADE - INFRAWATCH
# =============================================================================
# Corrige conflitos identificados entre schemas e dados existentes
# Data: 08/09/2025
# =============================================================================

echo "🔧 INFRAWATCH - CORREÇÃO DE COMPATIBILIDADE DE DADOS"
echo "===================================================="
echo "Data/Hora: $(date)"
echo ""

# Ativar ambiente virtual
source ../venv/bin/activate

# Verificar se a API está rodando
echo "🔍 Verificando conectividade com o banco..."
if ! sqlite3 ../database.db "SELECT COUNT(*) FROM users;" > /dev/null 2>&1; then
    echo "❌ Erro: Não foi possível conectar ao banco de dados"
    exit 1
fi
echo "✅ Conexão com banco estabelecida"
echo ""

# =============================================================================
# PROBLEMA 1: Valor inválido de impact em alerts
# =============================================================================
echo "🚨 CORREÇÃO 1: Valores inválidos de impact em alerts"
echo "------------------------------------------------"

# Verificar registros problemáticos
INVALID_IMPACT=$(sqlite3 ../database.db "SELECT COUNT(*) FROM alerts WHERE impact NOT IN ('high', 'medium', 'low');")
echo "📊 Registros com impact inválido encontrados: $INVALID_IMPACT"

if [ "$INVALID_IMPACT" -gt 0 ]; then
    echo "🔍 Registros problemáticos:"
    sqlite3 ../database.db "SELECT id, title, impact FROM alerts WHERE impact NOT IN ('high', 'medium', 'low');"
    
    echo ""
    echo "🔄 Corrigindo valores inválidos..."
    
    # Backup antes da correção
    echo "💾 Criando backup..."
    sqlite3 ../database.db ".dump alerts" > "../backup_alerts_$(date +%Y%m%d_%H%M%S).sql"
    
    # Corrigir valores inválidos
    sqlite3 ../database.db "UPDATE alerts SET impact = 'high' WHERE impact = 'host unreachable';"
    
    # Verificar correção
    REMAINING_INVALID=$(sqlite3 ../database.db "SELECT COUNT(*) FROM alerts WHERE impact NOT IN ('high', 'medium', 'low');")
    
    if [ "$REMAINING_INVALID" -eq 0 ]; then
        echo "✅ Correção concluída - Todos os valores de impact estão válidos"
    else
        echo "❌ Erro: Ainda existem $REMAINING_INVALID registros com valores inválidos"
    fi
else
    echo "✅ Nenhum valor inválido de impact encontrado"
fi

echo ""

# =============================================================================
# PROBLEMA 2: Nicknames vazios em endpoints
# =============================================================================
echo "🏷️ CORREÇÃO 2: Nicknames vazios em endpoints"
echo "--------------------------------------------"

# Verificar registros problemáticos
EMPTY_NICKNAMES=$(sqlite3 ../database.db "SELECT COUNT(*) FROM endpoints WHERE nickname IS NULL OR nickname = '';")
echo "📊 Endpoints com nickname vazio encontrados: $EMPTY_NICKNAMES"

if [ "$EMPTY_NICKNAMES" -gt 0 ]; then
    echo "🔍 Endpoints problemáticos:"
    sqlite3 ../database.db "SELECT id, ip, nickname FROM endpoints WHERE nickname IS NULL OR nickname = '';"
    
    echo ""
    echo "🔄 Preenchendo nicknames vazios..."
    
    # Backup antes da correção
    echo "💾 Criando backup..."
    sqlite3 ../database.db ".dump endpoints" > "../backup_endpoints_$(date +%Y%m%d_%H%M%S).sql"
    
    # Corrigir nicknames vazios
    sqlite3 ../database.db "UPDATE endpoints SET nickname = 'Endpoint-' || ip WHERE nickname IS NULL OR nickname = '';"
    
    # Verificar correção
    REMAINING_EMPTY=$(sqlite3 ../database.db "SELECT COUNT(*) FROM endpoints WHERE nickname IS NULL OR nickname = '';")
    
    if [ "$REMAINING_EMPTY" -eq 0 ]; then
        echo "✅ Correção concluída - Todos os endpoints têm nickname"
    else
        echo "❌ Erro: Ainda existem $REMAINING_EMPTY endpoints sem nickname"
    fi
else
    echo "✅ Todos os endpoints já têm nickname"
fi

echo ""

# =============================================================================
# VERIFICAÇÃO FINAL
# =============================================================================
echo "🔍 VERIFICAÇÃO FINAL DA COMPATIBILIDADE"
echo "======================================"

echo "1. Verificando valores de impact..."
FINAL_INVALID_IMPACT=$(sqlite3 ../database.db "SELECT COUNT(*) FROM alerts WHERE impact NOT IN ('high', 'medium', 'low');")
if [ "$FINAL_INVALID_IMPACT" -eq 0 ]; then
    echo "   ✅ Todos os valores de impact estão válidos"
else
    echo "   ❌ Ainda existem $FINAL_INVALID_IMPACT valores inválidos"
fi

echo "2. Verificando nicknames..."
FINAL_EMPTY_NICKNAMES=$(sqlite3 ../database.db "SELECT COUNT(*) FROM endpoints WHERE nickname IS NULL OR nickname = '';")
if [ "$FINAL_EMPTY_NICKNAMES" -eq 0 ]; then
    echo "   ✅ Todos os endpoints têm nickname"
else
    echo "   ❌ Ainda existem $FINAL_EMPTY_NICKNAMES endpoints sem nickname"
fi

echo ""

# Calcular status geral
TOTAL_ISSUES=$((FINAL_INVALID_IMPACT + FINAL_EMPTY_NICKNAMES))

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    echo "🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!"
    echo "   Todos os problemas de compatibilidade foram resolvidos."
    exit 0
else
    echo "⚠️  CORREÇÃO PARCIAL"
    echo "   Ainda existem $TOTAL_ISSUES problemas não resolvidos."
    exit 1
fi
