"""
Página da Temporada 2025
Visualização e análise de dados de pit stops da temporada 2025
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image
from utils.constants import (
    get_drivers_names, get_team_info, track_images, 
    cor_por_piloto, mattheis_names_2025, COVER_IMAGE, DEFAULT_TRACK_IMAGE, AMATTHEIS_LOGO,
    get_pilot_color_map, get_amattheis_color_map, CAR_IMAGE, team_colors_2025,
    init_google_sheets_config, AMATTHEIS_NEUTRAL_COLOR
)

from utils.data_loader import load_all_data, load_mattheis_data, filter_sheets_by_season
from utils.season_2025 import (
    get_tipo_corrida_2025, get_track_image_2025, 
    get_nome_corrida_2025, parse_corrida_name, get_nome_aba_formatado
)

def convert_to_numeric(series):
    """Converte uma série para numérico, tratando strings como 'Não registrado' como NaN"""
    return pd.to_numeric(series, errors='coerce')

def render_dataframe_with_optional_style(df, formatter=None, cmap='RdYlGn_r', axis=None, text_align='center'):
    """Renderiza DataFrame com estilo se matplotlib estiver disponível; caso contrário, exibe sem gradiente."""
    try:
        styler = df.style
        if formatter is not None:
            styler = styler.format(formatter)
        styler = styler.background_gradient(cmap=cmap, axis=axis)
        if text_align:
            styler = styler.set_properties(**{'text-align': text_align})
        st.dataframe(styler, use_container_width=True)
    except ImportError:
        st.info("Matplotlib não está disponível neste ambiente. Exibindo tabela sem gradiente de cores.")
        if formatter is not None:
            if callable(formatter):
                df_display = df.applymap(lambda v: formatter(v) if pd.notnull(v) else formatter(float('nan')))
            elif isinstance(formatter, dict):
                df_display = df.copy()
                for col, fmt in formatter.items():
                    if col in df_display.columns:
                        if callable(fmt):
                            df_display[col] = df_display[col].apply(lambda v: fmt(v) if pd.notnull(v) else fmt(float('nan')))
                        else:
                            df_display[col] = df_display[col].apply(lambda v: fmt.format(v) if pd.notnull(v) else "—")
            else:
                df_display = df
        else:
            df_display = df
        st.dataframe(df_display, use_container_width=True)

# Configuração da página - DEVE SER O PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    page_title="Temporada 2025 - Pit Stop Report",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar configurações do Google Sheets (depois do set_page_config)
init_google_sheets_config()

# Adicionar carro como background transparente no canto inferior direito
try:
    import base64
    import os
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
except Exception as e:
    pass

# Logo da equipe Amattheis como capa grande
try:
    from PIL import Image
    logo_img = Image.open(AMATTHEIS_LOGO)
    st.image(logo_img, use_container_width=True)
except Exception:
    pass

st.markdown("<br>", unsafe_allow_html=True)

# Título da temporada
st.title("🏁 Temporada 2025")

# Carregar dados
try:
    dados = load_all_data()
    abas = list(dados.keys())
    
    # Remover abas vazias ou inválidas
    abas = [aba for aba in abas if aba and aba.strip() and aba != "Selecione uma corrida"]
    
    # Gerar lista esperada de abas para 2025 baseado no calendário
    from utils.constants import calendario_2025
    abas_esperadas_2025 = []
    for num_corrida in range(1, 24):
        info = calendario_2025[num_corrida]
        etapa = info.get('etapa', 1)
        tipo = info.get('tipo', 'Principal')
        
        if num_corrida == 1:
            nome_aba = "E1S"  # Corrida especial
        elif tipo == "Sprint":
            nome_aba = f"E{etapa}S"
        else:
            nome_aba = f"E{etapa}"
        
        abas_esperadas_2025.append(nome_aba)
    
    # Filtrar apenas abas que existem no arquivo E que correspondem ao padrão 2025
    # Estratégia: se não há dados de 2025, mostrar lista baseada no calendário mas sem dados
    abas_2025 = []
    abas_2025_existentes = []
    
    # Primeiro, verificar se há abas com "2025" no nome
    abas_com_ano = [aba for aba in abas if '2025' in str(aba)]
    
    if abas_com_ano:
        # Se há abas com 2025, usar apenas essas
        abas_2025 = abas_com_ano
        abas_2025_existentes = abas_2025
    else:
        # Se não há abas com 2025, usar TODAS as abas que correspondem ao padrão esperado de 2025
        # Isso permite que abas preenchidas diretamente no Google Sheets sejam detectadas
        for aba_esperada in abas_esperadas_2025:
            if aba_esperada in abas:
                abas_2025_existentes.append(aba_esperada)
        
        # Se encontrou abas que correspondem ao padrão, usar essas
        if abas_2025_existentes:
            abas_2025 = abas_2025_existentes
        else:
            # Se não encontrou nenhuma, verificar se há abas com padrão similar (E1, E2, E1S, E2S, etc.)
            # que podem ser de 2025 mas não estão no calendário ainda
            import re
            padrao_aba = re.compile(r'^E\d+S?$')
            abas_com_padrao = [aba for aba in abas if padrao_aba.match(str(aba).strip())]
            
            if abas_com_padrao:
                # Se há abas com padrão similar, usar essas (assumindo que são de 2025)
                abas_2025 = sorted(abas_com_padrao, key=lambda x: (
                    int(re.findall(r'\d+', str(x))[0]) if re.findall(r'\d+', str(x)) else 999,
                    'S' in str(x)
                ))
                abas_2025_existentes = abas_2025
            else:
                # Se não encontrou nenhuma, mostrar lista esperada mas indicar que não há dados
                abas_2025 = abas_esperadas_2025  # Mostrar lista esperada
    
    # Debug: mostrar informações sobre as abas encontradas (apenas em desenvolvimento)
    # Descomente as linhas abaixo para debug temporário
    # st.write(f"🔍 **Debug:** Total de abas carregadas: {len(abas)}")
    # st.write(f"🔍 **Debug:** Abas encontradas: {', '.join(abas[:20])}")  # Mostrar primeiras 20
    # st.write(f"🔍 **Debug:** Abas 2025 detectadas: {len(abas_2025_existentes)}")
    # st.write(f"🔍 **Debug:** Abas 2025: {', '.join(abas_2025_existentes[:20])}")

    # Configuração de coloração (Equipes vs Padrão Amattheis)
    color_mode_options = ("Equipes", "Padrão Amattheis")
    color_mode = st.radio(
        "Padrão de cores dos pilotos:",
        color_mode_options,
        index=0,
        horizontal=True,
        help="Altere para destacar apenas os pilotos Amattheis e deixar os demais em cinza."
    )
    pilot_color_map_equipes = get_pilot_color_map(season=2025)
    pilot_color_map_amattheis = get_amattheis_color_map(season=2025)
    pilot_color_map_global = (pilot_color_map_amattheis
                              if color_mode == "Padrão Amattheis"
                              else pilot_color_map_equipes)
    
    # Se não há dados ainda, mostrar mensagem informativa
    if not abas_2025_existentes:
        st.info("ℹ️ **Nenhum dado da temporada 2025 encontrado ainda.** Use a página 'Inserir Dados' para adicionar os dados das corridas.")
        st.markdown("---")
    
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    import traceback
    st.exception(e)
    st.stop()

# Criar dicionário para mapear nomes formatados para nomes de abas
abas_2025_formatadas = {}
for aba in abas_2025:
    if aba == "Selecione uma corrida":
        abas_2025_formatadas[aba] = aba
    else:
        nome_formatado = get_nome_aba_formatado(aba)
        abas_2025_formatadas[nome_formatado] = aba

# Criar lista de opções formatadas (sem duplicar "Selecione uma corrida")
opcoes_formatadas = ["Selecione uma corrida"] + [k for k in abas_2025_formatadas.keys() if k != "Selecione uma corrida"]

# Menu seletor para escolher a corrida
opcao_selecionada = st.selectbox("Selecione a corrida:", opcoes_formatadas)

# Converter opção formatada para nome de aba
if opcao_selecionada == "Selecione uma corrida":
    corrida_selecionada = "Selecione uma corrida"
else:
    corrida_selecionada = abas_2025_formatadas[opcao_selecionada]

# Carregar dados da corrida selecionada
if corrida_selecionada != "Selecione uma corrida":
    # Verificar se a aba existe no arquivo
    if corrida_selecionada not in dados:
        st.warning(f"⚠️ **Corrida '{corrida_selecionada}' ainda não possui dados.**")
        st.info(f"💡 Use a página 'Inserir Dados' para adicionar os dados desta corrida.")
        st.stop()
    
    df = dados[corrida_selecionada].copy()
    # Usar dicionário de pilotos 2025
    drivers_names_2025 = get_drivers_names(2025)
    df['Piloto'] = df['Numeral'].astype(str).map(drivers_names_2025)
    pilotos_presentes = df['Piloto'].dropna().unique()
    pilot_color_map_corrida = {
        piloto: pilot_color_map_global.get(piloto, AMATTHEIS_NEUTRAL_COLOR)
        for piloto in pilotos_presentes
    }
    
    # Criar mapa de cores por piloto baseado na equipe
    pilot_color_map = pilot_color_map_corrida
    
    # Identificar número da corrida usando o novo sistema 2025
    numero_corrida = parse_corrida_name(corrida_selecionada)
    
    # Usar novo sistema de identificação 2025
    if numero_corrida:
        tipo_corrida = get_tipo_corrida_2025(numero_corrida)
        nome_corrida_formatado = get_nome_corrida_2025(numero_corrida)
        track_image_path = get_track_image_2025(numero_corrida)
        
        # Exibir imagem do circuito
        try:
            from PIL import Image
            track_img = Image.open(track_image_path)
            st.image(track_img, width=180)
        except Exception as e:
            st.warning(f"Imagem do circuito não encontrada: {track_image_path}")
            # Tentar usar imagem padrão
            try:
                default_img = Image.open(DEFAULT_TRACK_IMAGE)
                st.image(default_img, width=180)
            except:
                pass
    else:
        # Fallback para sistema antigo
        if 'E' in corrida_selecionada:
            parts = corrida_selecionada.split('E')
            if len(parts) > 1 and 'S' in parts[1]:
                tipo_corrida = "Sprint"
            else:
                tipo_corrida = "Principal"
        else:
            tipo_corrida = "Principal"
        
        # Verificar o trackid da corrida selecionada (sistema antigo)
        if 'trackid' in df.columns and not df['trackid'].empty:
            trackid = df['trackid'].iloc[0]
            if trackid in track_images:
                st.image(track_images[trackid], width=180)
            else:
                st.warning("Imagem do circuito não encontrada.")
    
    # Criando abas de visualização
    tabs = st.tabs(['Overview', 'Mattheis', 'Driver analysis', 'Team analysis'])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with tabs[0]:  # Overview
        # Exibir nome formatado da corrida se disponível
        if numero_corrida:
            nome_exibicao = nome_corrida_formatado
        else:
            nome_exibicao = corrida_selecionada
        st.write(f"Dados da corrida: {nome_exibicao} - Temporada 2025")
        
        # Criar gráfico de tempo de troca de pneus
        if tipo_corrida == "Sprint":
            df['Pneu_Trocado'] = df['Pneu1']
        else:
            df['Pneu_Trocado'] = df[['Pneu1', 'Pneu2']].agg(
                lambda x: ', '.join(x.dropna()), axis=1)
        
        # Converter Tempopneu para numérico
        df['Tempopneu_numeric'] = convert_to_numeric(df['Tempopneu'])
        df['TempoTotal_numeric'] = convert_to_numeric(df['TempoTotal'])
        
        # Ordenar por POS (Posição na corrida) para ordenar o eixo X
        if 'POS' in df.columns:
            df_plot = df.copy()
            # Converter POS para numérico e ordenar
            df_plot['POS_numeric'] = pd.to_numeric(df_plot['POS'], errors='coerce')
            df_plot = df_plot.sort_values('POS_numeric', na_position='last')
        else:
            df_plot = df.copy()
        
        # Calcular escala do eixo Y para Tempo de Troca de Pneus
        min_tempopneu = df_plot['Tempopneu_numeric'].min()
        max_tempopneu = df_plot['Tempopneu_numeric'].max()
        if pd.notna(min_tempopneu) and pd.notna(max_tempopneu):
            y_min_pneu = max(0, min_tempopneu - 1)
            y_max_pneu = max_tempopneu + 1
        else:
            y_min_pneu = None
            y_max_pneu = None
        
        fig = px.bar(df_plot, x='Piloto', y='Tempopneu_numeric',
                     title=f'Tempo de Troca de Pneus - {corrida_selecionada}',
                     labels={
                         'Piloto': 'Pilotos', 
                         'Tempopneu_numeric': 'Tempo de Troca de Pneus (segundos)'
                     },
                     color='Piloto',
                     color_discrete_map=pilot_color_map,
                     text='Pneu_Trocado')
        fig.update_layout(title_x=0.4, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        # Definir escala do eixo Y
        if y_min_pneu is not None and y_max_pneu is not None:
            fig.update_yaxes(type='linear', range=[y_min_pneu, y_max_pneu])
        else:
            fig.update_yaxes(type='linear')
        st.plotly_chart(fig)
        st.caption("💡 **Dica:** Você pode interagir com o gráfico! Clique na legenda para mostrar/ocultar pilotos específicos e use os controles do eixo Y para ajustar a escala.")
        
        # Calcular escala do eixo Y para Tempo Total
        min_tempo_total = df_plot['TempoTotal_numeric'].min()
        max_tempo_total = df_plot['TempoTotal_numeric'].max()
        if pd.notna(min_tempo_total) and pd.notna(max_tempo_total):
            y_min_total = max(0, min_tempo_total - 1)
            y_max_total = max_tempo_total + 1
        else:
            y_min_total = None
            y_max_total = None
        
        # Gráfico de tempo total - usar o mesmo df_plot já ordenado por POS
        fig2 = px.bar(df_plot, x='Piloto', y='TempoTotal_numeric',
                      title=f'Tempo Total - {corrida_selecionada}',
                      labels={
                          'Piloto': 'Pilotos', 
                          'TempoTotal_numeric': 'Tempo Total (segundos)'
                      },
                      text='Pneu_Trocado',
                      color='Piloto',
                      color_discrete_map=pilot_color_map)
        fig2.update_layout(title_x=0.4, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        # Definir escala do eixo Y
        if y_min_total is not None and y_max_total is not None:
            fig2.update_yaxes(type='linear', range=[y_min_total, y_max_total])
        else:
            fig2.update_yaxes(type='linear')
        st.plotly_chart(fig2)
        st.caption("💡 **Dica:** Você pode interagir com o gráfico! Clique na legenda para mostrar/ocultar pilotos específicos e use os controles do eixo Y para ajustar a escala.")
        
        # Estatísticas de pneus
        total_carros = len(df)
        
        if tipo_corrida == "Sprint":
            pneu_counts = df['Pneu1'].value_counts()
            pneu_counts_all = len(df[df['Pneu1'] == 'ALL'])
            pneu_stats = {
                'TD': pneu_counts.get('TD', 0),
                'TE': pneu_counts.get('TE', 0),
                'DD': pneu_counts.get('DD', 0),
                'DE': pneu_counts.get('DE', 0),
                'ALL': pneu_counts_all
            }
            
            st.subheader("Estatísticas de Pneus Troca - Sprint")
            for pneu, count in pneu_stats.items():
                if count > 0:
                    percentage = (count / total_carros) * 100
                    st.metric(label=f"Carros que trocaram {pneu}", 
                             value=f"{count} ({percentage:.1f}%)")
            
            pneu_labels = [pneu for pneu, count in pneu_stats.items() if count > 0]
            pneu_values = [count for count in pneu_stats.values() if count > 0]
            
            if pneu_labels:
                fig3 = px.pie(values=pneu_values, names=pneu_labels,
                             title="Distribuição de Pneus Trocados - Sprint",
                             labels={'values': 'Quantidade', 'names': 'Pneu'},
                             hole=0.3)
                st.plotly_chart(fig3)
        else:  # Principal
            combinacoes = {
                'TD & TE': df[((df['Pneu1'] == 'TD') & (df['Pneu2'] == 'TE')) | ((df['Pneu1'] == 'TE') & (df['Pneu2'] == 'TD'))],
                'TD & DD': df[((df['Pneu1'] == 'TD') & (df['Pneu2'] == 'DD')) | ((df['Pneu1'] == 'DD') & (df['Pneu2'] == 'TD'))],
                'TD & DE': df[((df['Pneu1'] == 'TD') & (df['Pneu2'] == 'DE')) | ((df['Pneu1'] == 'DE') & (df['Pneu2'] == 'TD'))],
                'DD & DE': df[((df['Pneu1'] == 'DD') & (df['Pneu2'] == 'DE')) | ((df['Pneu1'] == 'DE') & (df['Pneu2'] == 'DD'))],
                'DD & TE': df[((df['Pneu1'] == 'DD') & (df['Pneu2'] == 'TE')) | ((df['Pneu1'] == 'TE') & (df['Pneu2'] == 'DD'))],
                'TE & DE': df[((df['Pneu1'] == 'TE') & (df['Pneu2'] == 'DE')) | ((df['Pneu1'] == 'DE') & (df['Pneu2'] == 'TE'))]
            }
            combinacoes['ALL'] = df[df['Pneu1'] == 'ALL']
            
            st.subheader("Estatísticas de Combinações de Pneus Trocados - Main")
            
            combinacao_labels = []
            combinacao_values = []
            
            for combinacao, dados_combinacao in combinacoes.items():
                count = len(dados_combinacao)
                if count > 0:
                    percentage = (count / total_carros) * 100
                    st.metric(label=f"Carros que trocaram {combinacao}", 
                             value=f"{count} ({percentage:.1f}%)")
                    combinacao_labels.append(combinacao)
                    combinacao_values.append(count)
            
            if combinacao_labels:
                fig3 = px.pie(values=combinacao_values, names=combinacao_labels,
                             title="Distribuição de Combinações de Pneus Trocados - Principal",
                             labels={'values': 'Quantidade', 'names': 'Combinação'},
                             hole=0.3)
                st.plotly_chart(fig3)
        
        # Análise bivariada
        st.subheader("Análise Bivariada")
        
        fig_scatter = px.scatter(df, x='POS', y='TempoTotal',
                                 title=f'Posição da Corrida vs Tempo Total de Troca - {corrida_selecionada}',
                                 labels={
                                     'POS': 'Posição da Corrida',
                                     'TempoTotal': 'Tempo Total (segundos)'
                                 },
                                 color='Piloto',
                                 color_discrete_map=pilot_color_map)
        fig_scatter.update_layout(title_x=0.4, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_scatter.update_traces(marker=dict(size=10))
        st.plotly_chart(fig_scatter)
        
        fig_scatter_pit = px.scatter(df, x='POS', y='pitlap',
                                     title=f'Posição da Corrida vs Volta Pit - {corrida_selecionada}',
                                     labels={
                                         'POS': 'Posição da Corrida',
                                         'pitlap': 'Volta no Pit'
                                     },
                                     color='Piloto',
                                     color_discrete_map=pilot_color_map)
        fig_scatter_pit.update_layout(title_x=0.4, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_scatter_pit.update_traces(marker=dict(size=10))
        st.plotly_chart(fig_scatter_pit)
    
    with tabs[1]:  # Mattheis
        try:
            mattheis_dados = load_mattheis_data()
            
            if corrida_selecionada in mattheis_dados.keys():
                df_mattheis = mattheis_dados[corrida_selecionada].copy()
                df_mattheis['Piloto'] = df_mattheis['Numeral'].astype(str).map(mattheis_names_2025)
                df_filtrado_mattheis = df_mattheis[df_mattheis['Piloto'].notnull()]
                
                if not df_filtrado_mattheis.empty:
                    df_filtrado_mattheis['Cor'] = df_filtrado_mattheis['Numeral'].astype(str).map(cor_por_piloto)
                    
                    if tipo_corrida == "Sprint":
                        df_filtrado_mattheis['Troca1'] = df_filtrado_mattheis['Troca1']
                        df_filtrado_mattheis['TempoDeslocamento'] = df_filtrado_mattheis['Tempopneu'] - df_filtrado_mattheis['Troca1']
                    else:  # Principal
                        df_filtrado_mattheis['Troca1'] = df_filtrado_mattheis['Troca1']
                        df_filtrado_mattheis['Troca2'] = df_filtrado_mattheis['Troca2']
                        df_filtrado_mattheis['TempoDeslocamento'] = df_filtrado_mattheis['Tempopneu'] - (
                            df_filtrado_mattheis['Troca1'] + df_filtrado_mattheis['Troca2'])
                    
                    # Gráficos
                    graficos = [
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='TempoTotal',
                               title='Tempo Total por Piloto',
                               labels={'TempoTotal': 'Tempo Total (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Total"),
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='Tempopneu',
                               title='Tempo de Troca de Pneus por Piloto',
                               labels={'Tempopneu': 'Tempo de Troca de Pneus (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Pneus"),
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='aj',
                               title='Tempo de Reação Air Jack por Piloto',
                               labels={'aj': 'Tempo de Reação (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo AJ"),
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='1c',
                               title='Tempo para 1ª Conexão por Piloto',
                               labels={'1c': 'Tempo para 1ª Conexão (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo 1C"),
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='Troca1',
                               title='Tempo de Troca1 (Pistola e Encaixe) por Piloto',
                               labels={'Troca1': 'Tempo de Troca1 (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Troca1"),
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='Troca2',
                               title='Tempo de Troca2 (Pistola e encaixe) por Piloto',
                               labels={'Troca2': 'Tempo de Troca2 (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Troca2") if tipo_corrida == "Principal" else None,
                        (px.bar(df_filtrado_mattheis, x='Piloto', y='TempoDeslocamento',
                               title='Tempo de Deslocamento por Piloto',
                               labels={'TempoDeslocamento': 'Tempo de Deslocamento (segundos)', 'Piloto': 'Piloto'},
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Deslocamento")
                    ]
                    
                    graficos = [g for g in graficos if g is not None]
                    
                    num_graficos = len(graficos)
                    for i in range(0, num_graficos, 2):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.plotly_chart(graficos[i][0], use_container_width=True)
                        if i + 1 < num_graficos:
                            with col2:
                                st.plotly_chart(graficos[i + 1][0], use_container_width=True)
                    
                    # Links de vídeo - Visualização melhorada
                    st.markdown("---")
                    st.subheader("📹 Vídeos dos Pit Stops - YouTube")
                    
                    videos_exibidos = False
                    for _, row in df_filtrado_mattheis.iterrows():
                        piloto = row['Piloto']
                        link = row.get('link', None)
                        if pd.notna(link) and link and str(link).strip():
                            videos_exibidos = True
                            # Criar card visual para o link
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                st.markdown(f"**{piloto}**")
                            with col2:
                                st.markdown(f"[▶️ Assista no YouTube]({link})", unsafe_allow_html=True)
                    
                    if not videos_exibidos:
                        st.info("ℹ️ Nenhum link de vídeo disponível para esta corrida.")
                else:
                    st.warning("Nenhum dado encontrado para o Grupo Mattheis nesta corrida.")
            else:
                st.warning("Nenhum dado encontrado para o Grupo Mattheis nesta corrida.")
        except Exception as e:
            st.warning(f"Dados do Mattheis não disponíveis para esta corrida: {str(e)}")
    
    with tabs[2]:  # Driver Analysis
        drivers_names_2025 = get_drivers_names(2025)
        pilotos_selecionados = st.multiselect(
            "Selecione os pilotos:", list(drivers_names_2025.values()), default=[])
        
        if pilotos_selecionados:
            # Criar mapa de cores para os pilotos selecionados (usando dicionário de pilotos diretamente)
            driver_color_map = {
                piloto: pilot_color_map_global.get(piloto, AMATTHEIS_NEUTRAL_COLOR)
                for piloto in pilotos_selecionados
            }
            
            dados_pilotos = []
            
            # Iterar sobre as abas da temporada 2025
            for nome_abas in abas_2025[1:]:  # Pular "Selecione uma corrida"
                if nome_abas in dados:
                    df = dados[nome_abas].copy()
                    drivers_names_2025 = get_drivers_names(2025)
                    df['Piloto'] = df['Numeral'].astype(str).map(drivers_names_2025)
                    
                    if 'raceid' in df.columns:
                        df['raceid'] = df['raceid'].astype(int)
                    
                    # Converter para numérico antes de calcular
                    df['TempoTotal_numeric'] = convert_to_numeric(df['TempoTotal'])
                    df['Tempopneu_numeric'] = convert_to_numeric(df['Tempopneu'])
                    df['Ranking_TempoTotal'] = df['TempoTotal_numeric'].rank(method='min', na_option='keep')
                    df['Ranking_Tempopneu'] = df['Tempopneu_numeric'].rank(method='min', na_option='keep')
                    df['Tempo_Driver'] = df['TempoTotal_numeric'] - df['Tempopneu_numeric']
                    
                    df_pilotos = df[df['Piloto'].isin(pilotos_selecionados)]
                    
                    min_tempo_total = df['TempoTotal_numeric'].min()
                    min_tempopneu = df['Tempopneu_numeric'].min()
                    min_tempo_driver = df['Tempo_Driver'].min()
                    
                    for piloto in pilotos_selecionados:
                        df_piloto = df_pilotos[df_pilotos['Piloto'] == piloto]
                        if not df_piloto.empty:
                            dados_pilotos.append({
                                'Corrida': nome_abas,
                                'Piloto': piloto,
                                'deltatempototal': df_piloto['TempoTotal_numeric'].values[0] - min_tempo_total,
                                'Ranking_TempoTotal': df_piloto['Ranking_TempoTotal'].values[0],
                                'deltatempopneu': df_piloto['Tempopneu_numeric'].values[0] - min_tempopneu,
                                'Ranking_Tempopneu': df_piloto['Ranking_Tempopneu'].values[0],
                                'deltatempodriver': df_piloto['Tempo_Driver'].values[0] - min_tempo_driver,
                                'Tempo_Driver': df_piloto['Tempo_Driver'].values[0],
                                'raceid': df_piloto['raceid'].values[0] if 'raceid' in df_piloto.columns else None
                            })
            
            if dados_pilotos:
                df_pilotos_total = pd.DataFrame(dados_pilotos)
                if 'raceid' in df_pilotos_total.columns:
                    df_pilotos_total.sort_values(by='raceid', inplace=True)
                
                fig_total = px.line(df_pilotos_total, x='Corrida', y='deltatempototal', color='Piloto',
                                   title='Diferença do Tempo Total em Relação ao Mais Rápido',
                                   labels={'Corrida': 'Etapa', 'deltatempototal': 'Diferença do Tempo Total (segundos)'},
                                   markers=True,
                                   color_discrete_map=driver_color_map)
                fig_total.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_total)
                
                fig_pneu = px.line(df_pilotos_total, x='Corrida', y='deltatempopneu', color='Piloto',
                                   title='Diferença do Tempo de Troca de Pneus em Relação ao Mais Rápido',
                                   labels={'Corrida': 'Etapa', 'deltatempopneu': 'Diferença do Tempo de Troca de Pneus (segundos)'},
                                   markers=True,
                                   color_discrete_map=driver_color_map)
                fig_pneu.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pneu)
                
                fig_driver = px.line(df_pilotos_total, x='Corrida', y='deltatempodriver', color='Piloto',
                                     title='Diferença do Tempo do Piloto em Relação ao Mais Rápido',
                                     labels={'Corrida': 'Etapa', 'deltatempodriver': 'Diferença do Tempo do Piloto (segundos)'},
                                     markers=True,
                                     color_discrete_map=driver_color_map)
                fig_driver.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_driver)
                
                df_pilotos_display = df_pilotos_total[['Corrida', 'Piloto', 'Ranking_TempoTotal', 'Ranking_Tempopneu', 'Tempo_Driver']]
                
                colunas = st.columns(2)
                for idx, piloto in enumerate(pilotos_selecionados):
                    df_piloto = df_pilotos_display[df_pilotos_display['Piloto'] == piloto]
                    if not df_piloto.empty:
                        with colunas[idx % 2]:
                            st.subheader(piloto)
                            st.dataframe(df_piloto)
                
                media_rankings = df_pilotos_total.groupby('Piloto')[['Ranking_TempoTotal', 'Ranking_Tempopneu']].mean().reset_index()
                media_rankings.rename(columns={
                    'Ranking_TempoTotal': 'Média Ranking Tempo Total',
                    'Ranking_Tempopneu': 'Média Ranking Tempo Pneus'
                }, inplace=True)
                
                st.subheader("Média dos Rankings dos Pilotos Selecionados")
                st.dataframe(media_rankings)
    
    with tabs[3]:  # Team Analysis
        dados_ano = []
        drivers_names_full = get_drivers_names(2025)
        ordem_corridas = {
            aba: idx for idx, aba in enumerate(
                [aba for aba in abas_2025 if aba != "Selecione uma corrida"]
            )
        }
        
        for nome_abas in abas_2025[1:]:  # Pular "Selecione uma corrida"
            if nome_abas in dados:
                df = dados[nome_abas].copy()
                # Converter Numeral para int antes de mapear para Time
                df['Numeral_int'] = pd.to_numeric(df['Numeral'], errors='coerce').astype('Int64')
                team_info_dict = get_team_info(2025)
                df['Time'] = df['Numeral_int'].map(team_info_dict)
                # Filtrar apenas linhas com Time válido (não NaN)
                df = df[df['Time'].notna()].copy()
                
                if not df.empty:
                    df['Numero'] = df['Numeral'].astype(str)
                    df['Piloto'] = df['Numero'].map(drivers_names_full)
                    df['Corrida'] = get_nome_aba_formatado(nome_abas)
                    df['CorridaCodigo'] = nome_abas
                    df['OrdemCorrida'] = ordem_corridas.get(nome_abas, 0)
                    # Converter para numérico antes de calcular
                    df['Tempopneu_numeric'] = convert_to_numeric(df['Tempopneu'])
                    df['TempoTotal_numeric'] = convert_to_numeric(df['TempoTotal'])
                    melhor_tempopneu = df['Tempopneu_numeric'].min()
                    df['deltabest'] = df['Tempopneu_numeric'] - melhor_tempopneu
                    melhor_tempototal = df['TempoTotal_numeric'].min()
                    df['deltabest_total'] = df['TempoTotal_numeric'] - melhor_tempototal
                    df['TempoProcedimento'] = df['TempoTotal_numeric'] - df['Tempopneu_numeric']
                    dados_ano.append(df)
        
        if dados_ano:
            df_ano = pd.concat(dados_ano)
            # Garantir que apenas linhas com Time válido sejam usadas
            df_ano = df_ano[df_ano['Time'].notna()].copy()
            
            if not df_ano.empty:
                # Criar mapa de cores por equipe
                team_color_map = {team: team_colors_2025.get(team, '#808080') for team in df_ano['Time'].unique()}
                
                fig_total = px.box(df_ano, x='Time', y='TempoTotal_numeric',
                                   title='Box Plot do Tempo Total por Time - Temporada 2025',
                                   color='Time',
                                   color_discrete_map=team_color_map,
                                   labels={'TempoTotal_numeric': 'Tempo Total (segundos)', 'Time': 'Time'})
                fig_total.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_total)
                
                fig_pneu = px.box(df_ano, x='Time', y='Tempopneu_numeric',
                                 title='Box Plot do Tempo de Troca de Pneus por Time - Temporada 2025',
                                 color='Time',
                                 color_discrete_map=team_color_map,
                                 labels={'Tempopneu_numeric': 'Tempo de Troca de Pneus (segundos)', 'Time': 'Time'})
                fig_pneu.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_pneu)
                
                fig_deltabest = px.box(df_ano, x='Time', y='deltabest',
                                       title='Box Plot da Diferença em Relação ao Melhor Tempo de Troca de Pneus por Time - Temporada 2025',
                                       color='Time',
                                       color_discrete_map=team_color_map,
                                       labels={'deltabest': 'Diferença (segundos)', 'Time': 'Time'})
                fig_deltabest.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_deltabest)
                
                fig_deltabest_total = px.box(df_ano, x='Time', y='deltabest_total',
                                             title='Box Plot da Diferença em Relação ao Melhor Tempo Total por Time - Temporada 2025',
                                             color='Time',
                                             color_discrete_map=team_color_map,
                                             labels={'deltabest_total': 'Diferença (segundos)', 'Time': 'Time'})
                fig_deltabest_total.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_deltabest_total)

                st.markdown("---")
                st.subheader("Visão Geral do Ano - Tempo Total menos Procedimento")

                corrida_ordem_df = (df_ano[['Corrida', 'OrdemCorrida']]
                                    .dropna(subset=['Corrida'])
                                    .drop_duplicates()
                                    .sort_values('OrdemCorrida', na_position='last'))
                if corrida_ordem_df.empty:
                    corridas_unicas = list(dict.fromkeys(df_ano['Corrida'].dropna().tolist()))
                    corrida_ordem_df = pd.DataFrame({
                        'Corrida': corridas_unicas,
                        'OrdemCorrida': list(range(len(corridas_unicas)))
                    })
                corrida_ordem = corrida_ordem_df['Corrida'].tolist()

                # Tabela estilo heatmap por piloto e corrida
                heatmap_df = df_ano[['Corrida', 'Numero', 'TempoProcedimento']].dropna(subset=['TempoProcedimento'])
                if not heatmap_df.empty:
                    heatmap_resumido = (heatmap_df.groupby(['Corrida', 'Numero'], as_index=False)
                                        ['TempoProcedimento'].mean())
                    heatmap_pivot = (heatmap_resumido.pivot(index='Corrida', columns='Numero', values='TempoProcedimento')
                                     .reindex(corrida_ordem))
                    # Ordenar colunas por número do carro
                    def sort_key(col):
                        try:
                            return int(col)
                        except (TypeError, ValueError):
                            return 9999
                    heatmap_pivot = heatmap_pivot[sorted(heatmap_pivot.columns, key=sort_key)]
                    render_dataframe_with_optional_style(
                        heatmap_pivot,
                        formatter=lambda v: f"{v:.1f} s" if pd.notnull(v) else "—",
                        cmap='RdYlGn_r',
                        axis=None
                    )
                else:
                    st.info("Sem dados suficientes para montar a tabela geral dos pilotos.")

                st.markdown("---")
                st.subheader("Campeonato de Pit Stop (Diferença para o Mais Rápido por Etapa)")

                df_team_scores = (df_ano.groupby(['Corrida', 'Time'])['deltabest']
                                  .min()
                                  .reset_index())
                if not df_team_scores.empty:
                    total_corridas = df_team_scores['Corrida'].nunique()
                    max_descartes = max(0, min(6, total_corridas - 1))
                    if max_descartes > 0:
                        descartar = st.slider(
                            "Descartar piores resultados:",
                            min_value=0,
                            max_value=max_descartes,
                            value=min(4, max_descartes),
                            help="Remove os maiores tempos (piores resultados) antes de calcular a soma final."
                        )
                    else:
                        descartar = 0
                        st.info("Descartes indisponíveis: é necessário ter pelo menos duas corridas para descartar resultados.")

                    # Tabela detalhada por corrida
                    corrida_ordem_campeonato = corrida_ordem if corrida_ordem else list(dict.fromkeys(df_team_scores['Corrida'].tolist()))
                    team_pivot = (df_team_scores.pivot(index='Corrida', columns='Time', values='deltabest')
                                  .reindex(corrida_ordem_campeonato))
                    team_pivot = team_pivot.reindex(sorted(team_pivot.columns), axis=1)
                    render_dataframe_with_optional_style(
                        team_pivot,
                        formatter=lambda v: f"{v:.2f}" if pd.notnull(v) else "—",
                        cmap='RdYlGn_r',
                        axis=None
                    )

                    # Ranking geral
                    ranking_registros = []
                    for equipe, grupo in df_team_scores.groupby('Time'):
                        valores = grupo['deltabest'].sort_values()
                        if descartar > 0 and len(valores) > descartar:
                            valores_considerados = valores.iloc[:-descartar]
                            descartados = valores.iloc[-descartar:]
                        else:
                            valores_considerados = valores
                            descartados = pd.Series(dtype=float)
                        soma = valores_considerados.sum()
                        ranking_registros.append({
                            'Equipe': equipe,
                            'Participações': len(grupo),
                            'Descartes aplicados': len(descartados),
                            'Soma (menor é melhor)': round(soma, 2)
                        })
                    ranking_df = (pd.DataFrame(ranking_registros)
                                  .sort_values('Soma (menor é melhor)', ascending=True)
                                  .reset_index(drop=True))
                    ranking_df.insert(0, 'Pos', ranking_df.index + 1)
                    render_dataframe_with_optional_style(
                        ranking_df,
                        formatter={'Soma (menor é melhor)': '{:.2f}'},
                        cmap='RdYlGn_r',
                        axis=None
                    )
                    st.caption("O ranking soma a diferença do tempo de troca de pneus para o melhor de cada etapa. Valores menores indicam melhor desempenho.")
                else:
                    st.info("Sem dados suficientes para calcular o campeonato de pit stop.")
            else:
                st.warning("⚠️ Nenhum dado válido encontrado para análise de times. Verifique se os numerais estão corretos no dicionário de times.")

else:
    st.warning("Por favor, selecione uma corrida para visualizar os dados.")

