#!/bin/bash

# Script para diagnosticar e corrigir problemas nos testes
# Execute com: bash fix_test_issues.sh

echo "🔧 DIAGNÓSTICO E CORREÇÃO DOS TESTES"
echo "==================================="

# 1. Verificar problema no test_config_routes.py
echo "1. 📧 Verificando problema de configuração de email..."

# Vamos ajustar o test_config_routes.py para lidar com o erro de schema
python3 << 'EOF'
import sys
import os

# Verificar se o problema está no schema
try:
    sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend')
    from api.schemas import EmailConfigSchema
    
    # Verificar se tem atributo 'active'
    schema_fields = EmailConfigSchema.model_fields if hasattr(EmailConfigSchema, 'model_fields') else EmailConfigSchema.__fields__
    print(f"Campos do EmailConfigSchema: {list(schema_fields.keys())}")
    
    if 'active' not in schema_fields:
        print("❌ Campo 'active' não existe no EmailConfigSchema")
        print("✅ Isso explica o erro no teste")
    else:
        print("✅ Campo 'active' existe no schema")
        
except Exception as e:
    print(f"❌ Erro ao verificar schema: {e}")
EOF

echo ""

# 2. Verificar problema no test_alerts_routes.py  
echo "2. 🚨 Verificando problema de alertas..."

# Vamos verificar o schema de alertas
python3 << 'EOF'
import sys
import os

try:
    sys.path.append('/home/ubuntu/Code/infrawatch/infrawatch-backend')
    from api.schemas import AlertWithLogsSchema
    
    # Verificar campos do schema
    schema_fields = AlertWithLogsSchema.model_fields if hasattr(AlertWithLogsSchema, 'model_fields') else AlertWithLogsSchema.__fields__
    print(f"Campos do AlertWithLogsSchema: {list(schema_fields.keys())}")
    
    # Verificar especificamente o campo impact
    if 'impact' in schema_fields:
        impact_field = schema_fields['impact']
        print(f"Campo impact: {impact_field}")
        
except Exception as e:
    print(f"❌ Erro ao verificar schema de alertas: {e}")
EOF

echo ""

# 3. Verificar problema de autenticação no monitor
echo "3. 🔍 Verificando problema de autenticação no monitor..."

# Verificar se o test_monitor_api.py está usando autenticação correta
grep -n "TEST_CREDENTIALS\|email\|password" /home/ubuntu/Code/infrawatch/infrawatch-backend/test/test_monitor_api.py | head -5

echo ""

# 4. Sugerir correções
echo "🎯 SUGESTÕES DE CORREÇÃO:"
echo "========================"

echo "1. Para test_config_routes.py:"
echo "   - Remover campo 'active' do teste de criação de email"
echo "   - Ou adicionar campo 'active' ao EmailConfigSchema"

echo ""
echo "2. Para test_alerts_routes.py:"
echo "   - Corrigir valores de 'impact' para usar apenas: 'high', 'medium', 'low'"
echo "   - Verificar relacionamento alert_logs.user para não retornar None"

echo ""
echo "3. Para test_monitor_api.py:"
echo "   - Garantir que autenticação está sendo feita antes de cada teste"
echo "   - Adicionar retry em caso de 401"

echo ""
echo "4. Para melhorar robustez geral:"
echo "   - Adicionar timeouts nos testes"
echo "   - Implementar retry em caso de falhas de conexão"
echo "   - Validar dados antes de enviar para API"

echo ""
echo "🔧 Executando correções automáticas..."
echo "====================================="

# Correção 1: Atualizar credenciais do test_monitor_api.py se necessário
if grep -q "admin@empresa.com" /home/ubuntu/Code/infrawatch/infrawatch-backend/test/test_monitor_api.py; then
    echo "✅ Corrigindo credenciais em test_monitor_api.py..."
    sed -i 's/admin@empresa.com/ndondadaniel2020@gmail.com/g' /home/ubuntu/Code/infrawatch/infrawatch-backend/test/test_monitor_api.py
    sed -i 's/admin123/ndondadaniel2020@gmail.com/g' /home/ubuntu/Code/infrawatch/infrawatch-backend/test/test_monitor_api.py
    echo "✅ Credenciais corrigidas"
else
    echo "✅ Credenciais do test_monitor_api.py já estão corretas"
fi

echo ""
echo "✅ Diagnóstico concluído!"
echo "📋 Veja as sugestões acima para corrigir os problemas restantes."
