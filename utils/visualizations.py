"""
Funções auxiliares para criação de visualizações
"""

import pandas as pd
import plotly.express as px
from typing import Optional, List, Tuple
from utils.constants import cor_por_piloto


def create_tire_time_chart(df: pd.DataFrame, corrida_selecionada: str) -> px.bar:
    """Cria gráfico de tempo de troca de pneus"""
    if 'Sprint' in corrida_selecionada or ('E' in corrida_selecionada and 'S' in corrida_selecionada.split('E')[1]):
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
    return fig


def create_total_time_chart(df: pd.DataFrame, corrida_selecionada: str) -> px.bar:
    """Cria gráfico de tempo total"""
    if 'Sprint' in corrida_selecionada or ('E' in corrida_selecionada and 'S' in corrida_selecionada.split('E')[1]):
        df['Pneu_Trocado'] = df['Pneu1']
    else:
        df['Pneu_Trocado'] = df[['Pneu1', 'Pneu2']].agg(
            lambda x: ', '.join(x.dropna()), axis=1)
    
    fig = px.bar(df, x='Piloto', y='TempoTotal',
                 title=f'Tempo Total - {corrida_selecionada}',
                 labels={
                     'Piloto': 'Pilotos', 
                     'TempoTotal': 'Tempo Total (segundos)'
                 },
                 text='Pneu_Trocado',
                 color='Piloto')
    fig.update_layout(title_x=0.4)
    return fig


def create_tire_distribution_pie(df: pd.DataFrame, tipo_corrida: str) -> Optional[px.pie]:
    """Cria gráfico de pizza para distribuição de pneus"""
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
        pneu_labels = [pneu for pneu, count in pneu_stats.items() if count > 0]
        pneu_values = [count for count in pneu_stats.values() if count > 0]
        
        if pneu_labels:
            fig = px.pie(values=pneu_values, names=pneu_labels,
                        title="Distribuição de Pneus Trocados - Sprint",
                        labels={'values': 'Quantidade', 'names': 'Pneu'},
                        hole=0.3)
            return fig
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
        
        combinacao_labels = []
        combinacao_values = []
        
        for combinacao, dados in combinacoes.items():
            count = len(dados)
            if count > 0:
                combinacao_labels.append(combinacao)
                combinacao_values.append(count)
        
        if combinacao_labels:
            fig = px.pie(values=combinacao_values, names=combinacao_labels,
                        title="Distribuição de Combinações de Pneus Trocados - Main",
                        labels={'values': 'Quantidade', 'names': 'Combinação'},
                        hole=0.3)
            return fig
    
    return None


def create_position_scatter(df: pd.DataFrame, corrida_selecionada: str, 
                            y_column: str, title: str, y_label: str) -> px.scatter:
    """Cria gráfico de dispersão de posição vs métrica"""
    fig = px.scatter(df, x='POS', y=y_column,
                     title=title,
                     labels={
                         'POS': 'Posição da Corrida',
                         y_column: y_label
                     },
                     color='Piloto')
    fig.update_layout(title_x=0.4)
    fig.update_traces(marker=dict(size=10))
    return fig

