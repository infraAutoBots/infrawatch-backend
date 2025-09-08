# infrawatch-backend

Este projeto é o backend do **InfraWatch**, uma solução desenvolvida para monitoramento de infraestrutura, coleta de métricas e disponibilização de uma API RESTful para integração com outros sistemas. O backend é construído em Python e utiliza pacotes modernos para facilitar a manutenção, extensibilidade e confiabilidade do sistema.

## Sobre o Projeto

O **InfraWatch-backend** tem como objetivos principais:

- Coletar e armazenar métricas e logs de diversos servidores e serviços.
- Fornecer uma API para consulta, análise e integração dos dados monitorados.
- Facilitar o monitoramento ativo de infraestrutura com notificações e alertas.
- Escalabilidade e facilidade de integração com outros sistemas e dashboards.

## Verção do python
```bash
Python 3.12.3
```

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/infraAutoBots/infrawatch-backend.git
cd infrawatch-backend
```

### 2. Crie e ative um ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale as dependências do projeto

```bash
pip install -r requirements.txt
```

> **Nota:** Certifique-se de ter o Python 3.8+ instalado.

## Configuração

Edite o arquivo `.env` (ou `config.py`, caso exista) para configurar variáveis de ambiente como conexão ao banco de dados, portas, etc. Consulte os exemplos fornecidos no repositório.

## Configuração do PostgreSQL

**IMPORTANTE:** Antes de executar a API, certifique-se de que o PostgreSQL esteja instalado e funcionando.

### 1. Verificar se o PostgreSQL está rodando

```bash
sudo systemctl status postgresql
```

### 2. Iniciar o PostgreSQL (caso não esteja rodando)

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3. Verificar se o banco e usuário existem

```bash
# Conectar como superusuário
sudo -u postgres psql

# Listar bancos de dados
\l

# Listar usuários
\du

# Sair do PostgreSQL
\q
```

### 4. Criar banco e usuário (se necessário)

```bash
# Conectar como postgres
sudo -u postgres psql

# Criar banco de dados
CREATE DATABASE infrawatch_db;

# Criar usuário
CREATE USER infrawatch WITH PASSWORD 'sua_senha_aqui';

# Dar permissões ao usuário
GRANT ALL PRIVILEGES ON DATABASE infrawatch_db TO infrawatch;

# Sair
\q
```

### 5. Testar conexão

```bash
# Testar se consegue conectar com o usuário criado
psql -h localhost -U infrawatch -d infrawatch_db -c "SELECT current_user, current_database();"
```

### 6. Resolver problemas de autenticação (se necessário)

Se ocorrer erro de autenticação, edite o arquivo de configuração:

```bash
# Editar configuração de autenticação
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Alterar 'peer' para 'md5' nas linhas:
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### 7. Verificação rápida antes de executar a API

```bash
# Comando rápido para verificar se tudo está funcionando
sudo systemctl status postgresql && echo "✅ PostgreSQL está rodando"

# Verificar se consegue conectar (irá pedir senha)
psql -h localhost -U infrawatch -d infrawatch_db -c "SELECT 'Conexão OK' as status;"
```

## Como rodar a API

**⚠️ ATENÇÃO:** Antes de executar a API, certifique-se de que o PostgreSQL esteja rodando e configurado conforme a seção anterior.

Para iniciar a API, utilize o comando:

```bash
python app.py
```

Ou, se estiver utilizando frameworks como FastAPI/Flask/Uvicorn, utilize:

```bash
uvicorn app:app --reload  # FastAPI
# ou
flask run  # Flask
```

A API estará disponível, por padrão, em `http://localhost:8000` ou `http://localhost:5000`, dependendo da configuração/framework.

## Como rodar o Monitoramento

O serviço de monitoramento pode ser executado via script específico ou comando no console. Exemplo:

```bash
python monitor.py
```

Ou, caso utilize um gerenciador de processos (como systemd, Supervisor ou Docker), configure o serviço conforme a documentação.

### Executando Tudo em Ambiente de Desenvolvimento

Para desenvolvimento local, você pode rodar a API e o monitoramento simultaneamente em dois terminais:

```bash
# Terminal 1: API
python app.py

# Terminal 2: Monitoramento
python monitor.py
```

## Testes

Execute os testes (caso existam) com:

```bash
pytest
```

## Contribuição

Contribuições são bem-vindas! Abra uma issue ou envie um pull request com suas sugestões, melhorias ou correções.

## Licença

Consulte o arquivo LICENSE para mais detalhes.

---

**InfraWatch-backend** — Monitorando o seu ambiente, facilitando a sua gestão!