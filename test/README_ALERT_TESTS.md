# Testes da API de Alertas

Este diretório contém testes completos para todas as rotas da API de alertas do InfraWatch.

## Arquivos de Teste

### `test_alert_routes.py`
Teste completo e automatizado de todas as funcionalidades da API de alertas:

- **Autenticação**: Login automático com token JWT
- **CRUD Completo**: Criação, listagem, atualização e remoção de alertas  
- **Paginação**: Teste de paginação com diferentes tamanhos de página
- **Filtros Avançados**: Testes de todos os filtros disponíveis
- **Busca**: Teste de busca por texto em múltiplos campos
- **Ordenação**: Teste de ordenação por diferentes campos
- **Ações**: Teste de acknowledge, resolve e assign
- **Ações em Lote**: Teste de operações em múltiplos alertas
- **Estatísticas**: Teste do dashboard de estatísticas
- **Tratamento de Erros**: Teste de operações inválidas
- **Cleanup**: Limpeza automática dos dados de teste

## Como Executar

### 1. Pré-requisitos

```bash
# Instalar dependências (se necessário)
pip install requests

# Certificar-se que a API está rodando
cd infrawatch-backend
python api/app.py
```

### 2. Executar os Testes

#### Opção 1: Executar teste específico de alertas
```bash
cd infrawatch-backend/test
python3 test_alert_routes.py
```

#### Opção 2: Executar todos os testes (incluindo alertas)
```bash
cd infrawatch-backend/test
bash test_routes.sh
```

## Configuração

### Credenciais de Teste
Os testes usam as seguintes credenciais (configuradas em `TEST_CREDENTIALS`):

```python
TEST_CREDENTIALS = {
    "email": "ndondadaniel2020@gmail.com", 
    "password": "ndondadaniel2020@gmail.com"
}
```

**Importante**: O usuário precisa ter permissão de ADMIN ou MONITOR para executar todos os testes.

### URL da API
Por padrão, os testes apontam para: `http://localhost:8000`

Para alterar, modifique a variável `API_BASE` no início do arquivo.

## Estrutura dos Testes

### 1. Teste de Criação (`test_create_alert`)
Cria 4 alertas de teste com diferentes:
- Severidades: critical, high, medium, low
- Categorias: performance, security, network, infrastructure
- Impactos: high, medium, low

### 2. Teste de Listagem (`test_list_alerts`)
Testa 17 cenários diferentes:
- Listagem básica e paginação
- Filtros por severidade, status, categoria, impacto
- Busca por texto
- Ordenação
- Combinações de filtros

### 3. Teste de Estatísticas (`test_get_alert_stats`)
Verifica se o endpoint de stats retorna:
- Contadores básicos
- MTTR (Mean Time To Resolution)
- Distribuição por categoria e sistema

### 4. Teste de Detalhes (`test_get_alert_details`)
Obtém detalhes individuais com:
- Dados completos do alerta
- Histórico de logs de ações

### 5. Teste de Atualização (`test_update_alert`)
Atualiza campos como:
- Título e descrição
- Severidade e impacto
- Responsável

### 6. Teste de Ações (`test_alert_actions`)
Testa as 3 ações principais:
- **acknowledge**: Reconhecer alerta
- **assign**: Atribuir responsável
- **resolve**: Resolver alerta

### 7. Teste de Ações em Lote (`test_bulk_actions`)
Cria alertas adicionais e testa:
- Reconhecimento em lote
- Contagem de alertas atualizados

### 8. Teste de Operações Inválidas (`test_invalid_operations`)
Verifica tratamento de erros para:
- IDs inexistentes
- Dados inválidos ou malformados
- Parâmetros incorretos
- Ações inválidas

## Relatório de Resultados

O teste gera um relatório completo incluindo:

```
📊 RELATÓRIO FINAL DOS TESTES
============================================================
Testes executados: 8
Testes aprovados: 8  
Testes falharam: 0
Taxa de sucesso: 100.0%
Tempo total: 45.67s

Detalhes por teste:
  ✅ Criação de alertas          (5.23s)
  ✅ Listagem e filtros          (12.45s)
  ✅ Estatísticas                (2.11s)
  ✅ Detalhes de alertas         (3.67s)
  ✅ Atualização de alertas      (4.33s)
  ✅ Ações nos alertas           (8.90s)
  ✅ Ações em lote               (6.78s)  
  ✅ Operações inválidas         (2.20s)

🎯 Resultado geral: ✅ SUCESSO
```

## Limpeza Automática

O teste inclui uma função `cleanup()` que remove automaticamente todos os alertas criados durante os testes, evitando poluição da base de dados.

## Solução de Problemas

### Erro de Autenticação
- Verifique se as credenciais em `TEST_CREDENTIALS` estão corretas
- Certifique-se que o usuário tem permissão ADMIN ou MONITOR

### Erro de Conexão
- Verifique se a API está rodando em `http://localhost:8000`
- Teste manualmente: `curl http://localhost:8000/docs`

### Falhas nos Testes
- Verifique os logs detalhados de cada teste
- Confirme se todas as dependências estão instaladas
- Verifique se as migrações do banco foram aplicadas

### Módulo requests não encontrado
```bash
pip install requests
```

## Extensão dos Testes

Para adicionar novos testes:

1. Criar método `test_nova_funcionalidade(self)`
2. Adicionar à lista `tests` em `run_all_tests()`
3. Seguir o padrão de retorno `True/False` e logs detalhados

Exemplo:
```python
def test_nova_funcionalidade(self):
    """Testa nova funcionalidade"""
    print("\n🆕 Testando nova funcionalidade...")
    
    try:
        # Lógica do teste
        response = self.session.get(f"{ALERTS_ENDPOINT}/new-endpoint")
        
        if response.status_code == 200:
            print("✅ Nova funcionalidade funcionando")
            return True
        else:
            print(f"❌ Falha: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
```

Este conjunto de testes garante que toda a API de alertas está funcionando corretamente e pode ser executado continuamente durante o desenvolvimento.
