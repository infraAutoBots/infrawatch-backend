# infrawatch-backend

Este projeto é o backend do **InfraWatch**, uma solução desenvolvida para monitoramento de infraestrutura, coleta de métricas e disponibilização de uma API RESTful para integração com outros sistemas. O backend é construído em Python e utiliza pacotes modernos para facilitar a manutenção, extensibilidade e confiabilidade do sistema.

## Sobre o Projeto

O **InfraWatch-backend** tem como objetivos principais:

- Coletar e armazenar métricas e logs de diversos servidores e serviços.
- Fornecer uma API para consulta, análise e integração dos dados monitorados.
- Facilitar o monitoramento ativo de infraestrutura com notificações e alertas.
- Escalabilidade e facilidade de integração com outros sistemas e dashboards.

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

## Como rodar a API

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