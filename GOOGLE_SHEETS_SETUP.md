# 📊 Configuração do Google Sheets - Pit Stop Report

## 🎯 Por que usar Google Sheets?

✅ **Persistência de dados** - Dados salvos na nuvem, não se perdem  
✅ **Acesso em tempo real** - Múltiplos usuários podem acessar simultaneamente  
✅ **Sincronização automática** - Mudanças aparecem imediatamente  
✅ **Backup automático** - Google mantém histórico de versões  
✅ **Funciona no Streamlit Cloud** - Sem necessidade de commit/push  

## 📋 Pré-requisitos

1. Conta Google (Gmail)
2. Acesso ao Google Cloud Console
3. Python 3.7+

## 🚀 Passo a Passo - Configuração

### 1. Criar Projeto no Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Crie um novo projeto ou selecione um existente
3. Anote o **ID do Projeto**

### 2. Habilitar Google Sheets API

1. No Google Cloud Console, vá em **APIs & Services** > **Library**
2. Procure por **"Google Sheets API"**
3. Clique em **Enable** (Ativar)
4. Procure por **"Google Drive API"** e também ative

### 3. Criar Credenciais (Service Account)

1. Vá em **APIs & Services** > **Credentials**
2. Clique em **Create Credentials** > **Service Account**
3. Preencha:
   - **Name**: `pitstop-app` (ou qualquer nome)
   - **Description**: `Service account para Pit Stop Report`
4. Clique em **Create and Continue**
5. Em **Role**, selecione **Editor** (ou deixe sem role por enquanto)
6. Clique em **Done**

### 4. Gerar Chave JSON

1. Na lista de Service Accounts, clique no que você criou
2. Vá na aba **Keys**
3. Clique em **Add Key** > **Create new key**
4. Selecione **JSON**
5. Clique em **Create**
6. Um arquivo JSON será baixado - **GUARDE ESTE ARQUIVO COM SEGURANÇA!**

### 5. Criar Planilhas no Google Sheets

1. Acesse: https://sheets.google.com/
2. Crie uma nova planilha chamada **"PITSTOP"**
3. Anote o **ID da planilha** (está na URL): 1GDsLICxqRN_Sp4xY_CMQAviT7h4T3-MS41ud9ym3844/edit?gid=0#gid=0
   ```
   https://docs.google.com/spreadsheets/d/ID_DA_PLANILHA/edit
                                ↑ Esta parte é o ID
   ```
4. Crie outra planilha chamada **"Mattheis"**
5. Anote o ID desta também
1dEMDePVYxdzQwO31icmGI2WSG8g80mg0tptL71QXrP4/edit?gid=0#gid=0

### 6. Compartilhar Planilhas com Service Account

1. Abra cada planilha (PITSTOP e Mattheis)
2. Clique em **Share** (Compartilhar)
3. No campo de email, cole o **email do Service Account** (está no arquivo JSON baixado)
   - Procure por `"client_email"` no arquivo JSON
   - Exemplo: `pitstop-app@seu-projeto.iam.gserviceaccount.com`
4. Dê permissão de **Editor**
5. Clique em **Send** (mas não precisa enviar, apenas compartilhar)

### 7. Configurar no Streamlit

#### Opção A: Streamlit Secrets (Recomendado para Streamlit Cloud)

1. No Streamlit Cloud, vá em **Settings** > **Secrets**
2. Adicione o seguinte JSON:

```toml
GOOGLE_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "seu-projeto-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "pitstop-app@seu-projeto.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''

GOOGLE_SHEETS_PITSTOP_ID = "ID_DA_PLANILHA_PITSTOP"
GOOGLE_SHEETS_MATTHEIS_ID = "ID_DA_PLANILHA_MATTHEIS"
USE_GOOGLE_SHEETS = true
```

3. Cole o conteúdo completo do arquivo JSON baixado no campo `GOOGLE_CREDENTIALS`
4. Cole os IDs das planilhas
5. Salve

#### Opção B: Arquivo Local (Para desenvolvimento)

1. Copie o arquivo JSON baixado para a pasta do projeto
2. Renomeie para `credentials.json`
3. No arquivo `.gitignore`, adicione:
   ```
   credentials.json
   ```
4. Edite `utils/constants.py` e configure:
   ```python
   USE_GOOGLE_SHEETS = True
   GOOGLE_SHEETS_PITSTOP_ID = "seu-id-aqui"
   GOOGLE_SHEETS_MATTHEIS_ID = "seu-id-aqui"
   ```

### 8. Ativar no Código

Edite `utils/constants.py`:

```python
# Flag para usar Google Sheets (True) ou Excel local (False)
USE_GOOGLE_SHEETS = True  # Mudar para True quando configurar
```

**OU** configure via Streamlit Secrets (recomendado).

## ✅ Verificação

1. Execute o app: `streamlit run main.py`
2. Vá na página "Inserir Dados"
3. Preencha alguns dados de teste
4. Clique em "Salvar no Google Sheets"
5. Verifique se os dados aparecem na planilha do Google Sheets

## 🔒 Segurança

⚠️ **IMPORTANTE:**
- **NUNCA** commite o arquivo `credentials.json` no Git
- Use `.gitignore` para proteger credenciais
- No Streamlit Cloud, use **Secrets** (mais seguro)
- O Service Account deve ter apenas permissões necessárias

## 🐛 Troubleshooting

### Erro: "Permission denied"
- Verifique se compartilhou a planilha com o email do Service Account
- Verifique se deu permissão de **Editor**

### Erro: "API not enabled"
- Verifique se ativou Google Sheets API e Google Drive API

### Erro: "Invalid credentials"
- Verifique se o JSON está correto
- Verifique se não há espaços extras no JSON nos Secrets

### Erro: "Worksheet not found"
- O app criará a aba automaticamente se não existir
- Verifique se o Service Account tem permissão de Editor

## 📚 Recursos

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Documentation](https://gspread.readthedocs.io/)
- [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**Dúvidas?** Entre em contato ou abra uma issue no repositório!

