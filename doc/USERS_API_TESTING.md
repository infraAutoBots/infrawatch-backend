# Testando as Rotas de Usuários - API InfraWatch

## Como testar as rotas

### 1. Iniciar o servidor
```bash
cd /home/ubuntu/Code/infrawatch/infrawatch-backend
source jvenv/bin/activate
python api/app.py
```

### 2. Obter token de autenticação (fazer login)
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@empresa.com",
    "password": "senha_admin"
  }'
```

### 3. Usar o token nas próximas requisições
```bash
# Substitua SEU_TOKEN_AQUI pelo token recebido do login
export TOKEN="SEU_TOKEN_AQUI"
```

### 4. Testar as rotas de usuários

#### Listar usuários (com paginação)
```bash
# Listar primeira página (10 usuários)
curl -X GET "http://localhost:8000/users" \
  -H "Authorization: Bearer $TOKEN"

# Listar segunda página com limite de 5
curl -X GET "http://localhost:8000/users?page=2&limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Buscar usuários por nome/email
curl -X GET "http://localhost:8000/users?search=joao" \
  -H "Authorization: Bearer $TOKEN"

# Filtrar usuários ativos
curl -X GET "http://localhost:8000/users?status=active" \
  -H "Authorization: Bearer $TOKEN"

# Filtrar por nível de acesso
curl -X GET "http://localhost:8000/users?access_level=ADMIN" \
  -H "Authorization: Bearer $TOKEN"

# Combinar filtros
curl -X GET "http://localhost:8000/users?page=1&limit=20&search=silva&status=active&access_level=MONITOR" \
  -H "Authorization: Bearer $TOKEN"
```

#### Criar usuário
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao.silva@empresa.com",
    "password": "senha123",
    "access_level": "MONITOR",
    "state": true
  }'
```

#### Obter usuário específico
```bash
# Substitua 1 pelo ID do usuário
curl -X GET "http://localhost:8000/users/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### Atualizar usuário
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva Santos",
    "email": "joao.silva.santos@empresa.com",
    "access_level": "ADMIN"
  }'
```

#### Alterar senha de usuário
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "nova_senha456"
  }'
```

#### Alterar status do usuário
```bash
# Desativar usuário
curl -X PATCH "http://localhost:8000/users/1/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "state": false
  }'

# Ativar usuário
curl -X PATCH "http://localhost:8000/users/1/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "state": true
  }'
```

#### Excluir usuário
```bash
curl -X DELETE "http://localhost:8000/users/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### Obter estatísticas de usuários
```bash
curl -X GET "http://localhost:8000/users/stats/summary" \
  -H "Authorization: Bearer $TOKEN"
```

## Exemplos de Respostas

### Lista de usuários
```json
{
  "users": [
    {
      "id": 1,
      "name": "João Silva",
      "email": "joao.silva@empresa.com",
      "access_level": "ADMIN",
      "state": true,
      "last_login": "2024-01-15T14:30:00",
      "created_at": "2024-01-01T10:00:00"
    }
  ],
  "total": 12,
  "page": 1,
  "pages": 2,
  "stats": {
    "total_users": 12,
    "admins": 2,
    "monitors": 7,
    "viewers": 3,
    "active_users": 10,
    "inactive_users": 2
  }
}
```

### Estatísticas de usuários
```json
{
  "total_users": 12,
  "admins": 2,
  "monitors": 7,
  "viewers": 3,
  "active_users": 10,
  "inactive_users": 2
}
```

### Criar usuário (sucesso)
```json
{
  "message": "Usuário criado com sucesso",
  "user": {
    "id": 13,
    "name": "Maria Santos",
    "email": "maria.santos@empresa.com",
    "access_level": "MONITOR",
    "state": true,
    "created_at": "2024-01-15T15:30:00"
  }
}
```

### Erro - Email já existe
```json
{
  "detail": "Email already registered"
}
```

### Erro - Permissão negada
```json
{
  "detail": "Operation not permitted. Admin access required."
}
```

## Códigos de Status HTTP

- `200 OK` - Operação bem-sucedida
- `201 Created` - Recurso criado com sucesso
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Token inválido ou ausente
- `403 Forbidden` - Sem permissão para a operação
- `404 Not Found` - Recurso não encontrado
- `409 Conflict` - Conflito (ex: último admin, autoexclusão)
- `422 Unprocessable Entity` - Erro de validação

## Permissões por Nível de Acesso

### ADMIN
- ✅ Todas as operações de usuários
- ✅ Ver todos os usuários
- ✅ Criar, editar, excluir usuários
- ✅ Alterar status de usuários
- ✅ Ver estatísticas completas

### MONITOR
- ✅ Visualizar usuários ativos (limitado)
- ⚠️ Editar apenas próprio perfil (sem alterar access_level)
- ❌ Criar, excluir usuários
- ❌ Alterar status de outros usuários
- ✅ Ver estatísticas básicas

### VIEWER  
- ✅ Visualizar usuários ativos (limitado)
- ⚠️ Ver apenas próprio perfil
- ❌ Todas as outras operações de modificação
