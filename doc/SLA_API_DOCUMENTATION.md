# 📊 InfraWatch - APIs de SLA e Métricas Avançadas

## 🎯 Visão Geral

Este documento descreve as novas APIs implementadas para suporte completo a métricas de SLA, rastreamento de incidentes e análise de performance no sistema InfraWatch.

## 🚀 Funcionalidades Implementadas

### ✅ **DADOS COLETADOS:**
- ✅ Métricas de conectividade (ping, SNMP)
- ✅ Performance básica (CPU, RAM, Disco, Rede)
- ✅ Alertas e logs básicos
- ✅ Timestamps de eventos
- ✅ **Métricas SLA agregadas** (uptime %, MTTR, MTBF)
- ✅ **Tracking de incidentes estruturado**
- ✅ **Dados históricos de disponibilidade**
- ✅ **Percentis de performance** (P50, P90, P95, P99)

### 🗄️ **Novas Tabelas no Banco:**

#### 1. **SLAMetrics** - Métricas de SLA Agregadas
```sql
- id, endpoint_id, timestamp
- availability_percentage, uptime_seconds, downtime_seconds
- mttr_minutes, mtbf_hours, incidents_count
- sla_target, sla_compliance, sla_breach_minutes
- avg_response_time, max_response_time, min_response_time
- measurement_period_hours
```

#### 2. **IncidentTracking** - Rastreamento de Incidentes
```sql
- id, endpoint_id, alert_id
- incident_type, severity, status
- start_time, end_time, duration_seconds
- root_cause, impact_description, resolution_notes
- detected_by, resolved_by
- response_time_minutes, resolution_time_minutes
```

#### 3. **PerformanceMetrics** - Métricas de Performance Detalhadas
```sql
- id, endpoint_id, timestamp
- response_time_p50, response_time_p90, response_time_p95, response_time_p99
- response_time_avg, response_time_max, response_time_min
- error_rate_percentage, total_requests, failed_requests
- jitter_ms, packet_loss_rate
- measurement_period_minutes, sample_count
```

## 🔗 APIs Disponíveis

### 1. **GET /api/sla/summary**
Retorna dados brutos de SLA dos últimos N dias para processamento no frontend.

**Parâmetros:**
- `days` (opcional): Número de dias para análise (padrão: 30)

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "endpoints": [...],
    "sla_metrics": [...],
    "incidents": [...],
    "performance_data": [...],
    "alerts": [...],
    "summary": {
      "period_days": 30,
      "total_endpoints": 4,
      "total_incidents": 12,
      "total_alerts": 25
    }
  }
}
```

### 2. **GET /api/sla/endpoint/{endpoint_id}**
Retorna dados detalhados de SLA para um endpoint específico.

**Parâmetros:**
- `endpoint_id`: ID do endpoint
- `days` (opcional): Número de dias para análise (padrão: 30)

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "endpoint": {...},
    "sla_metrics": [...],
    "incidents": [...],
    "performance_metrics": [...],
    "raw_monitoring_data": [...]
  }
}
```

### 3. **GET /api/sla/compliance**
Retorna relatório de compliance de SLA de todos os endpoints.

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "overall_compliance_percentage": 96.8,
    "total_endpoints": 4,
    "compliant_endpoints": 3,
    "non_compliant_endpoints": 1,
    "endpoints": [...]
  }
}
```

### 4. **GET /api/incidents/summary**
Retorna resumo de incidentes para análise.

**Parâmetros:**
- `days` (opcional): Número de dias (padrão: 30)
- `status` (opcional): Filtrar por status
- `severity` (opcional): Filtrar por severidade

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_incidents": 15,
      "open_incidents": 2,
      "resolved_incidents": 13,
      "average_mttr_minutes": 12.5
    },
    "incidents_by_severity": {...},
    "incidents_by_type": {...},
    "incidents": [...]
  }
}
```

### 5. **GET /api/performance/metrics**
Retorna métricas de performance detalhadas.

**Parâmetros:**
- `endpoint_id` (opcional): ID do endpoint específico
- `days` (opcional): Número de dias (padrão: 7)

**Resposta:**
```json
{
  "status": "success",
  "data": {
    "metrics": [
      {
        "endpoint_id": 1,
        "timestamp": "2025-09-07T...",
        "response_time_percentiles": {
          "p50": 45.2,
          "p90": 89.1,
          "p95": 112.5,
          "p99": 156.7
        },
        "response_time_stats": {...},
        "error_metrics": {...},
        "network_metrics": {...}
      }
    ]
  }
}
```

## 🔄 Coleta Automática de Dados

### **SLADataCollector**
Nova classe integrada ao monitor que:

1. **Coleta métricas em tempo real** durante o monitoramento
2. **Rastreia mudanças de estado** para criação de incidentes
3. **Calcula percentis** de tempo de resposta
4. **Salva métricas agregadas** a cada hora
5. **Gerencia incidentes** automaticamente (criação e resolução)

### **Integração no Monitor**
```python
# Adicionado ao run_monitoring()
await asyncio.gather(
    self.send_alert(session_factory, result),
    self._check_performance_alerts(result, session_factory),
    self.insert_snmp_data_async(session_factory, result),
    self.sla_collector.collect_sla_metrics(result, session_factory),  # ← NOVO
    return_exceptions=True
)
```

## 💻 Frontend - Cálculos em Tempo Real

### **SLACalculator (JavaScript)**
Classe para calcular métricas no frontend:

```javascript
class SLACalculator {
  static calculateAvailability(uptimeSeconds, downtimeSeconds) {
    const totalSeconds = uptimeSeconds + downtimeSeconds;
    return ((uptimeSeconds / totalSeconds) * 100);
  }

  static calculateMTTR(incidents) {
    const resolved = incidents.filter(i => i.resolution_time_minutes);
    return resolved.reduce((acc, i) => acc + i.resolution_time_minutes, 0) / resolved.length;
  }

  static calculatePercentiles(responseTimes) {
    const sorted = responseTimes.sort((a, b) => a - b);
    return {
      p50: this.percentile(sorted, 50),
      p90: this.percentile(sorted, 90),
      p95: this.percentile(sorted, 95),
      p99: this.percentile(sorted, 99)
    };
  }

  static checkSLACompliance(availability, target = 99.9) {
    return availability >= target;
  }
}
```

## 📈 Dashboard de Exemplo

Criado um dashboard HTML completo (`sla_dashboard_demo.html`) que demonstra:

- ✅ **Métricas agregadas** (Compliance Geral, MTTR, Disponibilidade)
- ✅ **Gráficos interativos** (Chart.js)
- ✅ **Tabela de compliance** por endpoint
- ✅ **Cálculos em tempo real** no frontend
- ✅ **Atualização automática** a cada 5 minutos
- ✅ **Interface responsiva** e moderna

## 🎯 Benefícios da Arquitetura

### **Backend (Python/FastAPI):**
- ✅ Focado na **coleta e armazenamento**
- ✅ APIs **simples para dados brutos**
- ✅ **Processamento mínimo** no servidor
- ✅ **Escalabilidade** melhorada

### **Frontend (JavaScript):**
- ✅ **Cálculos distribuídos** nos clientes
- ✅ **Responsividade** em tempo real
- ✅ **Flexibilidade** para diferentes visualizações
- ✅ **Performance** otimizada

## 🔧 Como Usar

### 1. **Iniciar a API:**
```bash
cd /home/ubuntu/Code/infrawatch/infrawatch-backend
./venv/bin/python api/app.py
```

### 2. **Acessar Dashboard Demo:**
```bash
# Abrir no navegador:
file:///home/ubuntu/Code/infrawatch/infrawatch-backend/sla_dashboard_demo.html
```

### 3. **Testar APIs:**
```bash
# Exemplo de uso das APIs
curl "http://localhost:8000/api/sla/summary?days=30"
curl "http://localhost:8000/api/sla/compliance"
curl "http://localhost:8000/api/incidents/summary?days=7"
```

## 📊 Métricas Disponíveis

### **SLA e Compliance:**
- Disponibilidade percentual
- MTTR (Mean Time To Recovery)
- MTBF (Mean Time Between Failures)
- SLA Compliance
- Breach minutes

### **Performance:**
- Percentis de tempo de resposta (P50, P90, P95, P99)
- Estatísticas de resposta (avg, max, min)
- Taxa de erro
- Jitter e packet loss
- Throughput

### **Incidentes:**
- Tracking completo de incidentes
- Tempo de resolução
- Classificação por severidade
- Root cause analysis
- Histórico de ações

## 🚀 Próximos Passos

1. **Integração com Frontend React/Vue** no projeto principal
2. **Alertas inteligentes** baseados em SLA
3. **Relatórios PDF** automatizados
4. **Machine Learning** para predição de falhas
5. **Dashboards customizáveis** por usuário

---

**Status:** ✅ **IMPLEMENTADO E FUNCIONANDO**

Todas as funcionalidades foram implementadas com sucesso:
- ✅ Tabelas criadas no banco
- ✅ APIs funcionais
- ✅ Coleta automática de dados
- ✅ Dashboard de demonstração
- ✅ Cálculos de frontend
- ✅ Documentação completa
