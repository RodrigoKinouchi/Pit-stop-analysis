# 🚀 Configuração do Streamlit Cloud

## 📋 Como definir a página principal

### Problema
O Streamlit Cloud estava usando `pt_v3.py` como página principal ao invés de `main.py`.

### Solução

1. **Remover `pt_v3.py` do Git** ✅ (já feito)
   ```bash
   git rm --cached backup/pt_v3.py
   ```

2. **Adicionar `backup/` ao `.gitignore`** ✅ (já feito)

3. **Fazer commit e push:**
   ```bash
   git add .
   git commit -m "Fix: Definir main.py como página principal e remover pt_v3.py"
   git push
   ```

4. **No Streamlit Cloud:**
   - Vá em **Settings** → **General**
   - Verifique se o **Main file path** está como `main.py`
   - Se não estiver, altere para `main.py`
   - Salve as alterações

5. **Limpar cache do Streamlit Cloud:**
   - Vá em **Settings** → **Advanced settings**
   - Clique em **Clear cache and redeploy**
   - Ou faça um novo deploy

## ✅ Verificação

Após fazer o commit e push, o Streamlit Cloud deve:
- ✅ Usar `main.py` como página principal
- ✅ Mostrar o logo Amattheis na página inicial
- ✅ Ter as páginas corretas no menu lateral

## 📝 Nota

Se ainda aparecer `pt_v3.py` após o commit:
1. Verifique se o arquivo foi removido do Git
2. Limpe o cache do Streamlit Cloud
3. Faça um novo deploy

