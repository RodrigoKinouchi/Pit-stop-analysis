# 📋 Fluxo de Dados - Pit Stop Report

## 🔄 Como o Sistema Funciona

### 1. **Contexto do Streamlit Cloud**

O Streamlit Cloud é uma plataforma que hospeda aplicações Streamlit. Quando você faz deploy de uma aplicação:

- O código é executado no servidor do Streamlit Cloud
- Os arquivos de dados (Excel, CSV, etc.) ficam no servidor
- Quando um usuário salva dados, eles são salvos no servidor **temporariamente**

### 2. **Fluxo Atual de Dados**

#### **Opção 1: Desenvolvimento Local**
```
Usuário (Estagiário) → Inserir Dados no App → Salvar no Excel Local
→ Arquivo Excel local é atualizado → Commit no Git → Push para GitHub
→ Streamlit Cloud detecta mudanças → Re-deploy automático
```

#### **Opção 2: Streamlit Cloud (Deploy)**
```
Usuário → Inserir Dados → Salvar no Excel (no servidor)
→ Arquivo Excel no servidor é atualizado TEMPORARIAMENTE
→ ⚠️ ATENÇÃO: Mudanças podem ser perdidas se o app reiniciar!
```

### 3. **Problema Atual**

❌ **O Streamlit Cloud não persiste arquivos entre sessões!**

Quando você salva um arquivo Excel no Streamlit Cloud:
- O arquivo é salvo no sistema de arquivos temporário do servidor
- Se o app reiniciar (por timeout, erro, ou re-deploy), os dados são perdidos
- O Streamlit Cloud não é um banco de dados persistente

### 4. **Soluções Recomendadas**

#### **Solução A: Banco de Dados (Recomendado para Produção)**

Use um banco de dados para persistir dados:
- **Google Sheets API** (gratuito, fácil)
- **Firebase / Firestore** (gratuito até certo limite)
- **PostgreSQL** (via Heroku, Supabase, etc.)
- **SQLite** (simples, mas limitado no Cloud)

#### **Solução B: Git Integration (Atual - Melhorado)**

Melhorar o fluxo atual:
1. Usuário insere dados no app
2. App salva no Excel local
3. **Automático ou manual**: Commit e push para GitHub
4. Streamlit Cloud re-deploys automaticamente

**Como implementar:**
```python
# Após salvar, oferecer opção de fazer commit automático
if st.button("💾 Salvar e Fazer Commit"):
    # 1. Salvar no Excel
    # 2. Executar git add, commit, push
    # 3. Notificar usuário
```

#### **Solução C: Download/Upload Manual**

1. Usuário insere dados
2. App oferece download do Excel atualizado
3. Usuário faz upload manualmente depois
4. Ou você baixa e faz commit manualmente

### 5. **Como Funciona Agora (Corrigido)**

#### **Passo a Passo:**

1. **Estagiário acessa o app** (local ou Cloud)

2. **Vai na página "Inserir Dados"**

3. **Preenche os dados** de uma corrida:
   - Seleciona temporada e corrida
   - Preenche dados de cada piloto
   - Adiciona dados específicos do Mattheis (se aplicável)

4. **Clica em "Salvar no Excel"**:
   - ✅ O arquivo `PITSTOP.xlsx` é atualizado localmente
   - ✅ O arquivo `Mattheis.xlsx` é atualizado (se houver dados Mattheis)
   - ✅ Mensagem de sucesso é exibida

5. **Para atualizar no Streamlit Cloud:**

   **Opção Manual:**
   ```bash
   # No terminal local
   git add PITSTOP.xlsx Mattheis.xlsx
   git commit -m "Atualização de dados - Etapa X"
   git push origin main
   ```
   
   **Opção Automática (Futuro):**
   - Implementar botão "Salvar e Fazer Commit"
   - Usar biblioteca `GitPython` para automatizar

### 6. **Recomendações**

✅ **Para Desenvolvimento Local:**
- Funciona perfeitamente como está
- Dados são salvos localmente
- Você controla quando fazer commit/push

✅ **Para Produção (Streamlit Cloud):**
- **Curto prazo:** Usar solução B (Git Integration melhorada)
- **Longo prazo:** Migrar para banco de dados (Solução A)

### 7. **Próximos Passos Sugeridos**

1. ✅ **Corrigido:** Método de salvamento (usando openpyxl diretamente)
2. 🔄 **Pendente:** Adicionar botão "Salvar e Fazer Commit" (opcional)
3. 🔄 **Futuro:** Migrar para banco de dados (Google Sheets ou Firebase)

---

## 📝 Nota Importante

**O código atual salva os arquivos Excel localmente.** 

Se você está rodando localmente:
- ✅ Os arquivos são salvos na pasta do projeto
- ✅ Você pode fazer commit e push quando quiser

Se você está rodando no Streamlit Cloud:
- ⚠️ Os arquivos são salvos temporariamente no servidor
- ⚠️ Você precisa fazer commit/push manualmente para persistir
- 💡 Recomendamos usar banco de dados para produção

---

**Dúvidas?** Entre em contato ou abra uma issue no repositório!

