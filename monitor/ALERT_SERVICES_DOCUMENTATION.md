# Serviços de Alerta - InfraWatch

## 📋 Visão Geral

O sistema de alertas do InfraWatch foi reestruturado em três serviços principais que trabalham de forma integrada:

1. **EmailService** - Envio de alertas por email
2. **WebhookService** - Envio de alertas via webhook 
3. **AlertService** - Serviço unificado que coordena ambos

## 🏗️ Arquitetura

```
AlertService (Coordenador)
├── EmailService (Email SMTP)
├── WebhookService (HTTP POST)
└── Configurações do Banco de Dados
    ├── EmailConfig
    ├── WebHookConfig
    └── FailureThresholdConfig
```

## 📧 EmailService

### Características
- ✅ Integração com configurações do banco de dados
- ✅ Fallback para variáveis de ambiente
- ✅ Busca automática de emails de administradores
- ✅ Templates HTML responsivos
- ✅ Teste de conectividade SMTP

### Configuração

#### Variáveis de Ambiente (Fallback)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app
FROM_EMAIL=noreply@infrawatch.com
EMAIL_ALERTS_ENABLED=true
```

#### Banco de Dados (Preferencial)
Use as APIs `/config/email` para configurar via interface.

### Uso Básico
```python
from alert_email_service import EmailService
from sqlalchemy.orm import Session

# Com banco de dados
email_service = EmailService(db_session=session)

# Sem banco (usa env vars)
email_service = EmailService()

# Enviar para admins automaticamente
email_service.send_alert_to_admins(
    subject="Alerta: Servidor Offline",
    endpoint_name="Server01",
    endpoint_ip="192.168.1.10",
    status="DOWN",
    timestamp=datetime.now()
)
```

## 🔗 WebhookService

### Características
- ✅ Retry automático com backoff exponencial
- ✅ Timeout configurável
- ✅ Suporte a autenticação Bearer Token
- ✅ Payloads JSON estruturados
- ✅ Webhook de sistema e alertas

### Configuração

#### Variáveis de Ambiente
```bash
WEBHOOK_URL=https://hooks.slack.com/services/...
WEBHOOK_TOKEN=seu_token_aqui
WEBHOOK_ALERTS_ENABLED=true
WEBHOOK_TIMEOUT=30
WEBHOOK_RETRY_ATTEMPTS=3
```

#### Banco de Dados
Use as APIs `/config/webhook` para configurar via interface.

### Uso Básico
```python
from webhook_service import WebhookService

webhook_service = WebhookService()

# Configurar URL
webhook_service.set_webhook_url("https://seu.webhook.url/endpoint")

# Enviar alerta
webhook_service.send_alert_webhook(
    webhook_url="https://hooks.slack.com/services/...",
    endpoint_name="Server01",
    endpoint_ip="192.168.1.10",
    status="DOWN",
    timestamp=datetime.now()
)
```

### Formato do Payload

#### Alerta de Endpoint
```json
{
  "type": "alert",
  "service": "InfraWatch",
  "timestamp": "2025-09-03T10:00:00",
  "severity": "critical",
  "alert": {
    "title": "🔴 InfraWatch Alert - DOWN",
    "message": "Endpoint 'Server01' (192.168.1.10) is DOWN",
    "details": {
      "endpoint_name": "Server01",
      "endpoint_ip": "192.168.1.10",
      "status": "DOWN",
      "timestamp": "03/09/2025 10:00:00",
      "additional_info": "Connection timeout after 30s"
    },
    "color": "#dc3545"
  }
}
```

#### Status do Sistema
```json
{
  "type": "system_status",
  "service": "InfraWatch",
  "timestamp": "2025-09-03T10:00:00",
  "system": {
    "title": "✅ InfraWatch System Status",
    "status": "healthy",
    "message": "Monitoring 10 endpoints",
    "details": {
      "total_endpoints": 10,
      "up_endpoints": 8,
      "down_endpoints": 1,
      "snmp_down_endpoints": 1
    },
    "color": "#28a745"
  }
}
```

## 🚨 AlertService (Recomendado)

### Características
- ✅ Coordena email e webhook automaticamente
- ✅ Carrega configurações do banco de dados
- ✅ Implementa lógica de limites de falhas
- ✅ Métodos convenientes para uso comum
- ✅ Testes automatizados de conectividade

### Uso Básico
```python
from alert_service import AlertService
from sqlalchemy.orm import Session

# Inicializar com banco de dados
alert_service = AlertService(db_session=session)

# Enviar alerta para endpoint
results = alert_service.send_endpoint_alert(
    endpoint_name="Server01",
    endpoint_ip="192.168.1.10", 
    status="DOWN",
    timestamp=datetime.now(),
    additional_info="Connection timeout"
)

print(f"Email: {results['email_sent']}")
print(f"Webhook: {results['webhook_sent']}")

# Verificar se deve enviar baseado em falhas consecutivas
if alert_service.should_send_alert('ping', 5):
    # Enviar alerta...
    pass
```

### Integração com Monitoramento

```python
# Exemplo de uso no sistema de monitoramento
class MonitorService:
    def __init__(self):
        self.alert_service = AlertService(db_session)
        self.failure_counts = {}
    
    def check_endpoint(self, endpoint):
        # Lógica de monitoramento...
        
        if not endpoint.is_reachable():
            self.failure_counts[endpoint.id] = self.failure_counts.get(endpoint.id, 0) + 1
            
            # Verificar se deve enviar alerta
            if self.alert_service.should_send_alert('ping', self.failure_counts[endpoint.id]):
                self.alert_service.send_endpoint_alert(
                    endpoint_name=endpoint.name,
                    endpoint_ip=endpoint.ip,
                    status="DOWN",
                    timestamp=datetime.now(),
                    additional_info=f"Consecutive failures: {self.failure_counts[endpoint.id]}"
                )
        else:
            # Reset contador em caso de sucesso
            if endpoint.id in self.failure_counts:
                del self.failure_counts[endpoint.id]
```

## ⚙️ Configurações do Banco de Dados

### Limites de Falhas Consecutivas
- **SNMP**: Padrão 3 falhas
- **Ping**: Padrão 5 falhas
- Configurável via API `/config/failure-threshold`

### Prioridade de Configurações
1. **Banco de Dados** (configurações ativas)
2. **Variáveis de Ambiente** (fallback)
3. **Valores Padrão** (último recurso)

## 🧪 Testes

### Script de Teste Completo
```bash
cd monitor
python test_alert_services.py
```

### Testes Individuais
```python
# Testar EmailService
email_service = EmailService()
assert email_service.test_connection()

# Testar WebhookService  
webhook_service = WebhookService()
webhook_service.set_webhook_url("https://httpbin.org/post")
assert webhook_service.test_connection()

# Testar AlertService
alert_service = AlertService()
results = alert_service.test_services()
assert results['email_connection'] or results['webhook_connection']
```

## 📊 Status e Monitoramento

### Obter Status dos Serviços
```python
alert_service = AlertService(db_session)
status = alert_service.get_service_status()

print(f"Email habilitado: {status['email_service']['enabled']}")
print(f"Webhook habilitado: {status['webhook_service']['enabled']}")
print(f"Admins cadastrados: {status['email_service']['admin_count']}")
print(f"Limites SNMP/Ping: {status['failure_thresholds']}")
```

### Recarregar Configurações
```python
# Recarregar após mudanças no banco
alert_service.reload_configurations()
```

## 🔧 Configuração de Produção

### 1. Configurar Email (Gmail)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@empresa.com
SMTP_PASSWORD=senha_de_app_gmail
EMAIL_ALERTS_ENABLED=true
```

### 2. Configurar Webhook (Slack)
```bash
WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXXX
WEBHOOK_ALERTS_ENABLED=true
```

### 3. Configurar via API
```bash
# Configurar email via API
curl -X POST "http://localhost:8000/config/email" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alerts@empresa.com",
    "password": "senha_app",
    "port": 587,
    "server": "smtp.gmail.com",
    "active": true
  }'

# Configurar webhook via API
curl -X POST "http://localhost:8000/config/webhook" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.slack.com/services/...",
    "active": true
  }'
```

## 🚀 Próximos Passos

1. **Integrar no Sistema de Monitor**: Substituir calls diretos por `AlertService`
2. **Configurar Templates**: Personalizar templates de email por tipo de alerta
3. **Métricas**: Adicionar contadores de alertas enviados
4. **Dashboard**: Interface para visualizar status dos serviços
5. **Escalação**: Implementar níveis de escalação de alertas

## 📝 Notas Importantes

- ⚠️ **Senhas**: Por segurança, senhas de email devem estar em variáveis de ambiente
- 🔄 **Configurações**: Mudanças no banco requerem `reload_configurations()`
- 🔒 **HTTPS**: Webhooks devem usar HTTPS em produção
- 📧 **Rate Limits**: Considere limites de envio do provedor de email
- 🔑 **Tokens**: Use tokens seguros para webhooks autenticados
