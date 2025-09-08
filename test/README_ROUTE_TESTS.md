# 🧪 Script de Testes de Rotas - InfraWatch

## 📋 Descrição

O script `run_route_te./run_route_tests.sh config        # Apenas configuração
./run_route_tests.sh alerts       # Apenas alertas
./run_route_tests.sh monitor       # Apenas monitoramento
./run_route_tests.sh sla           # Apenas SLA.sh` foi criado automaticamente após análise dos testes existentes no projeto InfraWatch. Ele executa todos os testes de rotas da API de forma organizada e produz relatórios detalhados.

## 🎯 Testes Incluídos

### 1. **Testes de Autenticação** (`test_auth_api.py`)
- Login via JSON
- Login via formulário
- Refresh token
- Validação de tokens

### 2. **Testes de Usuários - Python** (`test_users_api.py`)
- CRUD completo de usuários
- Paginação e filtros
- Estatísticas de usuários
- Validação de permissões

### 3. **Testes de Usuários - cURL** (`test_routes.sh`)
- Testes usando curl
- Validação de respostas JSON
- Operações CRUD via HTTP

### 4. **Testes de Configuração** (`test_config_routes.py`)
- Endpoints de configuração do sistema
- Parâmetros de monitoramento
- Configurações de alertas

### 5. **Testes de Alertas** (`test_alerts_routes.py`)
- Sistema de alertas e notificações
- Criação e gerenciamento de alertas
- Integração com webhooks

### 6. **Testes de Monitoramento** (`test_monitor_api.py`)
- Status dos serviços
- Métricas de performance
- Health checks

### 7. **Testes de SLA** (`test_sla_routes.py`)
- Resumo de SLA por período
- Métricas específicas por endpoint
- Resumo de incidentes
- Métricas de performance
- Compliance e targets SLA

## 🚀 Como Usar

### Pré-requisitos

1. **API deve estar rodando:**
   ```bash
   cd /home/ubuntu/Code/infrawatch/infrawatch-backend
   python api/app.py
   ```

2. **Dependências serão instaladas automaticamente:**
   - `jq` (para processamento JSON)
   - `requests` (Python)

### Execução

```bash
# Ir para o diretório de testes
cd /home/ubuntu/Code/infrawatch/infrawatch-backend/test

# Executar todos os testes
./run_route_tests.sh

# Ou usando bash explicitamente
bash run_route_tests.sh
```

### Opções Disponíveis

```bash
# Executar todos os testes
./run_route_tests.sh all

# Executar testes específicos
./run_route_tests.sh auth          # Apenas autenticação
./run_route_tests.sh users         # Apenas usuários (Python)
./run_route_tests.sh users-curl    # Apenas usuários (cURL)
./run_route_tests.sh config        # Apenas configuração
./run_route_tests.sh alerts        # Apenas alertas
./run_route_tests.sh monitor       # Apenas monitoramento

# Verificar se a API está rodando
./run_route_tests.sh check

# Mostrar ajuda
./run_route_tests.sh help
```

## 📊 Saída do Script

### Durante a Execução
- **Headers coloridos** para cada teste
- **Indicadores visuais** (✅ sucesso, ❌ falha)
- **Tempo de execução** de cada teste
- **Status em tempo real**

### Exemplo de Saída
```
=============================================================================
🧪 INFRAWATCH - EXECUÇÃO DE TESTES DE ROTAS DA API
=============================================================================
Data/Hora: Mon Sep  8 10:30:45 2025
Diretório: /home/ubuntu/Code/infrawatch/infrawatch-backend/test
Log File: logs/route_tests_20250908_103045.log
=============================================================================

🔍 Verificando se a API está rodando...
✅ API está rodando em http://localhost:8000

🚀 Iniciando execução dos testes...

▶ TESTE 1 - ROTAS DE AUTENTICAÇÃO
📝 Testando login, logout e refresh token
----------------------------------------
✅ test_auth_api.py - SUCESSO (3s)

▶ TESTE 2 - ROTAS DE USUÁRIOS (Python)
📝 Testando CRUD de usuários via Python/requests
----------------------------------------
✅ test_users_api.py - SUCESSO (8s)

[... outros testes ...]

=============================================================================
📊 RESUMO DOS TESTES
=============================================================================
Total de testes executados: 6
Testes bem-sucedidos: 6
Testes falharam: 0
Taxa de sucesso: 100%
Log completo: logs/route_tests_20250908_103045.log
=============================================================================
🎉 Todos os testes passaram com sucesso!
```

## 📁 Logs

- **Localização:** `test/logs/`
- **Formato:** `route_tests_YYYYMMDD_HHMMSS.log`
- **Conteúdo:** Saída completa de todos os testes executados

## 🔧 Personalização

### Modificar Configurações
Edite as variáveis no início do script:

```bash
API_BASE="http://localhost:8000"    # URL da API
TEST_DIR="/caminho/para/testes"     # Diretório dos testes
LOG_DIR="$TEST_DIR/logs"            # Diretório dos logs
```

### Adicionar Novos Testes
Para incluir um novo teste, adicione uma função:

```bash
test_new_feature() {
    print_test_header "TESTE X - NOVA FUNCIONALIDADE" "Descrição do teste"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_new_feature.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_new_feature.py" $exit_code $duration
    return $exit_code
}
```

## ⚠️ Troubleshooting

### API não está rodando
```bash
cd /home/ubuntu/Code/infrawatch/infrawatch-backend
python api/app.py
```

### Dependências em falta
```bash
sudo apt-get update && sudo apt-get install -y jq
pip3 install requests
```

### Permissões do script
```bash
chmod +x run_route_tests.sh
```

### Problemas de autenticação
Verifique as credenciais nos arquivos de teste:
- `test_auth_api.py`
- `test_users_api.py`
- `test_config_routes.py`
- etc.

## 📈 Métricas e Relatórios

O script coleta automaticamente:
- ⏱️ **Tempo de execução** de cada teste
- ✅ **Taxa de sucesso/falha**
- 📋 **Logs detalhados** de cada execução
- 📊 **Resumo consolidado** ao final

## 🤝 Contribuição

Para adicionar novos testes ou melhorar o script:

1. Crie seu arquivo de teste seguindo o padrão existente
2. Adicione a função de teste no script
3. Inclua a chamada na função `run_all_tests()`
4. Teste e documente as mudanças

---

**Criado automaticamente através da análise dos testes existentes** 🤖
