# 🏁 Pit Stop Report - Stock Car

Aplicativo web desenvolvido com Python e Streamlit para visualização e análise de dados de pit stops do campeonato Stock Car no Brasil.

## 📋 Descrição

Este aplicativo permite visualizar e gerar insights de dados coletados dos procedimentos obrigatórios (pit stops) do campeonato Stock Car. O sistema foi desenvolvido para facilitar a análise de dados de múltiplas temporadas.

## 🚀 Funcionalidades

- **Visualização por Temporada**: Dados separados por temporada (2024, 2025, etc.)
- **Inserção de Dados**: Interface para inserir dados de pit stops diretamente no app
- **Overview**: Visualização geral dos dados de pit stops
- **Análise Mattheis**: Análise detalhada do grupo Mattheis
- **Análise de Pilotos**: Análise comparativa de pilotos ao longo das temporadas
- **Análise de Times**: Análise comparativa de times
- **Integração com Google Sheets**: Persistência de dados na nuvem (opcional)

## 📁 Estrutura do Projeto

```
PITSTOPapp/
├── main.py                 # Página principal/home
├── pages/                  # Páginas das temporadas
│   ├── temporada_2024.py  # Página da temporada 2024
│   ├── temporada_2025.py  # Página da temporada 2025
│   └── inserir_dados.py   # Página para inserir dados
├── utils/                  # Módulos utilitários
│   ├── __init__.py
│   ├── constants.py       # Constantes e dicionários
│   ├── data_loader.py     # Funções de carregamento de dados
│   ├── google_sheets.py   # Integração com Google Sheets
│   ├── season_2025.py     # Funções auxiliares temporada 2025
│   └── visualizations.py  # Funções de visualização
├── images/                 # Imagens dos circuitos e capa
├── .streamlit/            # Configurações do Streamlit
│   └── config.toml        # Tema dark e outras configurações
├── PITSTOP.xlsx           # Arquivo Excel com dados principais
├── Mattheis.xlsx          # Arquivo Excel com dados do grupo Mattheis
├── GOOGLE_SHEETS_SETUP.md # Instruções para configurar Google Sheets
└── requirements.txt       # Dependências do projeto
```

## 🛠️ Instalação

1. Clone o repositório ou navegue até a pasta do projeto

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## ▶️ Como Executar

Execute o aplicativo Streamlit:
```bash
streamlit run main.py
```

O aplicativo será aberto automaticamente no seu navegador padrão.

## 📊 Como Usar

1. **Página Principal (main.py)**: 
   - Mostra informações sobre o aplicativo
   - Permite navegação para as temporadas disponíveis

2. **Páginas de Temporada**:
   - Selecione uma corrida no menu dropdown (nomes formatados: "Corrida X - Tipo Etapa Y")
   - Explore as diferentes abas:
     - **Overview**: Visualização geral dos dados
     - **Mattheis**: Análise específica do grupo Mattheis
     - **Driver analysis**: Análise comparativa de pilotos
     - **Team analysis**: Análise comparativa de times

3. **Página Inserir Dados**:
   - Selecione temporada e corrida
   - Preencha dados de cada piloto
   - Salve diretamente no Excel ou Google Sheets
   - Suporte para modo individual ou upload de planilha

## ⚙️ Configuração de Temporadas

O aplicativo tenta identificar automaticamente quais abas do Excel pertencem a cada temporada. Se necessário, você pode ajustar o mapeamento manualmente:

### Para Temporada 2024
Edite o arquivo `pages/temporada_2024.py` e ajuste o mapeamento na seção:

```python
season_2024_mapping = {
    2024: [lista_de_abas_2024]
}
```

### Para Temporada 2025
Edite o arquivo `pages/temporada_2025.py` e ajuste o mapeamento na seção:

```python
season_2025_mapping = {
    2025: [lista_de_abas_2025]
}
```

## 📝 Notas

- O aplicativo assume que as abas do Excel seguem um padrão de nomenclatura (ex: E1, E1S, E2, E2S, etc.)
- Se as abas não contêm o ano explicitamente no nome, o sistema tenta inferir pela ordem das abas
- Você pode ajustar o mapeamento manualmente conforme necessário

## 🔧 Dependências Principais

- streamlit
- pandas
- plotly
- openpyxl
- pillow
- gspread (para Google Sheets - opcional)
- google-auth (para Google Sheets - opcional)

## 📊 Fluxo de Dados

### Opção 1: Excel Local (Padrão)
- Dados salvos localmente em arquivos Excel
- Requer commit/push para atualizar no Streamlit Cloud
- Ideal para desenvolvimento local

### Opção 2: Google Sheets (Recomendado para Produção)
- Dados salvos diretamente no Google Sheets
- Persistência automática na nuvem
- Funciona perfeitamente no Streamlit Cloud
- **Veja `GOOGLE_SHEETS_SETUP.md` para instruções de configuração**

## ⚙️ Configuração do Google Sheets

Para usar Google Sheets em vez de Excel local:

1. **Siga as instruções em `GOOGLE_SHEETS_SETUP.md`**
2. **Configure as credenciais** no Streamlit Secrets
3. **O sistema detectará automaticamente** e usará Google Sheets

**Nota**: Se Google Sheets não estiver configurado, o sistema usa Excel local automaticamente.

## 📄 Licença

Este projeto foi desenvolvido para uso interno do campeonato Stock Car.

## 👤 Autor

Amattheis

