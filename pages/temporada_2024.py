"""
Página da Temporada 2024
Visualização e análise de dados de pit stops da temporada 2024
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image
from utils.constants import (
    drivers_names, team_info, track_images, 
    cor_por_piloto, mattheis_names, COVER_IMAGE, init_google_sheets_config
)

# Temporada 2024 usa dados estáticos do Excel local (não Google Sheets)
# from utils.data_loader import load_all_data, load_mattheis_data, filter_sheets_by_season

# Configuração da página - DEVE SER O PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    page_title="Temporada 2024 - Pit Stop Report",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar configurações do Google Sheets (depois do set_page_config)
init_google_sheets_config()

# Título da temporada
st.title("🏁 Temporada 2024")
st.info("ℹ️ Temporada 2024 - Dados estáticos (temporada encerrada)")

# Carregar dados - SEMPRE usar Excel local para 2024 (dados estáticos)
try:
    # Temporada 2024 é estática - sempre usar Excel local
    from utils.constants import PITSTOP_FILE
    dados = pd.read_excel(PITSTOP_FILE, sheet_name=None)
    abas = list(dados.keys())
    
    # Filtrar abas da temporada 2024
    # Estratégia: excluir abas que são claramente de 2025
    # Primeiro, verificar se há abas com "2024" no nome
    abas_com_ano_2024 = [aba for aba in abas if '2024' in str(aba)]
    
    if abas_com_ano_2024:
        # Se há abas com 2024, usar apenas essas
        abas_2024 = abas_com_ano_2024
    else:
        # Se não há abas com 2024, excluir abas que são de 2025
        # Gerar lista esperada de abas para 2025 (baseado no calendário)
        from utils.constants import calendario_2025
        abas_esperadas_2025 = []
        for num_corrida in range(1, 24):
            info = calendario_2025[num_corrida]
            etapa = info.get('etapa', 1)
            tipo = info.get('tipo', 'Principal')
            
            if num_corrida == 1:
                nome_aba = "E1S"
            elif tipo == "Sprint":
                nome_aba = f"E{etapa}S"
            else:
                nome_aba = f"E{etapa}"
            
            abas_esperadas_2025.append(nome_aba)
        
        # Excluir abas que são esperadas para 2025
        # E também excluir abas que têm "2025" no nome
        abas_2025_identificadas = [aba for aba in abas if '2025' in str(aba)]
        abas_2025_identificadas.extend(abas_esperadas_2025)
        
        # Filtrar: pegar apenas abas que não são de 2025
        abas_2024 = [aba for aba in abas if aba not in abas_2025_identificadas]
    
    # Remover abas que não existem
    abas_2024 = [aba for aba in abas_2024 if aba in dados.keys()]
    
    if not abas_2024:
        st.warning("⚠️ Nenhuma aba encontrada para a temporada 2024. Verifique o mapeamento de temporadas.")
        st.info("💡 Você pode ajustar o mapeamento em `pages/temporada_2024.py` na função `filter_sheets_by_season`")
    
except Exception as e:
    st.error(f"Erro ao carregar dados: {str(e)}")
    st.stop()

# Adicionar opção "Selecione uma corrida"
abas_2024.insert(0, "Selecione uma corrida")

# Menu seletor para escolher a corrida
corrida_selecionada = st.selectbox("Selecione a corrida:", abas_2024)

# Carregar dados da corrida selecionada
if corrida_selecionada != "Selecione uma corrida" and corrida_selecionada in dados:
    df = dados[corrida_selecionada].copy()
    df['Piloto'] = df['Numeral'].astype(str).map(drivers_names)
    
    # Verificar se é Sprint ou Main
    if 'E' in corrida_selecionada:
        parts = corrida_selecionada.split('E')
        if len(parts) > 1 and 'S' in parts[1]:
            tipo_corrida = "Sprint"
        else:
            tipo_corrida = "Main"
    else:
        tipo_corrida = "Main"
    
    # Verificar o trackid da corrida selecionada
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
        st.write(f"Dados da corrida: {corrida_selecionada} - Temporada 2024")
        
        # Criar gráfico de tempo de troca de pneus
        if tipo_corrida == "Sprint":
            df['Pneu_Trocado'] = df['Pneu1']
        else:
            df['Pneu_Trocado'] = df[['Pneu1', 'Pneu2']].agg(
                lambda x: ', '.join(x.dropna()), axis=1)
        
        fig = px.bar(df, x='Piloto', y='Tempopneu',
                     title=f'Tempo de Troca de Pneus - {corrida_selecionada}',
                     labels={
                         'Piloto': 'Pilotos', 
                         'Tempopneu': 'Tempo de Troca de Pneus (segundos)'
                     },
                     color='Piloto',
                     text='Pneu_Trocado')
        fig.update_layout(title_x=0.4)
        st.plotly_chart(fig)
        
        # Gráfico de tempo total
        fig2 = px.bar(df, x='Piloto', y='TempoTotal',
                      title=f'Tempo Total - {corrida_selecionada}',
                      labels={
                          'Piloto': 'Pilotos', 
                          'TempoTotal': 'Tempo Total (segundos)'
                      },
                      text='Pneu_Trocado',
                      color='Piloto')
        fig2.update_layout(title_x=0.4)
        st.plotly_chart(fig2)
        
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
        else:  # Main
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
                             title="Distribuição de Combinações de Pneus Trocados - Main",
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
                                 color='Piloto')
        fig_scatter.update_layout(title_x=0.4)
        fig_scatter.update_traces(marker=dict(size=10))
        st.plotly_chart(fig_scatter)
        
        fig_scatter_pit = px.scatter(df, x='POS', y='pitlap',
                                     title=f'Posição da Corrida vs Volta Pit - {corrida_selecionada}',
                                     labels={
                                         'POS': 'Posição da Corrida',
                                         'pitlap': 'Volta no Pit'
                                     },
                                     color='Piloto')
        fig_scatter_pit.update_layout(title_x=0.4)
        fig_scatter_pit.update_traces(marker=dict(size=10))
        st.plotly_chart(fig_scatter_pit)
    
    with tabs[1]:  # Mattheis
        try:
            # Temporada 2024 - sempre usar Excel local (dados estáticos)
            from utils.constants import MATTHEIS_FILE
            mattheis_dados = pd.read_excel(MATTHEIS_FILE, sheet_name=None)
            
            if corrida_selecionada in mattheis_dados.keys():
                df_mattheis = mattheis_dados[corrida_selecionada].copy()
                df_mattheis['Piloto'] = df_mattheis['Numeral'].astype(str).map(mattheis_names)
                df_filtrado_mattheis = df_mattheis[df_mattheis['Piloto'].notnull()]
                
                if not df_filtrado_mattheis.empty:
                    df_filtrado_mattheis['Cor'] = df_filtrado_mattheis['Numeral'].astype(str).map(cor_por_piloto)
                    
                    if tipo_corrida == "Sprint":
                        df_filtrado_mattheis['Troca1'] = df_filtrado_mattheis['Troca1']
                        df_filtrado_mattheis['TempoDeslocamento'] = df_filtrado_mattheis['Tempopneu'] - df_filtrado_mattheis['Troca1']
                    else:
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
                               color='Piloto', color_discrete_map=cor_por_piloto), "Tempo Troca2") if tipo_corrida == "Main" else None,
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
                    
                    # Links de vídeo
                    for _, row in df_filtrado_mattheis.iterrows():
                        piloto = row['Piloto']
                        link = row.get('link', None)
                        if pd.notna(link) and link:
                            st.markdown(f"[Assista ao vídeo do {piloto} no YouTube]({link})")
                else:
                    st.warning("Nenhum dado encontrado para o Grupo Mattheis nesta corrida.")
            else:
                st.warning("Nenhum dado encontrado para o Grupo Mattheis nesta corrida.")
        except Exception as e:
            st.warning(f"Dados do Mattheis não disponíveis para esta corrida: {str(e)}")
    
    with tabs[2]:  # Driver Analysis
        pilotos_selecionados = st.multiselect(
            "Selecione os pilotos:", list(drivers_names.values()), default=[])
        
        if pilotos_selecionados:
            dados_pilotos = []
            
            # Iterar sobre as abas da temporada 2024
            for nome_abas in abas_2024[1:]:  # Pular "Selecione uma corrida"
                if nome_abas in dados:
                    df = dados[nome_abas].copy()
                    df['Piloto'] = df['Numeral'].astype(str).map(drivers_names)
                    
                    if 'raceid' in df.columns:
                        df['raceid'] = df['raceid'].astype(int)
                    
                    df['Ranking_TempoTotal'] = df['TempoTotal'].rank(method='min', na_option='keep')
                    df['Ranking_Tempopneu'] = df['Tempopneu'].rank(method='min', na_option='keep')
                    df['Tempo_Driver'] = df['TempoTotal'] - df['Tempopneu']
                    
                    df_pilotos = df[df['Piloto'].isin(pilotos_selecionados)]
                    
                    min_tempo_total = df['TempoTotal'].min()
                    min_tempopneu = df['Tempopneu'].min()
                    min_tempo_driver = df['Tempo_Driver'].min()
                    
                    for piloto in pilotos_selecionados:
                        df_piloto = df_pilotos[df_pilotos['Piloto'] == piloto]
                        if not df_piloto.empty:
                            dados_pilotos.append({
                                'Corrida': nome_abas,
                                'Piloto': piloto,
                                'deltatempototal': df_piloto['TempoTotal'].values[0] - min_tempo_total,
                                'Ranking_TempoTotal': df_piloto['Ranking_TempoTotal'].values[0],
                                'deltatempopneu': df_piloto['Tempopneu'].values[0] - min_tempopneu,
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
                                   markers=True)
                st.plotly_chart(fig_total)
                
                fig_pneu = px.line(df_pilotos_total, x='Corrida', y='deltatempopneu', color='Piloto',
                                   title='Diferença do Tempo de Troca de Pneus em Relação ao Mais Rápido',
                                   labels={'Corrida': 'Etapa', 'deltatempopneu': 'Diferença do Tempo de Troca de Pneus (segundos)'},
                                   markers=True)
                st.plotly_chart(fig_pneu)
                
                fig_driver = px.line(df_pilotos_total, x='Corrida', y='deltatempodriver', color='Piloto',
                                     title='Diferença do Tempo do Piloto em Relação ao Mais Rápido',
                                     labels={'Corrida': 'Etapa', 'deltatempodriver': 'Diferença do Tempo do Piloto (segundos)'},
                                     markers=True)
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
        
        for nome_abas in abas_2024[1:]:  # Pular "Selecione uma corrida"
            if nome_abas in dados:
                df = dados[nome_abas].copy()
                df['Time'] = df['Numeral'].map(team_info)
                melhor_tempopneu = df['Tempopneu'].min()
                df['deltabest'] = df['Tempopneu'] - melhor_tempopneu
                melhor_tempototal = df['TempoTotal'].min()
                df['deltabest_total'] = df['TempoTotal'] - melhor_tempototal
                dados_ano.append(df)
        
        if dados_ano:
            df_ano = pd.concat(dados_ano)
            
            fig_total = px.box(df_ano, x='Time', y='TempoTotal',
                               title='Box Plot do Tempo Total por Time - Temporada 2024',
                               color='Time',
                               labels={'TempoTotal': 'Tempo Total (segundos)', 'Time': 'Time'})
            st.plotly_chart(fig_total)
            
            fig_pneu = px.box(df_ano, x='Time', y='Tempopneu',
                             title='Box Plot do Tempo de Troca de Pneus por Time - Temporada 2024',
                             color='Time',
                             labels={'Tempopneu': 'Tempo de Troca de Pneus (segundos)', 'Time': 'Time'})
            st.plotly_chart(fig_pneu)
            
            fig_deltabest = px.box(df_ano, x='Time', y='deltabest',
                                   title='Box Plot da Diferença em Relação ao Melhor Tempo de Troca de Pneus por Time - Temporada 2024',
                                   color='Time',
                                   labels={'deltabest': 'Diferença (segundos)', 'Time': 'Time'})
            st.plotly_chart(fig_deltabest)
            
            fig_deltabest_total = px.box(df_ano, x='Time', y='deltabest_total',
                                         title='Box Plot da Diferença em Relação ao Melhor Tempo Total por Time - Temporada 2024',
                                         color='Time',
                                         labels={'deltabest_total': 'Diferença (segundos)', 'Time': 'Time'})
            st.plotly_chart(fig_deltabest_total)

else:
    st.warning("Por favor, selecione uma corrida para visualizar os dados.")

