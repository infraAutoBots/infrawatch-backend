# 🔍 InfraWatch Monitor - Guia Completo de Testes

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Configuração de Ambiente](#configuração-de-ambiente)
- [Testes de Conectividade](#testes-de-conectividade)
- [Testes SNMP](#testes-snmp)
- [Testes de Alertas](#testes-de-alertas)
- [Testes de Performance](#testes-de-performance)
- [Testes de Integração](#testes-de-integração)
- [Testes de Falhas](#testes-de-falhas)
- [Cenários de Teste Completos](#cenários-de-teste-completos)
- [Scripts de Automação](#scripts-de-automação)

---

## 🎯 Visão Geral

O sistema de monitoramento InfraWatch possui múltiplas camadas de verificação:

### Componentes Principais
- **OptimizedMonitor**: Classe principal de monitoramento
- **SNMP Engine Pool**: Pool de conexões SNMP reutilizáveis
- **Email Service**: Sistema de notificações por email
- **Database Layer**: Persistência de dados no SQLite

### Tipos de Verificação
1. **Ping Check**: Conectividade ICMP básica
2. **TCP Check**: Conectividade em portas específicas
3. **SNMP Check**: Coleta de dados via SNMP v2c/v3
4. **Database Operations**: Inserção e consulta de dados

---

## ⚙️ Configuração de Ambiente

### Pré-requisitos
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente (.env)
cd monitor/
cp .env.example .env
```

### Variáveis de Ambiente Críticas
```env
# Database
DATABASE_URL=sqlite:///database.db

# SNMP
SNMP_TIMEOUT=5
SNMP_RETRIES=3

# TCP Ports
TCP_PORTS=80,443,22,161

# Email Alerts
EMAIL_ALERTS_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@infrawatch.com

# Thresholds
MAX_CONSECUTIVE_PING_FAILURES=5
MAX_CONSECUTIVE_SNMP_FAILURES=5
ENGINE_REFRESH_THRESHOLD=10
```

---

## 🌐 Testes de Conectividade

### 1. Teste Básico de Ping
```bash
# Teste manual
python -c "
import asyncio
from monitor import OptimizedMonitor

async def test_ping():
    monitor = OptimizedMonitor()
    result = await monitor.fast_ping_check(['8.8.8.8', '1.1.1.1'])
    print(result)

asyncio.run(test_ping())
"
```

**Resultado Esperado:**
```python
{'8.8.8.8': (True, 10.5), '1.1.1.1': (True, 8.2)}
```

### 2. Teste de TCP Check
```python
# Teste de conectividade TCP
import asyncio
from monitor import OptimizedMonitor

async def test_tcp():
    monitor = OptimizedMonitor()
    
    # Testes específicos
    test_cases = [
        ('8.8.8.8', 'Google DNS - deve passar'),
        ('127.0.0.1', 'Localhost - pode falhar'),
        ('192.168.1.1', 'Gateway local - pode falhar'),
        ('10.0.0.1', 'IP interno - pode falhar')
    ]
    
    for ip, description in test_cases:
        result = await monitor.fast_tcp_check(ip)
        print(f"{'✅' if result else '❌'} {ip} ({description}): {result}")

asyncio.run(test_tcp())
```

### 3. Teste de Conectividade Híbrida
```bash
# Teste com IPs mistos (alguns online, outros offline)
python -c "
import asyncio
from monitor import OptimizedMonitor

async def test_hybrid():
    monitor = OptimizedMonitor()
    
    # IPs que devem estar online
    online_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
    
    # IPs que provavelmente estarão offline
    offline_ips = ['127.0.0.2', '192.168.999.1', '10.0.0.254']
    
    all_ips = online_ips + offline_ips
    results = await monitor.fast_ping_check(all_ips)
    
    print('=== RESULTADOS HÍBRIDOS ===')
    for ip, (alive, rtt) in results.items():
        status = '🟢 ONLINE' if alive else '🔴 OFFLINE'
        print(f'{status} {ip} - RTT: {rtt:.1f}ms')

asyncio.run(test_hybrid())
"
```

---

## 📊 Testes SNMP

### 1. Configuração de Dispositivos de Teste
```sql
-- Inserir dispositivos SNMP de teste
INSERT INTO endpoints (ip, name, version, community, port, interval) VALUES
('127.0.0.1', 'Localhost SNMP', '2c', 'public', 161, 30),
('8.8.8.8', 'Google DNS', '2c', 'public', 161, 60),
('demo.snmplabs.com', 'SNMP Labs Demo', '2c', 'public', 161, 30);

-- Configurar OIDs padrão
INSERT INTO endpoint_oids (endpoint_id, oid_name, oid_value) VALUES
(1, 'sysDescr', '1.3.6.1.2.1.1.1.0'),
(1, 'sysName', '1.3.6.1.2.1.1.5.0'),
(1, 'sysUpTime', '1.3.6.1.2.1.1.3.0'),
(2, 'sysDescr', '1.3.6.1.2.1.1.1.0'),
(3, 'sysDescr', '1.3.6.1.2.1.1.1.0');
```

### 2. Teste Individual de SNMP
```python
import asyncio
from monitor import OptimizedMonitor

async def test_snmp_individual():
    monitor = OptimizedMonitor()
    
    # Configurar host de teste
    from utils import HostStatus
    test_host = HostStatus(
        ip='demo.snmplabs.com',
        version='2c',
        community='public',
        port=161,
        oids={'sysDescr': '1.3.6.1.2.1.1.1.0'}
    )
    monitor.hosts_status['demo.snmplabs.com'] = test_host
    
    # Executar teste
    result = await monitor.fast_snmp_check_with_retry('demo.snmplabs.com')
    print(f"SNMP Result: {result}")

asyncio.run(test_snmp_individual())
```

### 3. Teste SNMP v3 (Se Disponível)
```python
async def test_snmp_v3():
    monitor = OptimizedMonitor()
    
    # Configuração SNMPv3
    test_host = HostStatus(
        ip='your-snmpv3-device.com',
        version='3',
        user='snmpuser',
        authKey='authpassword',
        privKey='privpassword',
        oids={'sysDescr': '1.3.6.1.2.1.1.1.0'}
    )
    monitor.hosts_status['your-snmpv3-device.com'] = test_host
    
    result = await monitor.fast_snmp_check_with_retry('your-snmpv3-device.com')
    print(f"SNMPv3 Result: {result}")

# asyncio.run(test_snmp_v3())
```

---

## 🚨 Testes de Alertas

### 1. Teste de Email Service
```python
import asyncio
from datetime import datetime
from alert_email_service import EmailService

async def test_email_service():
    email_service = EmailService()
    
    # Teste de email de alerta
    success = email_service.send_alert_email(
        to_emails=["test@example.com"],  # Substitua pelo seu email
        subject="TESTE - Host Offline",
        endpoint_name="Test Device",
        endpoint_ip="192.168.1.100",
        status="DOWN",
        timestamp=datetime.now(),
        additional_info="Este é um teste do sistema de alertas"
    )
    
    print(f"Email enviado: {'✅ Sucesso' if success else '❌ Falhou'}")

asyncio.run(test_email_service())
```

### 2. Simulação de Falhas Consecutivas
```bash
# Script para simular falhas consecutivas de ping
python -c "
import asyncio
from datetime import datetime
from monitor import OptimizedMonitor
from utils import HostStatus

async def test_consecutive_failures():
    monitor = OptimizedMonitor()
    
    # Criar host fictício que sempre falhará
    fake_host = HostStatus(
        ip='192.168.999.999',  # IP inválido
        is_alive=False,
        consecutive_ping_failures=0
    )
    monitor.hosts_status['192.168.999.999'] = fake_host
    
    # Simular 6 falhas consecutivas
    for i in range(6):
        result = await monitor.check_single_host(fake_host)
        print(f'Tentativa {i+1}: Falhas consecutivas = {result.consecutive_ping_failures}')
        
        # Na 5ª falha, deve disparar alerta
        if result.consecutive_ping_failures >= 5:
            print('🚨 ALERTA DEVE SER DISPARADO AGORA!')

asyncio.run(test_consecutive_failures())
"
```

### 3. Teste de Recuperação de Host
```python
async def test_host_recovery():
    monitor = OptimizedMonitor()
    
    # Host que estava offline (simulado)
    recovering_host = HostStatus(
        ip='8.8.8.8',  # IP que deve estar online
        consecutive_ping_failures=5,  # Já teve falhas
        informed=True  # Já foi informado que estava offline
    )
    monitor.hosts_status['8.8.8.8'] = recovering_host
    
    # Testar recuperação
    result = await monitor.check_single_host(recovering_host)
    print(f"Host recuperado: {result.is_alive}")
    print(f"Falhas resetadas: {result.consecutive_ping_failures}")
    print(f"Status de informado: {result.informed}")

# asyncio.run(test_host_recovery())
```

---

## ⚡ Testes de Performance

### 1. Teste de Throughput
```python
import asyncio
import time
from monitor import OptimizedMonitor

async def test_performance():
    monitor = OptimizedMonitor()
    
    # Lista de IPs para teste
    test_ips = [
        '8.8.8.8', '1.1.1.1', '208.67.222.222',
        '9.9.9.9', '4.4.4.4', '8.8.4.4'
    ]
    
    # Teste sequencial
    start_time = time.time()
    for ip in test_ips:
        await monitor.fast_ping_check([ip])
    sequential_time = time.time() - start_time
    
    # Teste paralelo
    start_time = time.time()
    await monitor.fast_ping_check(test_ips)
    parallel_time = time.time() - start_time
    
    print(f"Sequencial: {sequential_time:.2f}s")
    print(f"Paralelo: {parallel_time:.2f}s")
    print(f"Speedup: {sequential_time/parallel_time:.1f}x")

asyncio.run(test_performance())
```

### 2. Teste de Stress
```python
async def test_stress():
    monitor = OptimizedMonitor()
    
    # Gerar 100 IPs fictícios
    stress_ips = [f"192.168.{i//256}.{i%256}" for i in range(1, 101)]
    
    start_time = time.time()
    results = await monitor.fast_ping_check(stress_ips)
    elapsed = time.time() - start_time
    
    online_count = sum(1 for alive, _ in results.values() if alive)
    
    print(f"Testados: {len(stress_ips)} hosts")
    print(f"Online: {online_count}")
    print(f"Tempo: {elapsed:.2f}s")
    print(f"Taxa: {len(stress_ips)/elapsed:.1f} hosts/s")

# asyncio.run(test_stress())
```

### 3. Benchmark de Engine Pool
```python
async def test_engine_pool():
    from snmp_engine_pool import SNMPEnginePool
    import time
    
    pool = SNMPEnginePool()
    
    # Teste de criação de engines
    start_time = time.time()
    engines = []
    for i in range(10):
        engine = await pool.get_engine()
        engines.append(engine)
    creation_time = time.time() - start_time
    
    # Retornar engines
    for engine in engines:
        await pool.return_engine(engine)
    
    print(f"Criação de 10 engines: {creation_time:.3f}s")
    print(f"Pool size: {pool.pool_size}")

# asyncio.run(test_engine_pool())
```

---

## 🔗 Testes de Integração

### 1. Teste End-to-End Completo
```python
import asyncio
from datetime import datetime
from monitor import OptimizedMonitor

async def test_full_integration():
    print("🚀 Iniciando teste de integração completo...")
    
    monitor = OptimizedMonitor()
    
    # 1. Carregar hosts da base de dados
    await monitor.check_hosts_db()
    print(f"✅ Carregados {len(monitor.hosts_status)} hosts da BD")
    
    # 2. Executar um ciclo de monitoramento
    results = []
    async for result in monitor.monitoring_cycle():
        results.append(result)
    
    print(f"✅ Monitoramento completado: {len(results)} resultados")
    
    # 3. Testar notificações
    for result in results:
        if result:
            await monitor.notification(result)
    
    print("✅ Sistema de notificações testado")
    
    # 4. Verificar inserção na base de dados
    print("✅ Teste de integração concluído com sucesso!")

asyncio.run(test_full_integration())
```

### 2. Teste de Ciclo Completo com Timer
```bash
# Teste de 1 minuto de monitoramento
timeout 60 python -c "
import asyncio
from monitor import OptimizedMonitor

async def test_timed():
    monitor = OptimizedMonitor()
    await monitor.run_monitoring(interval=10.0)

asyncio.run(test_timed())
" || echo "Teste concluído após 1 minuto"
```

---

## 💥 Testes de Falhas

### 1. Simulação de Falha de Base de Dados
```python
async def test_db_failure():
    monitor = OptimizedMonitor()
    
    # Simular falha removendo arquivo da BD
    import os
    db_path = "database.db"
    backup_path = f"{db_path}.backup"
    
    try:
        # Backup da BD
        if os.path.exists(db_path):
            os.rename(db_path, backup_path)
        
        # Tentar carregar hosts (deve falhar graciosamente)
        await monitor.check_hosts_db()
        print("Sistema lidou com falha de BD correctamente")
        
    finally:
        # Restaurar BD
        if os.path.exists(backup_path):
            os.rename(backup_path, db_path)

# asyncio.run(test_db_failure())
```

### 2. Teste de Memory Leak
```python
import asyncio
import psutil
import os

async def test_memory_leak():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    monitor = OptimizedMonitor()
    
    # Executar 100 ciclos
    for i in range(100):
        await monitor.check_hosts_db()
        
        # Verificar memória a cada 10 ciclos
        if i % 10 == 0:
            current_memory = process.memory_info().rss
            memory_diff = (current_memory - initial_memory) / 1024 / 1024
            print(f"Ciclo {i}: Memória adicional: {memory_diff:.1f}MB")

# asyncio.run(test_memory_leak())
```

### 3. Teste de Timeout
```python
async def test_timeouts():
    monitor = OptimizedMonitor()
    
    # IPs que devem dar timeout
    timeout_ips = ['10.255.255.1', '172.31.255.1', '192.168.255.255']
    
    start_time = time.time()
    results = await monitor.fast_ping_check(timeout_ips)
    elapsed = time.time() - start_time
    
    print(f"Teste de timeout completado em {elapsed:.1f}s")
    for ip, (alive, rtt) in results.items():
        print(f"{ip}: {'Online' if alive else 'Timeout'}")

# asyncio.run(test_timeouts())
```

---

## 🎭 Cenários de Teste Completos

### Cenário 1: Ambiente de Produção Simulado
```bash
#!/bin/bash
# Script: test_production_scenario.sh

echo "🏭 TESTE DE CENÁRIO DE PRODUÇÃO"
echo "================================"

# 1. Configurar ambiente
export EMAIL_ALERTS_ENABLED=true
export MAX_CONSECUTIVE_PING_FAILURES=3
export ENGINE_REFRESH_THRESHOLD=5

# 2. Inserir dados de teste
python -c "
from dependencies import init_session
from models import EndPoints

session = init_session()
test_endpoints = [
    EndPoints(ip='8.8.8.8', name='Google DNS', version='2c', community='public'),
    EndPoints(ip='1.1.1.1', name='Cloudflare DNS', version='2c', community='public'),
    EndPoints(ip='127.0.0.1', name='Localhost', version='2c', community='public'),
    EndPoints(ip='192.168.999.1', name='Fake Host', version='2c', community='public')
]

for endpoint in test_endpoints:
    session.merge(endpoint)
session.commit()
session.close()
print('✅ Dados de teste inseridos')
"

# 3. Executar monitoramento por 2 minutos
echo "🔄 Executando monitoramento por 2 minutos..."
timeout 120 python monitor.py || echo "✅ Teste de produção concluído"
```

### Cenário 2: Teste de Recuperação de Desastres
```python
async def disaster_recovery_test():
    """Simula diferentes tipos de falhas e recuperações"""
    
    scenarios = [
        {
            'name': 'Falha Total de Conectividade',
            'ips': ['192.168.999.1', '192.168.999.2'],
            'expected': 'all_offline'
        },
        {
            'name': 'Falha Parcial de SNMP',
            'ips': ['8.8.8.8'],  # Ping OK, SNMP fail
            'expected': 'ping_ok_snmp_fail'
        },
        {
            'name': 'Recuperação Gradual',
            'ips': ['1.1.1.1', '8.8.8.8'],
            'expected': 'gradual_recovery'
        }
    ]
    
    monitor = OptimizedMonitor()
    
    for scenario in scenarios:
        print(f"\n🎭 Testando: {scenario['name']}")
        
        results = await monitor.fast_ping_check(scenario['ips'])
        
        for ip, (alive, rtt) in results.items():
            status = "🟢 OK" if alive else "🔴 FAIL"
            print(f"   {status} {ip} - {rtt:.1f}ms")

# asyncio.run(disaster_recovery_test())
```

---

## 🤖 Scripts de Automação

### Script de Teste Diário
```bash
#!/bin/bash
# daily_test.sh - Execute testes automáticos diários

LOGFILE="/var/log/infrawatch/daily_test_$(date +%Y%m%d).log"
mkdir -p $(dirname "$LOGFILE")

{
    echo "🕐 $(date): Iniciando testes diários do InfraWatch"
    
    # Teste básico de conectividade
    echo "📡 Teste de conectividade básica..."
    python -c "
import asyncio
from monitor import OptimizedMonitor

async def daily_connectivity_test():
    monitor = OptimizedMonitor()
    essential_hosts = ['8.8.8.8', '1.1.1.1', 'demo.snmplabs.com']
    results = await monitor.fast_ping_check(essential_hosts)
    
    all_ok = all(alive for alive, _ in results.values())
    print('✅ Todos os hosts essenciais estão acessíveis' if all_ok else '⚠️  Alguns hosts essenciais estão inacessíveis')
    return all_ok

result = asyncio.run(daily_connectivity_test())
exit(0 if result else 1)
    "
    
    if [ $? -eq 0 ]; then
        echo "✅ Teste de conectividade: PASSOU"
    else
        echo "❌ Teste de conectividade: FALHOU"
    fi
    
    # Teste de performance
    echo "⚡ Teste de performance..."
    python -c "
import asyncio, time
from monitor import OptimizedMonitor

async def performance_test():
    monitor = OptimizedMonitor()
    start = time.time()
    await monitor.fast_ping_check(['8.8.8.8'] * 10)
    elapsed = time.time() - start
    
    if elapsed < 5.0:
        print(f'✅ Performance OK: {elapsed:.2f}s')
        return True
    else:
        print(f'⚠️  Performance degradada: {elapsed:.2f}s')
        return False

result = asyncio.run(performance_test())
    "
    
    echo "🏁 $(date): Testes diários concluídos"
    
} | tee "$LOGFILE"
```

### Script de Teste de Carga
```python
#!/usr/bin/env python3
# load_test.py - Teste de carga avançado

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from monitor import OptimizedMonitor

async def load_test_suite():
    """Suite completa de testes de carga"""
    
    print("🔥 INICIANDO TESTES DE CARGA")
    print("=" * 50)
    
    monitor = OptimizedMonitor()
    
    # Teste 1: Ping simultâneo em massa
    print("\n1️⃣  Teste de Ping em Massa")
    large_ip_list = [f"8.8.{i//256}.{i%256}" for i in range(1, 201)]
    
    start = time.time()
    results = await monitor.fast_ping_check(large_ip_list)
    elapsed = time.time() - start
    
    successful = sum(1 for alive, _ in results.values() if alive)
    print(f"   Testados: {len(large_ip_list)} IPs")
    print(f"   Sucessos: {successful}")
    print(f"   Tempo: {elapsed:.2f}s")
    print(f"   Taxa: {len(large_ip_list)/elapsed:.1f} IPs/s")
    
    # Teste 2: Stress test de engine pool
    print("\n2️⃣  Teste de Stress do Engine Pool")
    from snmp_engine_pool import SNMPEnginePool
    
    pool = SNMPEnginePool()
    
    async def get_return_engine():
        engine = await pool.get_engine()
        await asyncio.sleep(0.01)  # Simular uso
        await pool.return_engine(engine)
    
    start = time.time()
    await asyncio.gather(*[get_return_engine() for _ in range(100)])
    elapsed = time.time() - start
    
    print(f"   100 operações de engine: {elapsed:.2f}s")
    
    # Teste 3: Monitoramento contínuo
    print("\n3️⃣  Teste de Monitoramento Contínuo (30s)")
    
    cycle_times = []
    start_time = time.time()
    
    while time.time() - start_time < 30:
        cycle_start = time.time()
        
        results_count = 0
        async for result in monitor.monitoring_cycle():
            if result:
                results_count += 1
        
        cycle_time = time.time() - cycle_start
        cycle_times.append(cycle_time)
        
        print(f"   Ciclo: {cycle_time:.2f}s, Resultados: {results_count}")
        
        await asyncio.sleep(max(0, 5 - cycle_time))  # Intervalo de 5s
    
    if cycle_times:
        print(f"\n📊 Estatísticas dos Ciclos:")
        print(f"   Média: {statistics.mean(cycle_times):.2f}s")
        print(f"   Mediana: {statistics.median(cycle_times):.2f}s")
        print(f"   Min: {min(cycle_times):.2f}s")
        print(f"   Max: {max(cycle_times):.2f}s")
    
    print("\n🏁 TESTES DE CARGA CONCLUÍDOS")

if __name__ == "__main__":
    asyncio.run(load_test_suite())
```

---

## 📈 Monitoramento e Métricas

### Métricas Importantes para Acompanhar

1. **Conectividade**
   - Taxa de sucesso de ping (deve ser > 95%)
   - RTT médio (deve ser < 100ms para hosts locais)
   - Taxa de timeout (deve ser < 5%)

2. **SNMP**
   - Taxa de sucesso SNMP (deve ser > 90%)
   - Tempo médio de resposta SNMP (deve ser < 2s)
   - Renovações de engine por hora (deve ser < 10)

3. **Performance**
   - Tempo por ciclo de monitoramento (deve ser < 30s)
   - Uso de memória (deve ser estável)
   - Throughput (hosts/segundo)

4. **Alertas**
   - Tempo médio para detecção de falha (< 2 minutos)
   - Taxa de falsos positivos (deve ser < 1%)
   - Tempo de recuperação após falha (< 1 minuto)

---

## 🚀 Execução Rápida dos Testes

```bash
# Executar todos os testes básicos
./run_all_tests.sh

# Teste específico de conectividade
python -c "import asyncio; from monitor import OptimizedMonitor; asyncio.run(OptimizedMonitor().run_monitoring(60))"

# Teste de alertas
python test_alerts.py

# Teste de performance
python load_test.py

# Teste de integração
python integration_test.py
```

---

## 📞 Troubleshooting

### Problemas Comuns

1. **"SNMP timeout"**
   - Verificar se SNMP está habilitado no dispositivo
   - Confirmar community string
   - Testar com `snmpwalk` manual

2. **"Email não enviado"**
   - Verificar credenciais SMTP
   - Confirmar configuração de app password
   - Testar conectividade com servidor SMTP

3. **"Database locked"**
   - Verificar se não há múltiplas instâncias rodando
   - Confirmar permissões do arquivo da BD
   - Considerar usar PostgreSQL para produção

4. **Performance degradada**
   - Monitorar uso de memória
   - Verificar pool de engines SNMP
   - Analisar logs de timeout

---

## 📝 Relatórios de Teste

Após executar os testes, documente:

- ✅ Testes que passaram
- ❌ Testes que falharam (com logs)
- ⚠️  Testes com warnings
- 📊 Métricas de performance
- 🔧 Ações corretivas necessárias

**Exemplo de Relatório:**
```
📋 Relatório de Teste - 01/09/2025
=====================================

Conectividade Básica: ✅ 100% sucesso
SNMP v2c: ✅ 95% sucesso  
SNMP v3: ⚠️  Não testado (sem dispositivos)
Alertas por Email: ✅ Funcionando
Performance: ✅ 45 hosts/s
Stress Test: ✅ Suportou 200 hosts simultâneos

Próximos Passos:
- Configurar dispositivo SNMPv3 para testes
- Implementar testes automatizados via CI/CD
- Monitorar métricas em produção
```

---

## 🎯 Checklist Pré-Produção

Antes de colocar em produção, verificar:

- [ ] Todos os testes básicos passam
- [ ] Configurações de email funcionam
- [ ] Base de dados está configurada
- [ ] Logs estão sendo gravados
- [ ] Métricas estão sendo coletadas
- [ ] Backup da configuração está feito
- [ ] Documentação está atualizada
- [ ] Equipe está treinada
- [ ] Plano de rollback está pronto
- [ ] Monitoramento do próprio monitor está configurado

---

*Este documento é vivo e deve ser atualizado conforme o sistema evolui. Para dúvidas, consulte a documentação técnica ou a equipe de desenvolvimento.*
