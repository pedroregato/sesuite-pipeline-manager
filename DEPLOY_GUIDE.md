# 🚀 Guia de Deploy — Business Modeling Studio no Streamlit Community Cloud

---

## Estrutura final de arquivos

```
business-modeling-studio/        ← pasta raiz do projeto
│
├── app.py                        ← aplicação principal
├── auth.py                       ← módulo de autenticação
├── requirements.txt              ← dependências Python
├── .gitignore                    ← protege secrets.toml
│
└── .streamlit/
    ├── secrets.toml              ← ⚠️ NÃO vai pro Git (está no .gitignore)
    └── config.toml               ← (opcional) tema visual
```

---

## PASSO 1 — Instalar o Git (se não tiver)

Acesse https://git-scm.com/downloads e instale.

Verifique: `git --version`

---

## PASSO 2 — Criar conta no GitHub

1. Acesse https://github.com
2. Clique em **Sign up** → crie sua conta gratuita
3. Confirme o e-mail

---

## PASSO 3 — Criar o repositório no GitHub

1. No GitHub, clique em **+** (canto superior direito) → **New repository**
2. Preencha:
   - **Repository name:** `business-modeling-studio`
   - **Visibility:** ✅ **Private** (recomendado — protege o código)
   - **Description:** Business Modeling Studio — BMM, BPMN, SBVR, DMN
3. Clique em **Create repository**

---

## PASSO 4 — Preparar os arquivos localmente

Abra o terminal na pasta onde estão os arquivos e execute:

```bash
# Entre na pasta do projeto (ajuste o caminho)
cd ~/Downloads/business-modeling-studio

# Inicialize o repositório Git
git init

# Configure seu nome e e-mail (primeira vez)
git config --global user.name  "Seu Nome"
git config --global user.email "seu@email.com"

# Adicione todos os arquivos (exceto os do .gitignore)
git add app.py auth.py requirements.txt .gitignore

# Faça o primeiro commit
git commit -m "feat: Business Modeling Studio com autenticação"

# Conecte ao repositório remoto (substitua SEU_USUARIO pelo seu login do GitHub)
git remote add origin https://github.com/SEU_USUARIO/business-modeling-studio.git

# Envie o código
git push -u origin main
```

> 💡 O GitHub pode pedir seu usuário e senha. Use um **Personal Access Token**
> (GitHub → Settings → Developer settings → Personal access tokens → Tokens classic)

---

## PASSO 5 — Criar conta no Streamlit Community Cloud

1. Acesse https://share.streamlit.io
2. Clique em **Sign up** → escolha **Continue with GitHub**
3. Autorize o Streamlit a acessar seus repositórios

---

## PASSO 6 — Fazer o deploy do app

1. Em https://share.streamlit.io, clique em **New app**
2. Preencha:
   - **Repository:** `SEU_USUARIO/business-modeling-studio`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Clique em **Deploy!**

O Streamlit vai instalar as dependências do `requirements.txt` automaticamente.
Em ~1 minuto o app estará no ar em uma URL como:
```
https://SEU_USUARIO-business-modeling-studio-app-XXXX.streamlit.app
```

---

## PASSO 7 — Configurar os Secrets (senhas dos usuários)

Este é o passo mais importante para a segurança.

1. No painel do seu app em share.streamlit.io, clique nos **três pontos** (⋮) → **Settings**
2. Clique na aba **Secrets**
3. Cole o conteúdo abaixo (substituindo os hashes reais):

```toml
AUTH_SALT = "troque_por_valor_secreto_unico_aqui"

[users]

  [users.admin]
  name          = "Administrador"
  password_hash = "HASH_DA_SENHA_ADMIN"
  role          = "admin"
  email         = "admin@suaempresa.com"

  [users.colaborador]
  name          = "Nome do Colaborador"
  password_hash = "HASH_DA_SENHA_DELE"
  role          = "editor"
  email         = "colaborador@suaempresa.com"
```

### Como gerar o password_hash?

Execute no terminal Python:

```python
import hashlib

salt = "troque_por_valor_secreto_unico_aqui"   # mesmo valor do AUTH_SALT

# Gere um hash para cada usuário
senha = "SenhaDoUsuario@2025"
print(hashlib.sha256(f"{salt}{senha}".encode()).hexdigest())
```

Cole o resultado longo (64 caracteres) no campo `password_hash` do secrets.

4. Clique em **Save** → o app reiniciará automaticamente com as novas credenciais

---

## PASSO 8 — (Opcional) Restringir quem pode ACESSAR a URL

Por padrão, qualquer pessoa com a URL pode ver a tela de login.
Para impedir isso completamente:

1. Em Settings → **Sharing**
2. Ative **"Only specific people can view this app"**
3. Adicione os e-mails autorizados

Assim, o Streamlit exige login com conta Google/GitHub antes mesmo de mostrar a tela de login do app.

---

## PASSO 9 — Atualizar o app no futuro

Sempre que quiser atualizar o código:

```bash
# Edite os arquivos localmente, depois:
git add .
git commit -m "fix: descrição da mudança"
git push
```

O Streamlit Community Cloud detecta o push e reinicia o app automaticamente em ~30 segundos.

---

## Resumo de Segurança

| Camada | Proteção |
|---|---|
| Repositório **privado** | Código não visível ao público |
| **`.gitignore`** para `secrets.toml` | Senhas nunca vão ao GitHub |
| **Secrets** no painel Streamlit | Senhas injetadas em ambiente seguro |
| **Hash SHA-256** das senhas | Senhas nunca ficam em texto puro |
| **Bloqueio por tentativas** | Proteção contra força bruta (5 tentativas → bloqueio 5 min) |
| **Viewer authentication** (opcional) | Barreira antes mesmo da tela de login |

---

## Papéis de acesso

| Papel | Visualizar | Editar | Deletar | Exportar |
|---|---|---|---|---|
| `admin` | ✅ | ✅ | ✅ | ✅ |
| `editor` | ✅ | ✅ | ❌ | ✅ |
| `viewer` | ✅ | ❌ | ❌ | ✅ |

---

*Business Modeling Studio · Bridgeland & Zahavi (2009) · OMG Standards*
