#!/bin/bash
# Script de teste das rotas de usuários usando curl
# Execute com: bash test_routes.sh

API_BASE="http://localhost:8000"
TOKEN=""

echo "🚀 Testando API de Usuários - InfraWatch"
echo "========================================"

# Função para fazer login e obter token
login() {
    echo "🔐 Fazendo login..."
    
    RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@empresa.com",
            "password": "admin123"
        }')
    
    TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        echo "✅ Login realizado com sucesso"
        echo "🔑 Token: ${TOKEN:0:20}..."
    else
        echo "❌ Falha no login"
        echo "Resposta: $RESPONSE"
        exit 1
    fi
}

# Função para testar listagem de usuários
test_list_users() {
    echo -e "\n📋 Testando listagem de usuários..."
    
    echo "1. Listagem básica:"
    curl -s -X GET "$API_BASE/users" \
        -H "Authorization: Bearer $TOKEN" | jq .
    
    echo -e "\n2. Com paginação (página 1, 3 itens):"
    curl -s -X GET "$API_BASE/users?page=1&limit=3" \
        -H "Authorization: Bearer $TOKEN" | jq .
    
    echo -e "\n3. Busca por 'admin':"
    curl -s -X GET "$API_BASE/users?search=admin" \
        -H "Authorization: Bearer $TOKEN" | jq .
    
    echo -e "\n4. Filtro de usuários ativos:"
    curl -s -X GET "$API_BASE/users?status=active" \
        -H "Authorization: Bearer $TOKEN" | jq .
    
    echo -e "\n5. Filtro por nível ADMIN:"
    curl -s -X GET "$API_BASE/users?access_level=ADMIN" \
        -H "Authorization: Bearer $TOKEN" | jq .
}

# Função para testar criação de usuário
test_create_user() {
    echo -e "\n➕ Testando criação de usuário..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    RESPONSE=$(curl -s -X POST "$API_BASE/users" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"Teste Usuario $TIMESTAMP\",
            \"email\": \"teste_$TIMESTAMP@exemplo.com\",
            \"password\": \"senha123\",
            \"access_level\": \"MONITOR\",
            \"state\": true
        }")
    
    echo "$RESPONSE" | jq .
    
    # Extrair ID do usuário criado
    USER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "🆔 Usuário criado com ID: $USER_ID"
    
    return $USER_ID
}

# Função para testar obtenção de usuário específico
test_get_user() {
    local user_id=$1
    echo -e "\n👤 Testando obtenção do usuário $user_id..."
    
    curl -s -X GET "$API_BASE/users/$user_id" \
        -H "Authorization: Bearer $TOKEN" | jq .
}

# Função para testar atualização de usuário
test_update_user() {
    local user_id=$1
    echo -e "\n✏️ Testando atualização do usuário $user_id..."
    
    curl -s -X PUT "$API_BASE/users/$user_id" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Usuario Atualizado",
            "access_level": "VIEWER"
        }' | jq .
}

# Função para testar alteração de status
test_update_status() {
    local user_id=$1
    echo -e "\n🔄 Testando alteração de status do usuário $user_id..."
    
    echo "Desativando usuário:"
    curl -s -X PATCH "$API_BASE/users/$user_id/status" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"state": false}' | jq .
    
    sleep 1
    
    echo -e "\nReativando usuário:"
    curl -s -X PATCH "$API_BASE/users/$user_id/status" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"state": true}' | jq .
}

# Função para testar estatísticas
test_stats() {
    echo -e "\n📊 Testando estatísticas..."
    
    curl -s -X GET "$API_BASE/users/stats/summary" \
        -H "Authorization: Bearer $TOKEN" | jq .
}

# Função para testar exclusão de usuário
test_delete_user() {
    local user_id=$1
    echo -e "\n🗑️ Testando exclusão do usuário $user_id..."
    
    curl -s -X DELETE "$API_BASE/users/$user_id" \
        -H "Authorization: Bearer $TOKEN" | jq .
}

# Função principal
main() {
    # Verificar se jq está instalado
    if ! command -v jq &> /dev/null; then
        echo "⚠️ jq não está instalado. Instalando..."
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    # Fazer login
    login
    
    # Testar listagem
    test_list_users
    
    # Criar usuário para testes
    test_create_user
    USER_ID=$?
    
    if [ $USER_ID -gt 0 ]; then
        # Testar operações com o usuário criado
        test_get_user $USER_ID
        test_update_user $USER_ID
        test_update_status $USER_ID
        
        # Testar estatísticas
        test_stats
        
        # Excluir usuário de teste
        test_delete_user $USER_ID
    fi
    
    echo -e "\n🎉 Testes concluídos!"
}

# Verificar se a API está rodando
echo "🔍 Verificando se a API está rodando..."
if curl -s -f "$API_BASE/docs" > /dev/null; then
    echo "✅ API está rodando"
    main
else
    echo "❌ API não está rodando em $API_BASE"
    echo "Execute: python api/app.py"
    exit 1
fi
