# 🔑 Como Atualizar Credenciais do Railway

## ❌ Problema Atual
```
psycopg2.OperationalError: password authentication failed for user "postgres"
```

Isso significa que a senha do PostgreSQL no arquivo `.env` está **desatualizada** ou **incorreta**.

---

## ✅ Solução: Atualizar Credenciais

### 📋 Passo 1: Obter Credenciais do Railway

1. Acesse: https://railway.app/
2. Faça login
3. Selecione o projeto **infrawatch**
4. Clique no serviço **PostgreSQL** (ícone de elefante 🐘)
5. Vá na aba **Variables**
6. Copie as seguintes variáveis:

```bash
DATABASE_URL=postgresql://postgres:SENHA_AQUI@postgres.railway.internal:5432/railway
DATABASE_PUBLIC_URL=postgresql://postgres:SENHA_AQUI@HOST.proxy.rlwy.net:PORTA/railway
PGPASSWORD=SENHA_AQUI
POSTGRES_PASSWORD=SENHA_AQUI
```

---

### 📝 Passo 2: Atualizar o Arquivo `.env`

Abra o arquivo `/home/ubuntu/Code/infrawatch/infrawatch-backend/.env` e atualize **TODAS** as linhas com a **MESMA SENHA**:

```bash
# Linha 30 - DATABASE_PUBLIC_URL
DATABASE_PUBLIC_URL=postgresql://postgres:NOVA_SENHA@gondola.proxy.rlwy.net:51468/railway

# Linha 31 - DATABASE_URL
DATABASE_URL=postgresql://postgres:NOVA_SENHA@postgres.railway.internal:5432/railway

# Linha 35 - PGPASSWORD
PGPASSWORD=NOVA_SENHA

# Linha 38 - POSTGRES_PASSWORD
POSTGRES_PASSWORD=NOVA_SENHA
```

---

### 🚀 Passo 3: Fazer Deploy

Depois de atualizar o `.env`:

```bash
# Fazer commit das alterações
git add .env
git commit -m "chore: update Railway PostgreSQL credentials"
git push origin main
```

**⚠️ IMPORTANTE:** O `.env` deve estar configurado para ser lido pelo Railway, ou você deve definir as variáveis diretamente no dashboard do Railway.

---

## 🔍 Alternativa: Usar Variáveis de Ambiente do Railway

**Melhor prática (recomendado):**

1. No Railway Dashboard
2. Vá em **Settings** do serviço backend
3. Clique em **Variables**
4. Adicione/atualize:
   - `DATABASE_URL`
   - `DATABASE_PUBLIC_URL`
   - `PGPASSWORD`
   - `POSTGRES_PASSWORD`

Isso é mais seguro que manter as credenciais no código!

---

## 🧪 Passo 4: Testar Conexão

Após atualizar, teste a conexão:

```bash
python -c "from api.models import db; print('✅ Conexão bem-sucedida!')"
```

---

## 📞 Precisa de Ajuda?

Se ainda tiver problemas:
1. Verifique se a senha não tem caracteres especiais que precisam ser encodados
2. Confirme que o serviço PostgreSQL está ativo no Railway
3. Verifique os logs do Railway para mais detalhes

---

**Data de criação:** 6 de outubro de 2025
