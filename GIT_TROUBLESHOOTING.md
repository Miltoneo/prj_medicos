# 🔧 Guia de Resolução de Problemas Git

## Problema: "Please make sure you have the correct access rights and the repository exists"

### 🔍 Diagnóstico

1. **Verificar status do repositório:**
```bash
cd f:\Projects\Django\prj_medicos
git status
```

2. **Verificar repositórios remotos:**
```bash
git remote -v
```

3. **Verificar configuração:**
```bash
git config --list
```

### 🛠️ Soluções Possíveis

#### 1. **Configurar usuário Git (se não estiver configurado):**
```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@exemplo.com"
```

#### 2. **Se não há repositório remoto configurado:**
```bash
# Adicionar origem remota (GitHub, GitLab, etc.)
git remote add origin https://github.com/seuusuario/prj_medicos.git

# Ou SSH (se configurado)
git remote add origin git@github.com:seuusuario/prj_medicos.git
```

#### 3. **Se o repositório remoto não existe, criar primeiro:**
- No GitHub: Criar novo repositório em https://github.com/new
- No GitLab: Criar novo projeto
- Ou usar Git local apenas

#### 4. **Fazer commit inicial e push:**
```bash
# Adicionar arquivos
git add .

# Fazer commit
git commit -m "Initial commit: Sistema Médicos SaaS"

# Enviar para repositório remoto
git push -u origin main
```

#### 5. **Se houver problemas de autenticação:**

**Para HTTPS:**
```bash
# Usar token pessoal em vez de senha
git config --global credential.helper manager-core
```

**Para SSH:**
```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu.email@exemplo.com"

# Adicionar ao ssh-agent
ssh-add ~/.ssh/id_ed25519

# Adicionar chave pública ao GitHub/GitLab
```

#### 6. **Se o repositório está corrompido:**
```bash
# Verificar integridade
git fsck

# Reparar se necessário
git gc --prune=now
```

### 📋 Checklist de Verificação

- [ ] Git está instalado: `git --version`
- [ ] Usuário configurado: `git config user.name`
- [ ] Email configurado: `git config user.email`
- [ ] Repositório remoto existe e está acessível
- [ ] Permissões de acesso corretas (SSH keys ou token)
- [ ] Repositório local não está corrompido

### 🚀 Workflow Recomendado

1. **Primeiro uso:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <URL_DO_REPOSITORIO>
git push -u origin main
```

2. **Uso normal:**
```bash
git add .
git commit -m "Descrição das mudanças"
git push
```

### 🔐 Configuração de Autenticação

#### GitHub (Token Pessoal):
1. GitHub → Settings → Developer Settings → Personal Access Tokens
2. Generate new token (classic)
3. Selecionar scopes: repo, workflow
4. Usar token como senha

#### SSH:
1. Gerar chave: `ssh-keygen -t ed25519 -C "email@exemplo.com"`
2. Adicionar ao GitHub/GitLab: Settings → SSH Keys
3. Usar URL SSH: `git@github.com:usuario/repo.git`

### 📞 Comandos de Emergência

**Reset completo (cuidado!):**
```bash
git reset --hard HEAD
git clean -fd
```

**Reverter último commit:**
```bash
git revert HEAD
```

**Ver histórico:**
```bash
git log --oneline
```
