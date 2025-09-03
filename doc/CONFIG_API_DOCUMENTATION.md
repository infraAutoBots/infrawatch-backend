# API de Configuração - Documentação

Esta documentação descreve as rotas de configuração criadas para gerenciar webhooks, configurações de email e limites de falhas consecutivas.

## Visão Geral

As rotas de configuração permitem gerenciar:
- **Webhooks**: URLs para receber notificações
- **Configurações de Email**: Configurações SMTP para envio de alertas
- **Limites de Falhas**: Configuração de falhas consecutivas para SNMP e ping

## Autenticação

Todas as rotas requerem autenticação via token JWT. As operações de criação, atualização e exclusão requerem nível de acesso **ADMIN**.

## Endpoints

### Webhooks

#### Criar Webhook
```
POST /config/webhook
```

**Body:**
```json
{
  "url": "https://example.com/webhook",
  "active": true
}
```

**Resposta:**
```json
{
  "id": 1,
  "url": "https://example.com/webhook",
  "active": true,
  "created_at": "2025-09-03T10:00:00",
  "updated_at": "2025-09-03T10:00:00"
}
```

#### Listar Webhooks
```
GET /config/webhook
```

**Resposta:**
```json
[
  {
    "id": 1,
    "url": "https://example.com/webhook",
    "active": true,
    "created_at": "2025-09-03T10:00:00",
    "updated_at": "2025-09-03T10:00:00"
  }
]
```

#### Obter Webhook Específico
```
GET /config/webhook/{webhook_id}
```

#### Atualizar Webhook
```
PUT /config/webhook/{webhook_id}
```

**Body:**
```json
{
  "url": "https://new-url.com/webhook",
  "active": false
}
```

#### Deletar Webhook
```
DELETE /config/webhook/{webhook_id}
```

**Resposta:**
```json
{
  "message": "Webhook config deleted successfully"
}
```

---

### Configurações de Email

#### Criar Configuração de Email
```
POST /config/email
```

**Body:**
```json
{
  "email": "alerts@company.com",
  "password": "senha_segura",
  "port": 587,
  "server": "smtp.gmail.com",
  "active": true
}
```

**Resposta:**
```json
{
  "id": 1,
  "email": "alerts@company.com",
  "port": 587,
  "server": "smtp.gmail.com",
  "active": true,
  "created_at": "2025-09-03T10:00:00",
  "updated_at": "2025-09-03T10:00:00"
}
```

**Nota:** A senha é criptografada antes de ser armazenada e não é retornada nas respostas.

#### Listar Configurações de Email
```
GET /config/email
```

#### Obter Configuração de Email Específica
```
GET /config/email/{email_id}
```

#### Atualizar Configuração de Email
```
PUT /config/email/{email_id}
```

**Body:**
```json
{
  "email": "new-alerts@company.com",
  "port": 465,
  "server": "smtp.outlook.com",
  "active": true
}
```

#### Deletar Configuração de Email
```
DELETE /config/email/{email_id}
```

---

### Limites de Falhas Consecutivas

#### Criar Configuração de Limites
```
POST /config/failure-threshold
```

**Body:**
```json
{
  "consecutive_snmp_failures": 3,
  "consecutive_ping_failures": 5,
  "active": true
}
```

**Resposta:**
```json
{
  "id": 1,
  "consecutive_snmp_failures": 3,
  "consecutive_ping_failures": 5,
  "active": true,
  "created_at": "2025-09-03T10:00:00",
  "updated_at": "2025-09-03T10:00:00"
}
```

#### Listar Configurações de Limites
```
GET /config/failure-threshold
```

#### Obter Configuração de Limites Específica
```
GET /config/failure-threshold/{threshold_id}
```

#### Atualizar Configuração de Limites
```
PUT /config/failure-threshold/{threshold_id}
```

**Body:**
```json
{
  "consecutive_snmp_failures": 5,
  "consecutive_ping_failures": 3
}
```

#### Deletar Configuração de Limites
```
DELETE /config/failure-threshold/{threshold_id}
```

---

### Obter Configurações Ativas

#### Obter Todas as Configurações Ativas
```
GET /config/active
```

**Resposta:**
```json
{
  "webhook": {
    "id": 1,
    "url": "https://example.com/webhook",
    "active": true,
    "created_at": "2025-09-03T10:00:00",
    "updated_at": "2025-09-03T10:00:00"
  },
  "email": {
    "id": 1,
    "email": "alerts@company.com",
    "port": 587,
    "server": "smtp.gmail.com",
    "active": true,
    "created_at": "2025-09-03T10:00:00",
    "updated_at": "2025-09-03T10:00:00"
  },
  "failure_threshold": {
    "id": 1,
    "consecutive_snmp_failures": 3,
    "consecutive_ping_failures": 5,
    "active": true,
    "created_at": "2025-09-03T10:00:00",
    "updated_at": "2025-09-03T10:00:00"
  }
}
```

## Códigos de Status HTTP

- **200**: Operação bem-sucedida
- **201**: Recurso criado com sucesso
- **400**: Dados inválidos
- **401**: Token de autenticação inválido
- **403**: Sem permissão (requer ADMIN)
- **404**: Recurso não encontrado
- **500**: Erro interno do servidor

## Exemplos de Uso

### 1. Configurar Webhook para Slack

```bash
curl -X POST "http://localhost:8000/config/webhook" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "active": true
  }'
```

### 2. Configurar Email Gmail

```bash
curl -X POST "http://localhost:8000/config/email" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-alert-email@gmail.com",
    "password": "your-app-password",
    "port": 587,
    "server": "smtp.gmail.com",
    "active": true
  }'
```

### 3. Configurar Limites de Falhas

```bash
curl -X POST "http://localhost:8000/config/failure-threshold" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consecutive_snmp_failures": 3,
    "consecutive_ping_failures": 5,
    "active": true
  }'
```

## Estrutura do Banco de Dados

### Tabela: webhook_config
- `id`: INTEGER (Primary Key)
- `url`: STRING (Not Null)
- `active`: BOOLEAN (Default: True)
- `created_at`: DATETIME
- `updated_at`: DATETIME

### Tabela: email_config
- `id`: INTEGER (Primary Key)
- `email`: STRING (Not Null)
- `password`: STRING (Encrypted, Not Null)
- `port`: INTEGER (Not Null)
- `server`: STRING (Not Null)
- `active`: BOOLEAN (Default: True)
- `created_at`: DATETIME
- `updated_at`: DATETIME

### Tabela: failure_threshold_config
- `id`: INTEGER (Primary Key)
- `consecutive_snmp_failures`: INTEGER (Default: 3)
- `consecutive_ping_failures`: INTEGER (Default: 5)
- `active`: BOOLEAN (Default: True)
- `created_at`: DATETIME
- `updated_at`: DATETIME

## Segurança

- As senhas de email são criptografadas usando bcrypt antes de serem armazenadas
- Todas as operações de modificação requerem permissão de ADMIN
- Os tokens JWT são verificados em todas as rotas
- As senhas nunca são retornadas nas respostas da API

## Notas Importantes

1. **Configurações Ativas**: O endpoint `/config/active` retorna apenas uma configuração ativa de cada tipo. Se houver múltiplas configurações ativas, apenas a primeira será retornada.

2. **Criptografia de Senhas**: As senhas de email são automaticamente criptografadas quando criadas ou atualizadas.

3. **Valores Padrão**: Os limites de falhas têm valores padrão (3 para SNMP, 5 para ping) caso não sejam especificados.

4. **Validação**: Todos os campos obrigatórios são validados antes de serem salvos no banco de dados.
