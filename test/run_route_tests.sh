#!/bin/bash

# =============================================================================
# Script para executar todos os testes de rotas da API InfraWatch
# =============================================================================
# Criado automaticamente a partir da análise dos testes existentes
# Execute com: bash run_route_tests.sh
# =============================================================================

# Configurações
API_BASE="http://localhost:8000"
TEST_DIR="/home/ubuntu/Code/infrawatch/infrawatch-backend/test"
LOG_DIR="$TEST_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/route_tests_$TIMESTAMP.log"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

print_header() {
    echo -e "${CYAN}=============================================================================${NC}"
    echo -e "${CYAN}🧪 INFRAWATCH - EXECUÇÃO DE TESTES DE ROTAS DA API${NC}"
    echo -e "${CYAN}=============================================================================${NC}"
    echo -e "${YELLOW}Data/Hora:${NC} $(date)"
    echo -e "${YELLOW}Diretório:${NC} $TEST_DIR"
    echo -e "${YELLOW}Log File:${NC} $LOG_FILE"
    echo -e "${CYAN}=============================================================================${NC}"
}

print_test_header() {
    local test_name=$1
    local description=$2
    echo -e "\n${BLUE}▶ $test_name${NC}"
    echo -e "${PURPLE}📝 $description${NC}"
    echo "----------------------------------------"
}

print_result() {
    local test_name=$1
    local status=$2
    local duration=$3
    
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✅ $test_name - SUCESSO${NC} ${YELLOW}(${duration}s)${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ $test_name - FALHOU${NC} ${YELLOW}(${duration}s)${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
}

check_api_status() {
    echo -e "${YELLOW}🔍 Verificando se a API está rodando...${NC}"
    
    if curl -s -f "$API_BASE/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API está rodando em $API_BASE${NC}"
        return 0
    else
        echo -e "${RED}❌ API não está rodando em $API_BASE${NC}"
        echo -e "${YELLOW}💡 Para iniciar a API, execute:${NC}"
        echo -e "   ${CYAN}cd /home/ubuntu/Code/infrawatch/infrawatch-backend${NC}"
        echo -e "   ${CYAN}python api/app.py${NC}"
        return 1
    fi
}

check_dependencies() {
    echo -e "${YELLOW}🔧 Verificando dependências...${NC}"
    
    # Verificar se jq está instalado
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠️ jq não está instalado. Instalando...${NC}"
        sudo apt-get update && sudo apt-get install -y jq
    fi
    
    # Verificar se python3 está disponível
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 não está instalado${NC}"
        return 1
    fi
    
    # Verificar se requests está instalado
    if ! python3 -c "import requests" 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Módulo requests não está instalado. Instalando...${NC}"
        pip3 install requests
    fi
    
    echo -e "${GREEN}✅ Dependências verificadas${NC}"
}

create_log_dir() {
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        echo -e "${GREEN}📁 Diretório de logs criado: $LOG_DIR${NC}"
    fi
}

# =============================================================================
# TESTES INDIVIDUAIS
# =============================================================================

test_auth_routes() {
    print_test_header "TESTE 1 - ROTAS DE AUTENTICAÇÃO" "Testando login, logout e refresh token"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_auth_api.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_auth_api.py" $exit_code $duration
    return $exit_code
}

test_users_routes() {
    print_test_header "TESTE 2 - ROTAS DE USUÁRIOS (Python)" "Testando CRUD de usuários via Python/requests"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_users_api.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_users_api.py" $exit_code $duration
    return $exit_code
}

test_users_routes_curl() {
    print_test_header "TESTE 3 - ROTAS DE USUÁRIOS (cURL)" "Testando CRUD de usuários via cURL"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    if [ -f "test_routes.sh" ]; then
        bash test_routes.sh >> "$LOG_FILE" 2>&1
        local exit_code=$?
    else
        echo -e "${RED}❌ Arquivo test_routes.sh não encontrado${NC}"
        local exit_code=1
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_routes.sh" $exit_code $duration
    return $exit_code
}

test_config_routes() {
    print_test_header "TESTE 4 - ROTAS DE CONFIGURAÇÃO" "Testando endpoints de configuração do sistema"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_config_routes.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_config_routes.py" $exit_code $duration
    return $exit_code
}

test_alerts_routes() {
    print_test_header "TESTE 5 - ROTAS DE ALERTAS" "Testando sistema de alertas e notificações"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_alerts_routes.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_alerts_routes.py" $exit_code $duration
    return $exit_code
}

test_monitor_routes() {
    print_test_header "TESTE 6 - ROTAS DE MONITORAMENTO" "Testando endpoints de monitoramento de serviços"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_monitor_api.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_monitor_api.py" $exit_code $duration
    return $exit_code
}

test_sla_routes() {
    print_test_header "TESTE 7 - ROTAS DE SLA" "Testando endpoints de SLA, métricas e compliance"
    
    local start_time=$(date +%s)
    
    cd "$TEST_DIR"
    python3 test_sla_routes.py >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_result "test_sla_routes.py" $exit_code $duration
    return $exit_code
}

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

run_all_tests() {
    print_header
    
    # Verificações iniciais
    create_log_dir
    check_dependencies
    
    if ! check_api_status; then
        echo -e "${RED}❌ Não é possível continuar sem a API rodando${NC}"
        exit 1
    fi
    
    echo -e "\n${CYAN}🚀 Iniciando execução dos testes...${NC}\n"
    
    # Executar todos os testes
    test_auth_routes
    test_users_routes
    test_users_routes_curl
    test_config_routes
    test_alerts_routes
    test_monitor_routes
    test_sla_routes
    
    # Resumo final
    print_summary
}

print_summary() {
    echo -e "\n${CYAN}=============================================================================${NC}"
    echo -e "${CYAN}📊 RESUMO DOS TESTES${NC}"
    echo -e "${CYAN}=============================================================================${NC}"
    echo -e "${YELLOW}Total de testes executados:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Testes bem-sucedidos:${NC} $PASSED_TESTS"
    echo -e "${RED}Testes falharam:${NC} $FAILED_TESTS"
    echo -e "${YELLOW}Taxa de sucesso:${NC} $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo -e "${YELLOW}Log completo:${NC} $LOG_FILE"
    echo -e "${CYAN}=============================================================================${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 Todos os testes passaram com sucesso!${NC}"
        exit 0
    else
        echo -e "${RED}⚠️ Alguns testes falharam. Verifique o log para mais detalhes.${NC}"
        exit 1
    fi
}

# =============================================================================
# OPÇÕES DE LINHA DE COMANDO
# =============================================================================

show_help() {
    echo -e "${CYAN}InfraWatch - Script de Testes de Rotas${NC}"
    echo -e "${YELLOW}Uso:${NC} $0 [opção]"
    echo ""
    echo -e "${YELLOW}Opções:${NC}"
    echo "  all              Executa todos os testes (padrão)"
    echo "  auth             Executa apenas testes de autenticação"
    echo "  users            Executa apenas testes de usuários (Python)"
    echo "  users-curl       Executa apenas testes de usuários (cURL)"
    echo "  config           Executa apenas testes de configuração"
    echo "  alerts           Executa apenas testes de alertas"
    echo "  monitor          Executa apenas testes de monitoramento"
    echo "  sla              Executa apenas testes de SLA"
    echo "  check            Verifica se a API está rodando"
    echo "  help, -h, --help Mostra esta ajuda"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  $0                    # Executa todos os testes"
    echo "  $0 auth              # Executa apenas testes de auth"
    echo "  $0 check             # Verifica status da API"
}

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

case "${1:-all}" in
    "all")
        run_all_tests
        ;;
    "auth")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_auth_routes
        ;;
    "users")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_users_routes
        ;;
    "users-curl")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_users_routes_curl
        ;;
    "config")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_config_routes
        ;;
    "alerts")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_alerts_routes
        ;;
    "monitor")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_monitor_routes
        ;;
    "sla")
        print_header
        create_log_dir
        check_dependencies
        check_api_status && test_sla_routes
        ;;
    "check")
        check_api_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opção inválida: $1${NC}"
        echo -e "${YELLOW}Use '$0 help' para ver as opções disponíveis${NC}"
        exit 1
        ;;
esac
