# Documentação das Rotas de API - Tela de Usuários

## Visão Geral
Esta documentação descreve as rotas de API necessárias para implementar completamente as funcionalidades da tela de usuários no frontend do sistema InfraWatch.

## Estrutura de Dados do Usuário

### Modelo User (baseado no código atual)
```python
{
    "id": int,
    "name": string,
    "email": string,
    "password": string (hash),
    "state": boolean,
    "last_login": datetime,
    "access_level": string ("ADMIN", "MONITOR", "VIEWER")
}
```

### Mapeamento de Perfis (Frontend → Backend)
- **Admin** → `ADMIN`
- **Operador** → `MONITOR` 
- **Visualizador** → `VIEWER`

---

## Rotas Necessárias

### 1. **GET /users** - Listar Usuários
**Funcionalidade:** Buscar todos os usuários para exibição na tabela principal

**Método:** `GET`

**Parâmetros de Query (opcionais):**
- `page`: int = 1 (paginação)
- `limit`: int = 10 (limite por página)
- `search`: string (busca por nome ou email)
- `status`: string ("active", "inactive") (filtrar por status)
- `access_level`: string ("ADMIN", "MONITOR", "VIEWER") (filtrar por perfil)

**Headers:**
```
Authorization: Bearer {token}
```

**Resposta de Sucesso (200):**
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

**Códigos de Erro:**
- `401`: Token inválido ou expirado
- `403`: Usuário sem permissão para listar usuários

---

### 2. **POST /users** - Criar Usuário
**Funcionalidade:** Criar novo usuário (funcionalidade do botão "Adicionar Usuário")

**Método:** `POST`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Corpo da Requisição:**
```json
{
    "name": "Maria Santos",
    "email": "maria.santos@empresa.com",
    "password": "senha123",
    "access_level": "MONITOR",
    "state": true
}
```

**Resposta de Sucesso (201):**
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

**Códigos de Erro:**
- `400`: Dados inválidos (email já existe, access_level inválido, etc.)
- `401`: Token inválido ou expirado
- `403`: Usuário sem permissão para criar usuários (apenas ADMIN)
- `422`: Dados de validação inválidos

---

### 3. **GET /users/{id}** - Obter Usuário Específico
**Funcionalidade:** Buscar dados de um usuário específico (para edição)

**Método:** `GET`

**Parâmetros de Path:**
- `id`: int (ID do usuário)

**Headers:**
```
Authorization: Bearer {token}
```

**Resposta de Sucesso (200):**
```json
{
    "id": 1,
    "name": "João Silva",
    "email": "joao.silva@empresa.com",
    "access_level": "ADMIN",
    "state": true,
    "last_login": "2024-01-15T14:30:00",
    "created_at": "2024-01-01T10:00:00"
}
```

**Códigos de Erro:**
- `401`: Token inválido ou expirado
- `403`: Usuário sem permissão
- `404`: Usuário não encontrado

---

### 4. **PUT /users/{id}** - Atualizar Usuário
**Funcionalidade:** Atualizar dados de um usuário (funcionalidade do botão de editar)

**Método:** `PUT`

**Parâmetros de Path:**
- `id`: int (ID do usuário)

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Corpo da Requisição:**
```json
{
    "name": "João Silva Santos",
    "email": "joao.silva.santos@empresa.com",
    "access_level": "ADMIN",
    "state": true,
    "password": "nova_senha123" // opcional
}
```

**Resposta de Sucesso (200):**
```json
{
    "message": "Usuário atualizado com sucesso",
    "user": {
        "id": 1,
        "name": "João Silva Santos",
        "email": "joao.silva.santos@empresa.com",
        "access_level": "ADMIN",
        "state": true,
        "updated_at": "2024-01-15T16:00:00"
    }
}
```

**Códigos de Erro:**
- `400`: Dados inválidos
- `401`: Token inválido ou expirado
- `403`: Usuário sem permissão para editar
- `404`: Usuário não encontrado
- `422`: Dados de validação inválidos

---

### 5. **DELETE /users/{id}** - Excluir Usuário
**Funcionalidade:** Excluir um usuário (funcionalidade do botão de lixeira)

**Método:** `DELETE`

**Parâmetros de Path:**
- `id`: int (ID do usuário)

**Headers:**
```
Authorization: Bearer {token}
```

**Resposta de Sucesso (200):**
```json
{
    "message": "Usuário excluído com sucesso"
}
```

**Códigos de Erro:**
- `401`: Token inválido ou expirado
- `403`: Usuário sem permissão para excluir (apenas ADMIN)
- `404`: Usuário não encontrado
- `409`: Não é possível excluir (ex: último administrador)

---

### 6. **PATCH /users/{id}/status** - Alterar Status do Usuário
**Funcionalidade:** Ativar/Desativar usuário

**Método:** `PATCH`

**Parâmetros de Path:**
- `id`: int (ID do usuário)

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Corpo da Requisição:**
```json
{
    "state": false
}
```

**Resposta de Sucesso (200):**
```json
{
    "message": "Status do usuário atualizado com sucesso",
    "user": {
        "id": 1,
        "state": false,
        "updated_at": "2024-01-15T16:30:00"
    }
}
```

---

### 7. **GET /users/stats** - Estatísticas dos Usuários
**Funcionalidade:** Obter estatísticas para os cards de resumo

**Método:** `GET`

**Headers:**
```
Authorization: Bearer {token}
```

**Resposta de Sucesso (200):**
```json
{
    "total_users": 12,
    "admins": 2,
    "monitors": 7,
    "viewers": 3,
    "active_users": 10,
    "inactive_users": 2,
    "users_last_24h": 3,
    "users_last_week": 8
}
```

---

## Permissões por Nível de Acesso

### ADMIN
- ✅ Visualizar todos os usuários
- ✅ Criar novos usuários
- ✅ Editar qualquer usuário
- ✅ Excluir usuários
- ✅ Alterar status de usuários
- ✅ Ver estatísticas

### MONITOR
- ✅ Visualizar usuários (limitado)
- ❌ Criar usuários
- ⚠️ Editar próprio perfil apenas
- ❌ Excluir usuários
- ❌ Alterar status
- ✅ Ver estatísticas básicas

### VIEWER
- ✅ Visualizar usuários (limitado)
- ❌ Todas as outras operações
- ⚠️ Ver próprio perfil apenas

---

## Funcionalidades do Frontend Mapeadas

### ✅ Implementadas no Backend (auth_routes.py)
- Login (`/auth/login`)
- Criar usuário (`/auth/signup`) - mas requer refatoração
- Refresh token (`/auth/refresh`)

### ❌ Ainda Necessárias
- Listar usuários com paginação e filtros
- Obter usuário específico
- Atualizar usuário
- Excluir usuário
- Alterar status
- Estatísticas detalhadas
- Busca por nome/email
- Filtros por perfil e status

---

## Observações e Recomendações

1. **Segurança:** Todas as rotas devem verificar o token JWT e as permissões do usuário
2. **Validação:** Implementar validação rigorosa de dados usando Pydantic schemas
3. **Paginação:** Implementar paginação para a listagem de usuários
4. **Logs:** Adicionar logs para operações críticas (criação, edição, exclusão)
5. **Rate Limiting:** Considerar implementar rate limiting nas rotas de criação/edição
6. **Soft Delete:** Considerar soft delete em vez de exclusão física
7. **Auditoria:** Manter histórico de alterações de usuários

### Schema Adicional Necessário

```python
# schemas.py
class UserUpdateSchemas(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    access_level: Optional[str] = None
    state: Optional[bool] = None
    password: Optional[str] = None

class UserListResponse(BaseModel):
    users: List[UserSchemas]
    total: int
    page: int
    pages: int
    stats: dict

class UserStatsSchemas(BaseModel):
    total_users: int
    admins: int
    monitors: int
    viewers: int
    active_users: int
    inactive_users: int
```
