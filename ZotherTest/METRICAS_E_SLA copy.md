# Sistema de Monitoramento - Métricas e SLA

## Métricas Fundamentais

### Métricas de Performance
- **Tempo de Resposta**
  - Latência média, mediana
  - Percentis: P50, P90, P95, P99, P99.9
  - Tempo de resposta mínimo/máximo
  - Desvio padrão do tempo de resposta

- **Throughput**
  - Requisições por segundo (RPS)
  - Transações por segundo (TPS)
  - Operações por segundo (OPS)
  - Throughput máximo sustentável

- **Taxa de Erro**
  - Percentual de falhas totais
  - Erros por categoria (4xx, 5xx)
  - Taxa de timeout
  - Taxa de rejeição

- **Disponibilidade**
  - Uptime percentual
  - Downtime acumulado
  - MTBF (Mean Time Between Failures)
  - MTTR (Mean Time To Recovery)

### Métricas de Infraestrutura

#### CPU
- Utilização percentual por core
- Load Average (1m, 5m, 15m)
- Context Switches por segundo
- CPU Wait Time (I/O wait)
- CPU Steal Time (virtualização)
- Processos em execução

#### Memória
- RAM Total/Usado/Livre/Disponível
- Buffer/Cache utilization
- Swap In/Out rate
- Memory Allocation Failures
- OOM (Out of Memory) events
- Memory Fragmentation

#### Disco
- Espaço usado por filesystem
- IOPS (Read/Write operations per second)
- Disk Latency (read/write)
- Queue Depth
- Disk Errors (read/write errors)
- Disk Temperature

#### Rede
- Bytes In/Out por interface
- Packets In/Out por interface
- Network Errors (dropped, overruns)
- TCP Connections (established, listening)
- DNS Resolution Time
- Network Utilization

### Métricas de Conectividade e Rede

#### Ping Metrics
- **RTT (Round Trip Time)**
  - Tempo mínimo/médio/máximo
  - Desvio padrão (jitter)
  - Percentis de latência

- **Packet Loss Rate**
  - Percentual de pacotes perdidos
  - Consecutivos pacotes perdidos
  - Padrões de perda

- **Jitter**
  - Variação no tempo de resposta
  - Jitter médio/máximo
  - Qualidade da conexão

- **TTL (Time To Live)**
  - Número de hops
  - Rota de rede
  - Mudanças de rota

#### SNMP Metrics
- **Interface Utilization**
  - Bandwidth in/out
  - Utilização percentual
  - Picos de tráfego

- **Interface Errors**
  - CRC errors
  - Collision count
  - Dropped packets

- **Interface Status**
  - Up/Down/Admin Down
  - Link speed
  - Duplex mode

- **SNMP Response Time**
  - Tempo de resposta SNMP
  - Timeouts SNMP
  - Taxa de sucesso

### Métricas de Aplicação e Serviços

#### Application Performance
- Response Time por endpoint
- Request Rate específico por serviço
- Error Rate por tipo de erro
- Active Sessions/Connections
- Queue Length/Processing Time
- Cache Hit/Miss Ratio

#### Database Metrics
- Query Response Time
- Connection Pool Usage
- Slow Queries Count
- Deadlocks per hour
- Table Lock Wait Time
- Index Usage Efficiency
- Database Size Growth

#### Cache Metrics
- Hit/Miss Ratio
- Cache Size/Usage
- Eviction Rate
- Cache Response Time
- Memory Pressure

### Métricas de Virtualização
- VM CPU Ready Time
- VM Memory Ballooning
- VM Storage Latency
- Host Resource Contention
- Hypervisor Performance

### Métricas de Storage
- Storage Capacity (used/free)
- Storage Performance (IOPS, throughput)
- Storage Latency
- RAID Status
- Backup Success Rate

### Métricas de Incidentes e Alertas

#### Gestão de Incidentes
- **Total de Incidentes**
  - Incidentes por período (hora/dia/semana/mês)
  - Incidentes por severidade (Info/Warning/Critical/Emergency)
  - Incidentes por categoria (Network/System/Application/Security)
  - Incidentes recorrentes vs únicos
  - Taxa de crescimento de incidentes

- **Tempo de Vida dos Alertas**
  - Duração média dos alertas ativos
  - Tempo mínimo/máximo de alerta ativo
  - Alertas de longa duração (> 24h)
  - Distribuição temporal dos alertas
  - Alertas por turno/horário

- **Tempo de Resposta a Incidentes**
  - MTTA (Mean Time To Acknowledge) - Tempo para reconhecimento
  - MTTR (Mean Time To Resolve) - Tempo para resolução
  - MTTF (Mean Time To Fix) - Tempo para correção
  - MTBF (Mean Time Between Failures) - Tempo entre falhas
  - Escalation Time - Tempo para escalação

#### Análise de Alertas
- **Volume de Alertas**
  - Alertas gerados por hora/dia
  - Picos de alertas (Alert Storms)
  - Alertas falso-positivos
  - Taxa de correlação de alertas
  - Alertas únicos vs duplicados

- **Efetividade dos Alertas**
  - Precisão dos alertas (True Positive Rate)
  - Taxa de falsos positivos
  - Alertas actionáveis vs informativos
  - Cobertura de monitoramento
  - Noise Ratio (ruído nos alertas)

- **Ciclo de Vida dos Alertas**
  - Tempo desde trigger até acknowledge
  - Tempo desde acknowledge até resolução
  - Alertas auto-resolvidos
  - Alertas que requerem intervenção manual
  - Alertas que geram incidentes

#### Métricas de Severidade
- **Por Nível de Severidade**
  - Info: Alertas informativos
  - Warning: Alertas de aviso (tempo médio ativo)
  - Critical: Alertas críticos (tempo médio ativo)
  - Emergency: Alertas de emergência (tempo médio ativo)

- **Distribuição Temporal**
  - Alertas por dia da semana
  - Alertas por horário do dia
  - Sazonalidade dos alertas
  - Padrões de ocorrência

#### Métricas de Recuperação
- **Tempo de Recuperação**
  - Recuperação automática vs manual
  - Tempo médio de recuperação por tipo de alerta
  - Taxa de sucesso na recuperação
  - Tentativas de recuperação antes do sucesso

- **Análise de Root Cause**
  - Causas raiz mais frequentes
  - Tempo para identificação da causa raiz
  - Recorrência de problemas
  - Efetividade das correções implementadas

#### Métricas de Performance do Sistema de Alertas
- **Latência do Sistema**
  - Tempo entre evento e geração do alerta
  - Tempo de processamento do alerta
  - Tempo de entrega da notificação
  - Latência na atualização de status

- **Disponibilidade do Sistema de Alertas**
  - Uptime do sistema de monitoramento
  - Perda de alertas (Alert Loss Rate)
  - Falhas na entrega de notificações
  - Redundância e failover

### Métricas de Dashboard e Interface

#### Métricas de Performance por Sistema
- **SLA por Sistema Individual**
  - SLA atual vs meta por sistema
  - Histórico de performance de cada sistema
  - Tendências (up/down/stable) por sistema
  - Classificação de criticidade por sistema

#### Métricas de Agrupamento
- **SLA Médio Geral**
  - Média ponderada de todos os sistemas
  - SLA médio por categoria de sistema
  - SLA médio por criticidade
  - Variação do SLA geral ao longo do tempo

- **Distribuição de Status**
  - Sistemas em status "Atingido" (verde)
  - Sistemas em status "Atenção" (amarelo) 
  - Sistemas em status "Crítico" (vermelho)
  - Percentual de sistemas por categoria de status

#### Métricas de Tendência e Análise
- **Análise de Tendência**
  - Sistemas com tendência de melhora
  - Sistemas com tendência de degradação
  - Sistemas estáveis
  - Velocidade de mudança das tendências

- **Métricas de Comparação**
  - Gap entre meta e performance atual
  - Ranking de sistemas por performance
  - Sistemas mais/menos confiáveis
  - Variabilidade de performance

#### Métricas de Impacto de Negócio
- **Criticidade dos Sistemas**
  - Sistemas críticos para o negócio
  - Impacto financeiro por downtime
  - Priorização baseada em criticidade
  - SLA diferenciado por importância

- **Métricas de Custo**
  - Custo por hora de downtime
  - Penalidades por violação de SLA
  - ROI de melhorias de infraestrutura
  - Budget de SLA credits

### Métricas de Relatórios e Exportação

#### Métricas de Compliance
- **Relatórios Regulamentares**
  - Compliance com regulamentações
  - Auditoria de SLA
  - Documentação de incidentes
  - Evidências de conformidade

#### Métricas de Histórico Detalhado
- **Análise Temporal Avançada**
  - Performance por período (dia/semana/mês/trimestre/ano)
  - Sazonalidade de incidentes
  - Padrões de uso e carga
  - Correlação temporal entre sistemas

- **Métricas de Previsão**
  - Projeção de SLA futuro
  - Previsão de incidentes
  - Capacidade futura necessária
  - Alertas preventivos

### Métricas de User Experience

#### Métricas de Percepção do Usuário
- **Satisfação do Usuário**
  - Net Promoter Score (NPS) técnico
  - Feedback sobre disponibilidade
  - Percepção de qualidade do serviço
  - Impacto na produtividade

#### Métricas de Comunicação
- **Transparência e Comunicação**
  - Tempo para comunicação de incidentes
  - Qualidade das mensagens de status
  - Frequência de atualizações
  - Clareza das informações

## Dados de SLA

### SLA de Disponibilidade (Uptime)

#### Níveis de SLA
- **99.9% (Three Nines)**
  - Downtime permitido por ano: 8h 45m 57s
  - Downtime permitido por mês: 43m 49s
  - Downtime permitido por dia: 1m 26s

- **99.95% (Three and a Half Nines)**
  - Downtime permitido por ano: 4h 22m 58s
  - Downtime permitido por mês: 21m 54s
  - Downtime permitido por dia: 43s

- **99.99% (Four Nines)**
  - Downtime permitido por ano: 52m 35s
  - Downtime permitido por mês: 4m 22s
  - Downtime permitido por dia: 8.6s

- **99.999% (Five Nines)**
  - Downtime permitido por ano: 5m 15s
  - Downtime permitido por mês: 26s
  - Downtime permitido por dia: 0.86s

### SLA de Performance

#### Response Time SLA
- **Target**: < 200ms para 95% das requests
- **Warning**: > 150ms
- **Critical**: > 200ms
- **Emergency**: > 500ms

#### Throughput SLA
- **Minimum**: 1000 RPS
- **Target**: 5000 RPS
- **Maximum**: 10000 RPS
- **Peak Load**: 15000 RPS

#### Error Rate SLA
- **Target**: < 0.1%
- **Warning**: > 0.05%
- **Critical**: > 0.1%
- **Emergency**: > 1%

### SLA de Conectividade

#### Ping Metrics SLA
- **RTT Target**: < 50ms
- **Packet Loss**: < 0.1%
- **Consecutive Failures**: < 3
- **Jitter**: < 10ms

#### SNMP Metrics SLA
- **Response Time**: < 2000ms
- **Timeout Rate**: < 1%
- **Consecutive Failures**: < 5
- **Availability**: > 99.5%

### SLA de Incidentes e Alertas

#### SLA de Tempo de Resposta
- **MTTA (Mean Time To Acknowledge)**
  - Target: < 15 minutos
  - Warning: > 10 minutos
  - Critical: > 15 minutos
  - Emergency: > 30 minutos

- **MTTR (Mean Time To Resolve)**
  - Info: < 4 horas
  - Warning: < 2 horas
  - Critical: < 1 hora
  - Emergency: < 30 minutos

- **MTTF (Mean Time To Fix)**
  - Target: < 4 horas para 90% dos incidentes
  - Critical: < 2 horas para incidentes críticos
  - Emergency: < 1 hora para emergências

#### SLA de Volume de Incidentes
- **Taxa de Incidentes**
  - Target: < 50 incidentes por dia
  - Warning: > 40 incidentes por dia
  - Critical: > 50 incidentes por dia
  - Emergency: > 100 incidentes por dia

- **Duração de Alertas Ativos**
  - Target: < 2 horas para 95% dos alertas
  - Warning: Alertas ativos > 1 hora
  - Critical: Alertas ativos > 2 horas
  - Emergency: Alertas ativos > 4 horas

- **Taxa de Falsos Positivos**
  - Target: < 5%
  - Warning: > 3%
  - Critical: > 5%
  - Emergency: > 10%

#### SLA de Cobertura de Monitoramento
- **Cobertura de Serviços**
  - Target: 100% dos serviços críticos monitorados
  - Warning: < 98% de cobertura
  - Critical: < 95% de cobertura

- **Tempo de Detecção**
  - Target: < 5 minutos para detectar falhas
  - Warning: > 3 minutos
  - Critical: > 5 minutos
  - Emergency: > 10 minutos

- **Disponibilidade do Sistema de Alertas**
  - Target: 99.95% de uptime
  - Warning: < 99.9%
  - Critical: < 99.5%
  - Emergency: < 99%

#### SLA de Escalação
- **Tempo de Escalação Automática**
  - Level 1 → Level 2: 30 minutos
  - Level 2 → Level 3: 60 minutos
  - Level 3 → Management: 2 horas

- **Taxa de Resolução por Nível**
  - Level 1: > 60% dos incidentes
  - Level 2: > 85% dos incidentes restantes
  - Level 3: > 95% dos incidentes restantes

### SLA de Dashboard e Visualização

#### SLA de Performance da Interface
- **Tempo de Carregamento do Dashboard**
  - Target: < 2 segundos
  - Warning: > 1.5 segundos
  - Critical: > 2 segundos
  - Emergency: > 5 segundos

- **Atualização de Dados em Tempo Real**
  - Target: Atualização a cada 30 segundos
  - Warning: > 45 segundos
  - Critical: > 60 segundos
  - Emergency: > 2 minutos

- **Disponibilidade da Interface**
  - Target: 99.9% de uptime
  - Warning: < 99.5%
  - Critical: < 99%

#### SLA de Precisão dos Dados
- **Acurácia das Métricas Exibidas**
  - Target: 99.99% de precisão
  - Warning: < 99.95%
  - Critical: < 99.9%
  - Emergency: < 99%

- **Latência dos Dados**
  - Target: < 1 minuto entre evento e exibição
  - Warning: > 30 segundos
  - Critical: > 1 minuto
  - Emergency: > 5 minutos

#### SLA de Exportação e Relatórios
- **Tempo de Geração de Relatórios**
  - Relatório simples: < 30 segundos
  - Relatório completo: < 5 minutos
  - Relatório histórico: < 15 minutos

- **Disponibilidade de Exportação**
  - Target: 99.5% de sucesso na exportação
  - Warning: < 99%
  - Critical: < 95%

### SLA por Categoria de Sistema

#### SLA Diferenciado por Criticidade
- **Sistemas Críticos (Tier 1)**
  - Availability: 99.99%
  - MTTR: < 15 minutos
  - MTTA: < 5 minutos
  - Performance: P95 < 100ms

- **Sistemas Importantes (Tier 2)**
  - Availability: 99.9%
  - MTTR: < 1 hora
  - MTTA: < 15 minutos
  - Performance: P95 < 200ms

- **Sistemas Padrão (Tier 3)**
  - Availability: 99.5%
  - MTTR: < 4 horas
  - MTTA: < 30 minutos
  - Performance: P95 < 500ms

#### SLA por Tipo de Sistema
- **APIs e Serviços Web**
  - Availability: 99.95%
  - Response Time: P95 < 200ms
  - Error Rate: < 0.1%
  - Throughput: > 1000 RPS

- **Bancos de Dados**
  - Availability: 99.99%
  - Query Response Time: P95 < 100ms
  - Connection Success Rate: > 99.9%
  - Backup Success Rate: 100%

- **Sistemas de Email**
  - Availability: 99.5%
  - Delivery Success Rate: > 99%
  - Delivery Time: < 5 minutos
  - Spam Detection: > 95%

### SLA de Comunicação e Transparência

#### SLA de Notificação de Incidentes
- **Tempo para Comunicação Inicial**
  - Critical: < 5 minutos
  - Warning: < 15 minutos
  - Info: < 30 minutos

- **Frequência de Atualizações**
  - Durante incidente crítico: A cada 15 minutos
  - Durante incidente warning: A cada 30 minutos
  - Resolução: Comunicação imediata

#### SLA de Documentação
- **Post-Mortem de Incidentes**
  - Incidentes críticos: Dentro de 48 horas
  - Incidentes importantes: Dentro de 1 semana
  - Documentação completa: 100% dos incidentes > 1 hora

### Métricas de SLA por Período

#### Real-time
- Current Availability
- Current Response Time
- Errors Last Hour
- Active Incidents

#### Diário
- Availability Today
- Average Response Time
- Error Rate
- Peak Usage

#### Mensal
- Availability MTD (Month to Date)
- SLA Breach Minutes
- Trend Analysis
- Performance Summary

#### Trimestral
- Availability QTD (Quarter to Date)
- SLA Credits/Penalties
- Improvement Actions
- Capacity Planning

#### Anual
- Availability YTD (Year to Date)
- Annual SLA Compliance
- Cost of Downtime
- Infrastructure Investments

### Alertas e Thresholds

#### Info Level
- Availability: > 99.9%
- Response Time: < 100ms
- Error Rate: < 0.01%
- Resource Usage: < 70%

#### Warning Level
- Availability: 99.5% - 99.9%
- Response Time: 100ms - 200ms
- Error Rate: 0.01% - 0.1%
- Resource Usage: 70% - 85%

#### Critical Level
- Availability: 99% - 99.5%
- Response Time: 200ms - 500ms
- Error Rate: 0.1% - 1%
- Resource Usage: 85% - 95%

#### Emergency Level
- Availability: < 99%
- Response Time: > 500ms
- Error Rate: > 1%
- Resource Usage: > 95%

### SLA Reporting

#### Métricas de Compliance
- SLA Achievement Percentage
- Breach Duration
- Root Cause Analysis
- Recovery Time Objective (RTO)
- Recovery Point Objective (RPO)

#### Financial Impact
- SLA Credits
- Penalty Calculations
- Cost per Minute of Downtime
- Revenue Impact

#### Improvement Metrics
- Trend Analysis
- Performance Improvements
- Infrastructure Upgrades
- Process Optimizations

## Implementação no Sistema

### Estrutura de Dados Recomendada

```json
{
  "metrics": {
    "availability": {
      "current": 99.97,
      "target": 99.9,
      "period": "monthly"
    },
    "performance": {
      "response_time": {
        "avg": 145,
        "p95": 280,
        "p99": 450
      },
      "throughput": {
        "current_rps": 2500,
        "target_rps": 5000
      },
      "error_rate": {
        "current": 0.02,
        "target": 0.1
      }
    },
    "connectivity": {
      "ping": {
        "avg_rtt": 25,
        "packet_loss": 0.01,
        "jitter": 5
      },
      "snmp": {
        "response_time": 850,
        "success_rate": 99.8
      }
    },
    "incidents": {
      "total_incidents": {
        "daily": 12,
        "weekly": 85,
        "monthly": 340
      },
      "incident_duration": {
        "avg_duration_hours": 2.5,
        "max_duration_hours": 8.2,
        "incidents_over_24h": 3
      },
      "by_severity": {
        "info": {
          "count": 150,
          "avg_duration_minutes": 45
        },
        "warning": {
          "count": 120,
          "avg_duration_minutes": 90
        },
        "critical": {
          "count": 50,
          "avg_duration_minutes": 180
        },
        "emergency": {
          "count": 20,
          "avg_duration_minutes": 360
        }
      },
      "response_times": {
        "mtta_minutes": 12,
        "mttr_hours": 1.8,
        "mttf_hours": 3.2,
        "mtbf_hours": 168
      },
      "alert_metrics": {
        "active_alerts": 25,
        "alerts_per_hour": 8.5,
        "false_positive_rate": 3.2,
        "auto_resolved": 65.5,
        "escalated": 12.3
      }
    },
    "dashboard_metrics": {
      "sla_summary": {
        "overall_sla": 99.15,
        "targets_met": 2,
        "total_systems": 4,
        "systems_status": {
          "achieved": 2,
          "attention": 0,
          "critical": 2
        }
      },
      "systems_performance": [
        {
          "system": "API Principal",
          "sla_target": 99.9,
          "current_sla": 99.2,
          "uptime": "99.2%",
          "downtime": "5h 45m",
          "incidents": 2,
          "trend": "down",
          "status": "critical",
          "criticality": "tier1"
        },
        {
          "system": "Banco de Dados",
          "sla_target": 99.5,
          "current_sla": 99.8,
          "uptime": "99.8%",
          "downtime": "1h 30m",
          "incidents": 1,
          "trend": "up",
          "status": "achieved",
          "criticality": "tier1"
        },
        {
          "system": "Sistema Web",
          "sla_target": 99.0,
          "current_sla": 98.5,
          "uptime": "98.5%",
          "downtime": "10h 20m",
          "incidents": 3,
          "trend": "down",
          "status": "critical",
          "criticality": "tier2"
        },
        {
          "system": "Email Server",
          "sla_target": 98.0,
          "current_sla": 99.1,
          "uptime": "99.1%",
          "downtime": "6h 15m",
          "incidents": 2,
          "trend": "up",
          "status": "achieved",
          "criticality": "tier3"
        }
      ],
      "trends": {
        "improving_systems": 2,
        "degrading_systems": 2,
        "stable_systems": 0
      }
    },
    "business_impact": {
      "financial": {
        "downtime_cost_per_hour": 5000,
        "total_cost_this_month": 115750,
        "sla_penalties": 2500,
        "potential_savings": 15000
      },
      "user_experience": {
        "user_satisfaction": 85.2,
        "complaints_received": 12,
        "productivity_impact": "medium"
      }
    }
  },
  "sla_status": {
    "overall": "compliant",
    "breaches": 0,
    "credits": 0,
    "next_review": "2025-10-01",
    "incident_sla": {
      "mtta_compliance": 98.5,
      "mttr_compliance": 94.2,
      "alert_duration_compliance": 96.8
    }
  }
}
```

### Endpoints de API Sugeridos

```python
# Endpoints para métricas e SLA
GET /api/metrics/summary
GET /api/metrics/availability?period=monthly
GET /api/metrics/performance?period=daily
GET /api/sla/status
GET /api/sla/history?period=quarterly
GET /api/alerts/thresholds

# Endpoints específicos para incidentes e alertas
GET /api/incidents/summary
GET /api/incidents/total?period=daily|weekly|monthly
GET /api/incidents/duration/stats
GET /api/incidents/by-severity
GET /api/incidents/response-times
GET /api/alerts/active
GET /api/alerts/metrics
GET /api/alerts/duration?status=active|resolved
GET /api/sla/incidents/compliance

# Endpoints específicos para dashboard e visualização
GET /api/dashboard/sla-summary
GET /api/dashboard/systems-performance
GET /api/dashboard/systems/trends
GET /api/dashboard/systems/status-distribution
GET /api/dashboard/systems/{system_id}/details
GET /api/dashboard/business-impact
GET /api/dashboard/export/report
GET /api/dashboard/charts/sla-history
GET /api/dashboard/charts/performance-comparison

# Endpoints por categoria de sistema
GET /api/systems/by-criticality?tier=1|2|3
GET /api/systems/by-type?type=api|database|web|email
GET /api/sla/by-tier
GET /api/sla/compliance/detailed
```

### Configuração de Alertas

```python
ALERT_CONFIGURATION = {
    "availability": {
        "warning": 99.5,
        "critical": 99.0,
        "emergency": 98.0
    },
    "response_time": {
        "warning": 150,
        "critical": 200,
        "emergency": 500
    },
    "error_rate": {
        "warning": 0.05,
        "critical": 0.1,
        "emergency": 1.0
    },
    "ping": {
        "rtt_warning": 50,
        "rtt_critical": 100,
        "packet_loss_warning": 0.1,
        "packet_loss_critical": 1.0
    },
    "snmp": {
        "response_time_warning": 2000,
        "response_time_critical": 5000,
        "timeout_rate_warning": 1.0,
        "timeout_rate_critical": 5.0
    },
    "incidents": {
        "total_incidents_daily": {
            "warning": 40,
            "critical": 50,
            "emergency": 100
        },
        "alert_duration_hours": {
            "warning": 1,
            "critical": 2,
            "emergency": 4
        },
        "mtta_minutes": {
            "warning": 10,
            "critical": 15,
            "emergency": 30
        },
        "mttr_hours": {
            "info": 4,
            "warning": 2,
            "critical": 1,
            "emergency": 0.5
        },
        "false_positive_rate": {
            "warning": 3,
            "critical": 5,
            "emergency": 10
        },
        "consecutive_failed_escalations": {
            "warning": 2,
            "critical": 3,
            "emergency": 5
        },
        "active_alerts_threshold": {
            "warning": 20,
            "critical": 30,
            "emergency": 50
        }
    },
    "dashboard": {
        "overall_sla_threshold": {
            "warning": 99.0,
            "critical": 98.5,
            "emergency": 98.0
        },
        "systems_critical_count": {
            "warning": 1,
            "critical": 2,
            "emergency": 3
        },
        "targets_met_percentage": {
            "warning": 75,
            "critical": 50,
            "emergency": 25
        },
        "dashboard_load_time": {
            "warning": 1.5,
            "critical": 2.0,
            "emergency": 5.0
        },
        "data_freshness_minutes": {
            "warning": 1,
            "critical": 2,
            "emergency": 5
        }
    },
    "business_impact": {
        "monthly_cost_threshold": {
            "warning": 100000,
            "critical": 150000,
            "emergency": 200000
        },
        "user_satisfaction": {
            "warning": 85,
            "critical": 75,
            "emergency": 65
        },
        "complaints_daily": {
            "warning": 5,
            "critical": 10,
            "emergency": 20
        }
    },
    "tier_specific": {
        "tier1_availability": {
            "warning": 99.95,
            "critical": 99.9,
            "emergency": 99.5
        },
        "tier2_availability": {
            "warning": 99.5,
            "critical": 99.0,
            "emergency": 98.5
        },
        "tier3_availability": {
            "warning": 99.0,
            "critical": 98.5,
            "emergency": 98.0
        }
    }
}
```

---

*Este documento serve como referência para implementação de métricas e SLA no sistema de monitoramento InfraWatch.*
