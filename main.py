"""
Página principal do aplicativo Pit Stop Report
Permite seleção de temporada para navegação
"""

import streamlit as st
from PIL import Image
from utils.constants import COVER_IMAGE, AMATTHEIS_LOGO, CAR_IMAGE

# Configurando o título da página
st.set_page_config(
    page_title="Pit Stop Report",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar CSS para carro de fundo transparente no canto inferior direito
try:
    import base64
    import os
    from utils.constants import CAR_IMAGE
    if os.path.exists(CAR_IMAGE):
        with open(CAR_IMAGE, "rb") as img_file:
            car_image_base64 = base64.b64encode(img_file.read()).decode()
        st.markdown(f"""
        <style>
            .car-background {{
                position: fixed;
                bottom: 0;
                right: 0;
                width: 400px;
                height: 250px;
                opacity: 0.2;
                z-index: -1;
                pointer-events: none;
                background-image: url('data:image/png;base64,{car_image_base64}');
                background-size: contain;
                background-repeat: no-repeat;
                background-position: bottom right;
            }}
            @media (max-width: 768px) {{
                .car-background {{
                    width: 250px;
                    height: 180px;
                    opacity: 0.15;
                }}
            }}
        </style>
        <div class="car-background"></div>
        """, unsafe_allow_html=True)
except Exception:
    pass

# Logo da equipe Amattheis como capa
try:
    logo_img = Image.open(AMATTHEIS_LOGO)
    st.image(logo_img, use_container_width=True)
except Exception as e:
    # Fallback para imagem de capa original
    try:
        image = Image.open(COVER_IMAGE)
        st.image(image, use_container_width=True)
    except:
        st.warning(f"Imagem de capa não encontrada: {e}")

st.write("<div align='center'><h2><i>PIT STOP report by: Amattheis</i></h2></div>",
         unsafe_allow_html=True)
st.write("")

# Informação sobre o aplicativo
st.markdown("""
### Bem-vindo ao Pit Stop Report! 🏁

Este aplicativo permite visualizar e analisar dados de pit stops do campeonato Stock Car.

**Selecione uma temporada no menu lateral** para começar a explorar os dados.

#### Funcionalidades:
- 📊 **Overview**: Visualização geral dos dados de pit stops
- 🏎️ **Mattheis**: Análise detalhada do grupo Mattheis
- 👤 **Driver Analysis**: Análise comparativa de pilotos
- 🏆 **Team Analysis**: Análise comparativa de times

**Use o menu lateral** para navegar entre as temporadas disponíveis.
""")

# Menu lateral para seleção de temporada
st.sidebar.title("🎯 Navegação")
st.sidebar.markdown("---")

st.sidebar.markdown("### 📅 Temporadas Disponíveis")

# Links para as temporadas (usando páginas do Streamlit)
st.sidebar.markdown("""
### 📊 Navegação por Temporada

Use os links abaixo para acessar as páginas das temporadas:

- [🏁 Temporada 2024](temporada_2024)
- [🏁 Temporada 2025](temporada_2025)
- [📝 Entrada de dados 2026 (SQLite)](entrada_2026)
""")
st.sidebar.markdown("""
**Ou use o menu lateral** para navegar diretamente entre as páginas.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Nota:** As páginas de temporada permitem:
- Seleção de corridas específicas
- Visualização de dados detalhados
- Análises comparativas
""")
