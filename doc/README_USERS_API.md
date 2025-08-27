# API de Usuários - InfraWatch

## Implementação Completa das Rotas de Usuários

Esta implementação fornece todas as funcionalidades necessárias para gerenciar usuários no sistema InfraWatch, incluindo suporte completo à paginação, filtros e controle de permissões.

## 📁 Arquivos Implementados

### 1. **api/users_routes.py** - Rotas Principais
- `GET /users` - Lista usuários com paginação e filtros
- `POST /users` - Cria novo usuário  
- `GET /users/{id}` - Obtém usuário específico
- `PUT /users/{id}` - Atualiza usuário
- `DELETE /users/{id}` - Exclui usuário
- `PATCH /users/{id}/status` - Altera status do usuário
- `GET /users/stats/summary` - Estatísticas de usuários

### 2. **api/schemas.py** - Schemas Adicionados
- `UserResponseSchemas` - Schema de resposta de usuário
- `UserCreateSchemas` - Schema para criação de usuário
- `UserUpdateSchemas` - Schema para atualização de usuário
- `UserStatusUpdateSchemas` - Schema para alteração de status
- `UserStatsSchemas` - Schema de estatísticas
- `UserListResponse` - Schema de resposta de listagem

### 3. **api/models.py** - Modelo Atualizado
- Adicionados campos `created_at` e `updated_at` à tabela Users
- Migração automática aplicada com Alembic

### 4. **api/app.py** - App Principal Atualizado
- Importação das rotas de usuários
- Correção de imports para funcionar corretamente

## 🚀 Como Executar

### 1. Configurar Banco de Dados
```bash
cd /home/ubuntu/Code/infrawatch/infrawatch-backend
source jvenv/bin/activate  # ou o ambiente virtual correto
python create_admin_user.py
```

### 2. Iniciar API
```bash
python api/app.py
```

### 3. Testar Rotas
```bash
python test_users_api.py
```

## 📊 Funcionalidades Implementadas

### ✅ Listagem de Usuários (GET /users)
- **Paginação**: `?page=1&limit=10`
- **Busca**: `?search=nome_ou_email`
- **Filtros**:
  - Status: `?status=active|inactive`
  - Nível de acesso: `?access_level=ADMIN|MONITOR|VIEWER`
- **Combinação**: `?page=1&limit=5&search=joao&status=active&access_level=MONITOR`

### ✅ Criação de Usuário (POST /users)
```json
{
    "name": "João Silva",
    "email": "joao@empresa.com",
    "password": "senha123",
    "access_level": "MONITOR",
    "state": true
}
```

### ✅ Atualização de Usuário (PUT /users/{id})
- Atualização parcial (apenas campos fornecidos)
- Validação de email único
- Criptografia automática de senha
- Controle de permissões

### ✅ Controle de Status (PATCH /users/{id}/status)
```json
{
    "state": false
}
```

### ✅ Estatísticas Completas (GET /users/stats/summary)
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

## 🔐 Sistema de Permissões

### ADMIN
- ✅ Ver todos os usuários
- ✅ Criar usuários
- ✅ Editar qualquer usuário
- ✅ Excluir usuários
- ✅ Alterar status de usuários
- ✅ Ver estatísticas completas

### MONITOR
- ✅ Ver usuários ativos (limitado)
- ⚠️ Editar apenas próprio perfil
- ❌ Criar/excluir usuários
- ❌ Alterar status
- ✅ Ver estatísticas

### VIEWER
- ✅ Ver usuários ativos (limitado)
- ⚠️ Ver apenas próprio perfil
- ❌ Outras operações

## 🛡️ Segurança Implementada

### Validações
- Email único no sistema
- Níveis de acesso válidos (ADMIN, MONITOR, VIEWER)
- Não exclusão do último administrador
- Não autoexclusão/autodesativação
- Criptografia de senhas com bcrypt

### Proteções
- Autenticação JWT obrigatória
- Verificação de permissões por endpoint
- Validação de dados com Pydantic
- Proteção contra operações perigosas

## 📝 Exemplos de Uso

### Listar usuários com paginação
```bash
curl -X GET "http://localhost:8000/users?page=1&limit=5" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Buscar usuários por nome
```bash
curl -X GET "http://localhost:8000/users?search=joão" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Criar usuário
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Usuário",
    "email": "novo@empresa.com",
    "password": "senha123",
    "access_level": "MONITOR"
  }'
```

### Filtrar usuários ativos com acesso ADMIN
```bash
curl -X GET "http://localhost:8000/users?status=active&access_level=ADMIN" \
  -H "Authorization: Bearer SEU_TOKEN"
```

## 🔄 Paginação Detalhada

A paginação é implementada de forma robusta:

```json
{
  "users": [...],
  "total": 25,        // Total de registros
  "page": 2,          // Página atual
  "pages": 3,         // Total de páginas
  "stats": {...}      // Estatísticas incluídas
}
```

**Parâmetros de paginação:**
- `page`: Página atual (padrão: 1)
- `limit`: Itens por página (padrão: 10, máximo: 100)

**Exemplos:**
- `?page=1&limit=20` - Primeira página, 20 itens
- `?page=3&limit=5` - Terceira página, 5 itens
- `?limit=50` - Primeira página, 50 itens

## 🧪 Testes Automatizados

O arquivo `test_users_api.py` inclui:

- ✅ Teste de autenticação
- ✅ Teste de listagem com paginação
- ✅ Teste de busca e filtros
- ✅ Teste de criação de usuário
- ✅ Teste de atualização
- ✅ Teste de alteração de status
- ✅ Teste de exclusão
- ✅ Teste de estatísticas
- ✅ Relatório completo de resultados

## 📋 Códigos de Status HTTP

- `200 OK` - Operação bem-sucedida
- `201 Created` - Usuário criado com sucesso
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Sem permissão
- `404 Not Found` - Usuário não encontrado
- `409 Conflict` - Conflito (último admin, etc.)
- `422 Unprocessable Entity` - Erro de validação

## 🔧 Configuração Adicional

### Variáveis de Ambiente Sugeridas
```env
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=sua_chave_secreta_aqui
TOKEN_EXPIRE_MINUTES=30
```

### Melhorias Futuras Sugeridas
- Rate limiting nas rotas de criação/edição
- Logs de auditoria para operações críticas
- Soft delete em vez de exclusão física
- Cache para estatísticas
- Exportação de dados de usuários
- Histórico de alterações

## 🎯 Compatibilidade com Frontend

Esta implementação é totalmente compatível com a tela de usuários do frontend, fornecendo:

- Dados estruturados para os cards de estatísticas
- Listagem paginada para a tabela
- Busca em tempo real
- Filtros por status e perfil
- Todas as operações CRUD necessárias
- Responses no formato esperado pelo frontend React
