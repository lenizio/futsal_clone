import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.tools import mpl_to_plotly
import io
import requests
import plotly.io as pio
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import os

def convert_df_to_csv(df):
    # Usando StringIO para criar um buffer de string
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, encoding="utf-8",index=False)
    return csv_buffer.getvalue()


def listar_opces_jogadores(lista_jogadores):
    opcoes_jogadores_dict={}
    opcoes_goleiro_dict = {jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Goleiro"}
    opcoes_jogadores_dict.update(opcoes_goleiro_dict)
    opcoes_goleiro_list = list(opcoes_goleiro_dict.keys())                    
    opcoes_jogadores_linha_dict = {}
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Fixo"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala D"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala E"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Pivô"})
    opcoes_jogadores_linha_list = list(opcoes_jogadores_linha_dict.keys())
    opcoes_jogadores_linha_list.sort()
    opcoes_jogadores_list=opcoes_goleiro_list+opcoes_jogadores_linha_list
    opcoes_jogadores_dict.update(opcoes_jogadores_linha_dict)
    
    return opcoes_jogadores_dict, opcoes_jogadores_list

def pegar_dados_pizza_plot(lista_jogadas):
    df = pd.DataFrame(lista_jogadas,columns=["id","jogador_id","jogador_nome","jogo_id","jogada","tempo","x_loc","y_loc"])
    tipos_finalizacoes = ["FIN.C", "FIN.E", "FIN.T"]    
    quantidade_finalizacoes = df.jogada[df["jogada"].isin( tipos_finalizacoes)].value_counts().reindex( tipos_finalizacoes, fill_value=0)
    quantidade_finalizacoes = quantidade_finalizacoes.to_numpy()
    
    tipos_desarmes = ['DES.C/P.', 'DES.S/P.']
    quantidade_desarmes = df.jogada[df["jogada"].isin(tipos_desarmes)].value_counts().reindex(tipos_desarmes,fill_value=0)
    quantidade_desarmes = quantidade_desarmes.to_numpy()
    
    percas_de_posse = ['PER.P', 'C.A']
    quantidade_percas_posse = df.jogada[df["jogada"].isin(percas_de_posse)].value_counts().reindex(percas_de_posse,fill_value=0)
    quantidade_percas_posse = quantidade_percas_posse.to_numpy()

    dados_grafico_pizza = [
        {
            "data": quantidade_finalizacoes,
            "labels": tipos_finalizacoes,
            "title": "Distribuição de Finalizações"
        },
        {
            "data": [quantidade_finalizacoes[0], sum(quantidade_finalizacoes)],  # Finalização certa / errada
            "labels": ["Certas", "Erradas"],
            "title": "Eficiência de Finalizações"
        },
        {
            "data": quantidade_desarmes,
            "labels": tipos_desarmes ,
            "title": "Distribuição de Desarmes"
        },
        {
            "data": quantidade_percas_posse,
            "labels":  percas_de_posse,
            "title": "Distribuição de Perdas de Posse"
        }
    ]
    
    return dados_grafico_pizza

def pizza_plot(dados_grafico_pizza):
    # Criar uma lista de figuras do Plotly
    figs = []

    # Iterar sobre os dados e gerar gráficos de pizza
    for dado in dados_grafico_pizza:
        data = dado["data"]
        labels = dado["labels"]
        title = dado["title"]

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=data,
            textinfo="percent+value",  # Exibir porcentagem e valor absoluto
            pull=[0.1] * len(labels),  # Se quiser destacar um pedaço, use esse parâmetro
            marker=dict(line=dict(color="white", width=1)),  # Bordas brancas
        )])
        
        fig.update_layout(
            title=title,
            showlegend=True
        )
        
        # Adicionar a figura gerada à lista de figuras
        figs.append(fig)
    
    return figs
def calcular_quadrante(x, y):
    
    num_colunas = 3
    num_linhas = 6
    width_quadrante = 280 / num_colunas
    height_quadrante = 470 / num_linhas
    # Encontrar a coluna (1 a 3)
    coluna = (x // width_quadrante) + 1
    # Encontrar a linha (1 a 6)
    linha = (y // height_quadrante) + 1
    return f"{linha}-{coluna}"

def extrair_dataframe_jogador(db_manager):
    dados_jogador = db_manager.listar_dados_analise_individual()
    dados_jogador_df = pd.DataFrame(dados_jogador, columns=["jogo_id","equipe_mandante_nome","equipe_visitante_nome","fase","rodada","competicao","jogador_nome","jogada","tempo","x_loc","y_loc"])
    dados_jogador_df["partida"] = dados_jogador_df.apply(
        lambda row: f"{row['equipe_mandante_nome']} x {row['equipe_visitante_nome']} - {row['competicao']} - {row['fase']} - {row['rodada']}",
        axis=1
    ) 
    dados_jogador_df['quadrante'] = dados_jogador_df.apply(lambda row: calcular_quadrante(row['x_loc'], row['y_loc']), axis=1)
    
    return dados_jogador_df

def extrair_estatisticas_jogadores(dados_jogador_df):
    
    primeiro_tempo=dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    estatiscas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo})
    estatiscas_jogadores_df["Total"] = estatiscas_jogadores_df["1ºT"] + estatiscas_jogadores_df["2ºT"]
    estatiscas_jogadores_df.loc['FIN.TOTAL'] = estatiscas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()


    return estatiscas_jogadores_df

def extrair_estatisticas_gerais(dados_jogador_df):
    
    primeiro_tempo=dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    estatisticas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo})
    estatisticas_jogadores_df["Total"] = estatisticas_jogadores_df["1ºT"] + estatisticas_jogadores_df["2ºT"]
    estatisticas_jogadores_df.loc['FIN.TOTAL'] = estatisticas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()
    
    estatisticas_primeiro_tempo_dict = estatisticas_jogadores_df["1ºT"].to_dict()
    estatisticas_segundo_tempo_dict = estatisticas_jogadores_df["2ºT"].to_dict()
    estatisticas_totais_dict = estatisticas_jogadores_df["Total"].to_dict()
    
    return estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict 


def extrair_estatisticas_localizacao(dados_jogador_df,jogada):
    primeiro_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '1ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    segundo_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '2ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    total = primeiro_tempo + segundo_tempo
    
    localizacao_jogadas = {
        "Primeiro Tempo": primeiro_tempo,
        "Segundo Tempo" : segundo_tempo,
        "Total": total
    }
    
    return localizacao_jogadas
    
def plotar_estatisticas_gerais_time(estatisticas_totais_dict,numero_jogos):
    estatisticas_gerais_fig = go.Figure()

    if estatisticas_totais_dict['FIN.TOTAL'] == 0:
        efetividade = 0
    else:
        efetividade = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL']

    # Indicador 1: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'],
        domain={'row': 1, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))

    # Indicador 2: Finalizações
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.TOTAL'],
        domain={'row': 0, 'column': 1},
        title={"text": "Finalizações", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 3: Assistências
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=numero_jogos,
        domain={'row': 0, 'column': 0},
        title={"text": "Jogos", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 4: Efetividade
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 1, 'column': 1},
        title={"text": "Efetividade", "font": {"size": 12}}
    ))

    # Indicador 5: Participações em Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'] / numero_jogos if numero_jogos > 0 else 0,
        domain={'row': 2, 'column': 0},
        title={"text": "Gols por Jogo", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 6: Finalizações Certas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.C'],
        domain={'row': 2, 'column': 1},
        title={"text": "Fin. Certas", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 2, 'pattern': "independent"},
        template="plotly_dark",
        margin_t=20,
        margin_b= 0,
        height= 330
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig

        


def plotar_estatisticas_gerais(estatisticas_totais_dict):
    estatisticas_gerais_fig = go.Figure()

    if estatisticas_totais_dict['FIN.TOTAL'] == 0:
        efetividade = 0
    else:
        efetividade = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL']

    # Indicador 1: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'],
        domain={'row': 0, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))

    # Indicador 2: Finalizações
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.TOTAL'],
        domain={'row': 0, 'column': 1},
        title={"text": "Finalizações", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 3: Assistências
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['ASSIST.'],
        domain={'row': 1, 'column': 0},
        title={"text": "Assistências", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 4: Efetividade
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 1, 'column': 1},
        title={"text": "Efetividade", "font": {"size": 12}}
    ))

    # Indicador 5: Participações em Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'] + estatisticas_totais_dict['ASSIST.'],
        domain={'row': 2, 'column': 0},
        title={"text": "Participações em Gols", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 6: Finalizações Certas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.C'],
        domain={'row': 2, 'column': 1},
        title={"text": "Fin. Certas", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 2, 'pattern': "independent"},
        template="plotly_dark",
        margin_t=20,
        margin_b= 0,
        height= 330
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig

def plotar_estatisticas_gerais_1(estatisticas_totais_dict):
    estatisticas_gerais_fig = go.Figure()

    # Indicador 1: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['DES.C/P.'],
        domain={'row': 0, 'column': 0},
        title={"text": "Des. c/ Posse", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))

    # Indicador 2: Finalizações
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['DES.S/P.'],
        domain={'row': 0, 'column': 1},
        title={"text": "Des. s/ Posse", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 3: Assistências
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['PER.P'],
        domain={'row': 0, 'column': 2},
        title={"text": "Perda de Posse", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador 4: Efetividade
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['C.A'],
        number={"font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 0, 'column': 3},
        title={"text": "C.A Adiversário", "font": {"size": 12}}
    ))

   

    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 1, 'columns': 4, 'pattern': "independent"},
        template="plotly_dark",
        height= 100,
        margin_t = 105,
        margin_r=5
    
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig





def plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict):
    # Extração das estatísticas
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'DES.S/P.', 'PER.P']
    
    # Valores para o 1º e 2º tempo
    valores_1T = [estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict[categoria] for categoria in categorias]
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)', 
         'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)']


    # Criar a figura com 2 subgráficos (um para o 1º tempo e outro para o 2º tempo)
    fig = make_subplots(
        rows=1, cols=2,  # Definir a quantidade de linhas e colunas
        subplot_titles=('1º Tempo', '2º Tempo'),  # Títulos para os subgráficos
        shared_yaxes=True  # Eixo Y compartilhado para comparação
    )

    # Adicionar o gráfico de barras para o 1º Tempo no subgráfico (1, 1)
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores_1T,
        name='1º Tempo',
        marker_color=cores  # Cor para as barras do 1º tempo
    ), row=1, col=1)

    # Adicionar o gráfico de barras para o 2º Tempo no subgráfico (1, 2)
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores_2T,
        name='2º Tempo',
        marker_color=cores  # Cor para as barras do 2º tempo
    ), row=1, col=2)

    # Atualizar o layout para personalizar a aparência do gráfico
    fig.update_layout(
        title={
            'text': 'Comparação de Ações por Tempo',
            'x': 0.5,  # Centraliza o título
            'xanchor': 'center',  # Garante que o título fique centralizado
            'y': 0.95  # Distância do título do topo
        },
        xaxis_title='Tipo de Ação',
        yaxis_title='Quantidade',
        barmode='group',  # Agrupa as barras para comparação direta
        template='plotly_dark',  # Tema visual
        showlegend=False,  # Não mostra a legenda
        height=400,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=80)  # Ajuste do espaço superior para o título
    )

    return fig



def plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,numero_jogos):

    # Dados para os gráficos
    labels = ['Primeiro Tempo', 'Segundo Tempo']

    # Dados para cada gráfico
    data_finalizacoes =np.array([estatisticas_primeiro_tempo_dict['FIN.TOTAL'], estatisticas_segundo_tempo_dict['FIN.TOTAL']])
    data_desempenho_posse = np.array([estatisticas_primeiro_tempo_dict['DES.C/P.'], estatisticas_segundo_tempo_dict['DES.C/P.']])
    data_perda_posse = np.array([estatisticas_primeiro_tempo_dict['PER.P'], estatisticas_segundo_tempo_dict['PER.P']])
    
    mean_finalizacoes = (data_finalizacoes/numero_jogos).astype(int)
    mean_desempenho_posse=(data_desempenho_posse/numero_jogos).astype(int)
    mean_perda_posse =(data_perda_posse/numero_jogos).astype(int)

    # Criar subplots com 1 linha e 3 colunass
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=['Média de Finalizações', 'Média Des. c/ Posse', 'Média Perda de Posse']
    )

    # Adicionar gráficos de "rosca" (hole > 0)
    fig.add_trace(go.Pie(
        labels=labels, 
        values=mean_finalizacoes, 
        name="Finalizações", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 1)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=mean_desempenho_posse, 
        name="Des. c/ Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 2)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=mean_perda_posse, 
        name="Perda de Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 3)

    # Atualizar layout
    fig.update_layout(
        title_text="Histórico",
        title_x=0.4,  # Centraliza o título
        showlegend=True,
        legend=dict(
            x=0.5,  # Localização horizontal (0=esquerda, 1=direita)
            y=-0.2,  # Localização vertical (0=fundo, 1=topo)
            xanchor="center",  # Âncora horizontal
            yanchor="middle",  # Âncora vertical
            orientation="h"  # Orientação horizontal
        )
    )
    
    return fig

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plotar_historico_time(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, numero_jogos):
    # Labels para os gráficos
    labels = ['Primeiro Tempo', 'Segundo Tempo']

    # Dados a serem plotados
    categorias = {
        "Média Finalizações Certas": "FIN.C",
        "Média Finalizações Erradas": "FIN.E",
        "Média Finalizações Travadas": "FIN.T",
        "Média Des. c/ Posse": "DES.C/P.",
        "Média Des. s/ Posse": "DES.S/P.",
        "Média Perda de Posse": "PER.P",
    }

    # Criar subplots com 2 linhas e 3 colunas
    fig = make_subplots(
        rows=2, cols=3,  
        specs=[[{'type': 'domain'}] * 3, [{'type': 'domain'}] * 3],  # Define o tipo de gráfico como 'domain' (rosca)
        subplot_titles=list(categorias.keys())  # Define os títulos automaticamente
    )

    # Loop para adicionar os gráficos dinamicamente
    for i, (titulo, chave) in enumerate(categorias.items()):
        row = (i // 3) + 1  # Calcula a linha correta (1 ou 2)
        col = (i % 3) + 1    # Calcula a coluna correta (1, 2 ou 3)

        # Calcula a média (evita divisão por zero)
        valores = np.array([
            estatisticas_primeiro_tempo_dict[chave], 
            estatisticas_segundo_tempo_dict[chave]
        ])
        mean_valores = (valores / numero_jogos).astype(int) if numero_jogos > 0 else [0, 0]

        # Adiciona o gráfico ao subplot correspondente
        fig.add_trace(go.Pie(
            labels=labels,
            values=mean_valores,
            name=titulo,
            hole=0.5,
            textinfo='percent',
            texttemplate='%{value} (%{percent})'
        ), row=row, col=col)
    
    fig.update_annotations(
        font_size=14,  # Tamanho da fonte dos títulos
        xanchor="center",  # Centraliza horizontalmente
        yanchor="bottom",
        yshift=20# Ajusta a posição vertical
        
        # Move os títulos um pouco para baixo
    )
    
    # Atualizar layout do gráfico
    fig.update_layout(
        title_text="Histórico",
        title_x=0.45,  # Centraliza o título
        title_y = 0.98,
        showlegend=True,
        height=450,  # Ajusta a altura do gráfico
        legend=dict(
            x=0.5, y=-0.2, 
            xanchor="center", 
            yanchor="bottom", 
            orientation="h"
        )
    )

    return fig


def plotar_radar_chart(estatisticas_totais_dict, estatisticas_geral_totais_dict):
    # Dados para o gráfico
    theta = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'DES.S/P.', 'PER.P']
    
    numerador = [estatisticas_totais_dict[i] for i in theta]
    denominador = [estatisticas_geral_totais_dict[i] for i in theta]
    valores = [n / d if d != 0 else 0 for n, d in zip(numerador, denominador)]
    
    # Garantir que os valores formam um ciclo fechado (voltam ao primeiro ponto)
    valores.append(valores[0])

    # Criar o gráfico de radar
    fig = go.Figure()

    # Adicionar traço com os valores
    fig.add_trace(go.Scatterpolar(
        r=valores,  # Valores percentuais
        theta=theta + [theta[0]],  # Fechar o ciclo
        fill='toself',  # Preencher o gráfico
        name="Desempenho",
        text=[f"{v:.1f}%" for v in valores],  # Texto formatado em porcentagem
        hoverinfo="text",  # Mostrar apenas os textos no hover
    ))

    # Configurar layout do gráfico
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,  # Mostrar o eixo radial
                range=[0, 1.0],  # Definir o intervalo de 0 a 100%
                showticklabels=True,  # Mostrar rótulos das ticks
                tickvals=[0.2, 0.4, 0.6, 0.8, 1.0],  # Posicionar as ticks
                ticktext=["20%", "40%", "60%", "80%", "100%"],  # Rótulos personalizados
                tickformat="%",  # Formato dos valores em porcentagem
                tickangle=0,  # Alinhar os rótulos
            ),
        ),
        showlegend=False,
        template="plotly_dark"  # Tema visual
    )
    
    return fig

def create_arc(x_center, y_center, radius, theta1, theta2, color='gray', width=2):
    theta = np.linspace(np.radians(theta1), np.radians(theta2), 100)
    x = x_center + radius * np.cos(theta)
    y = y_center + radius * np.sin(theta)
    return dict(type='scatter', x=x, y=y, mode='lines', line=dict(color=color, width=width)), (x[0], y[0]), (x[-1], y[-1])

# Função principal para criar a quadra de futsal
def create_futsal_court(titulo,localizacao_jogadas):
  
    # Criar a figura
    fig = go.Figure()

    # Tamanho ajustado da quadra
    width = 280  # Comprimento da quadra
    height = 470  # Largura da quadra
    radius = 60  # Raio dos arcos ajustado

    # Adicionar a quadra
    # Área de gol inferior
    arc_left_bottom, left_bottom_start, left_bottom_end = create_arc(-30, 0, radius, 90, 180)
    arc_right_bottom, right_bottom_start, right_bottom_end = create_arc(30, 0, radius, 0, 90)

    fig.add_trace(arc_left_bottom)
    fig.add_trace(arc_right_bottom)

    # Linha inferior conectando os extremos dos arcos inferiores
    fig.add_shape(
        type='line',
        x0=-30, y0=radius,  # Usar 'left_bottom_end' como ponto de partida
        x1=30, y1=radius,  # Usar 'right_bottom_start' como ponto final
        line=dict(color='gray', width=2)
    )

    # Área de gol superior
    arc_left_top, left_top_start, left_top_end = create_arc(-30, height, radius, 180, 270)
    arc_right_top, right_top_start, right_top_end = create_arc(30, height, radius, 270, 360)

    fig.add_trace(arc_left_top)
    fig.add_trace(arc_right_top)

    # Linha superior conectando os extremos dos arcos superiores
    fig.add_shape(
        type='line',
        x0=left_top_end[0], y0=left_top_end[1],  # Usar 'left_top_end' como ponto de partida
        x1=right_top_start[0], y1=right_top_start[1],  # Usar 'right_top_start' como ponto final
        line=dict(color='gray', width=2)
    )

    # Linha central
    fig.add_shape(type='line', x0=-140, y0=height / 2, x1=140, y1=height / 2, line=dict(color='gray', width=2))

    # Círculo central
    radius_circle = 40
    theta = np.linspace(0, 2 * np.pi, 100)
    x_center_circle = radius_circle * np.cos(theta)
    y_center_circle = height / 2 + radius_circle * np.sin(theta)
    fig.add_trace(go.Scatter(x=x_center_circle, y=y_center_circle, mode='lines', line=dict(color='gray', width=2)))

    # Linhas externas (ajustadas para 280 x 470)
    fig.add_shape(type='rect', x0=-140, y0=0, x1=140, y1=height, line=dict(color='gray', width=2))

    # Adicionar as linhas pontilhadas para dividir a quadra em 3 colunas e 6 linhas
    # Linhas verticais (colunas)
    for i in range(1, 3):  # Para as 2 linhas verticais (entre as colunas)
        fig.add_shape(
            type='line',
            x0=-140 + (i * 93.33), y0=0,  # Calculando a posição das colunas
            x1=-140 + (i * 93.33), y1=height,
            line=dict(color='gray', width=2, dash='dot')  # Linha pontilhada
        )

    # Linhas horizontais (linhas)
    for i in range(1, 6):  # Para as 5 linhas horizontais
        fig.add_shape(
            type='line',
            x0=-140, y0=(i * 78.33),  # Calculando a posição das linhas horizontais
            x1=140, y1=(i * 78.33),
            line=dict(color='gray', width=2, dash='dot')  # Linha pontilhada
        )

    # Adicionar círculos superior e inferior entre a linha central e a linha de fundo
    radius_small_circle = 1.5
    y_position_upper = 117.5  # Posição Y para o círculo superior
    y_position_lower = 352.5  # Posição Y para o círculo inferior

    # Círculo superior
    x_small_circle_upper = radius_small_circle * np.cos(theta)
    y_small_circle_upper = y_position_upper + radius_small_circle * np.sin(theta)
    fig.add_trace(go.Scatter(x=x_small_circle_upper, y=y_small_circle_upper, mode='lines', fill='toself', 
                             line=dict(color='gray', width=2)))

    # Círculo inferior
    x_small_circle_lower = radius_small_circle * np.cos(theta)
    y_small_circle_lower = y_position_lower + radius_small_circle * np.sin(theta)
    fig.add_trace(go.Scatter(x=x_small_circle_lower, y=y_small_circle_lower, mode='lines', fill='toself', 
                             line=dict(color='gray', width=2)))

    # Adicionar anotações no meio de cada quadrante com o número de ações
    for quadrante, quantidade in localizacao_jogadas.items():
        # Extrair linha e coluna a partir do formato 'linha-coluna'
        try:
            linha, coluna = map(float, quadrante.split('-'))
        except ValueError:
            print(f"Erro ao processar o quadrante: {quadrante}")
            continue
        
        # Calcular o centro do quadrante
        x_pos = -140 + (coluna - 1) * 93.33 + 46.67  # Posição x do centro do quadrante
        y_pos = height - (linha - 1) * 78.33 - 39.17
  # Posição y do centro do quadrante

        # Adicionar anotação de texto no centro do quadrante
        fig.add_trace(go.Scatter(
            x=[x_pos], y=[y_pos],
            mode='text',
            text=[str(quantidade)],
            textposition='middle center',
            showlegend=False,
            textfont=dict(size=14, color='white')  # Correção: usar textfont ao invés de font
        ))

    fig.add_annotation(
            x=-180, y=400,  # Aumente o valor de y para subir a seta
            ax=0, ay=200,  # Ajuste ay para posicionar a ponta da seta
            showarrow=True,
            arrowhead=2,
            font=dict(size=14, color="white"),
            arrowcolor="white",
            textangle=90
        )
    
    # Ajustar layout
    fig.update_layout(
        title=dict(
            text=titulo,  # Texto do título
            x=0.5,        # Centraliza o título no eixo X
            xanchor='center',  # Âncora centralizada
            yanchor='top'      # Âncora no topo
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        width=350,
        height=550,
        showlegend=False,
        plot_bgcolor='#121212',  # Fundo escuro
        template="plotly_dark"
        )

    # Exibir a quadra
    return fig


def pegar_imagem_jogador(image_id):
    if image_id is not None:
        url = f"https://drive.google.com/uc?export=view&id={image_id}"
        response = requests.get(url)
        return response.content
    else:
        return None
    
def salvar_graficos_pdf(estatisticas_gerais_fig,estatisticas_gerais_fig_1,grafico_barras_fig,historico_fig,radar_fig):
    """
    Gera um arquivo PDF com gráficos Plotly e retorna como bytes para download.

    Parâmetros:
    - figuras (dict): Dicionário onde as chaves são os nomes dos gráficos e os valores são os objetos Plotly.

    Retorna:
    - pdf_bytes (BytesIO): Arquivo PDF em memória pronto para download.
    """
    
    figuras = {
    "estatisticas_gerais": estatisticas_gerais_fig,
    "estatisticas_gerais_1": estatisticas_gerais_fig_1,
    "grafico_barras": grafico_barras_fig,
    "historico": historico_fig,
    "radar": radar_fig
        }
    width, height = letter
    imagens_temp = []

    # Criar buffer de memória para armazenar o PDF
    pdf_buffer = io.BytesIO()

    # Salvar os gráficos como imagens temporárias
    for nome, figura in figuras.items():
        nome_imagem = f"{nome}.png"
        pio.write_image(figura, nome_imagem, format="png")
        imagens_temp.append(nome_imagem)

    # Criar o PDF no buffer
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    def add_image_to_pdf(canvas, img_path, y_position):
        img = Image.open(img_path)
        img_width, img_height = img.size
        aspect = img_width / img_height
        new_width = width - 50
        new_height = new_width / aspect
        if new_height > height - 50:
            new_height = height - 50
            new_width = new_height * aspect
        canvas.drawImage(img_path, 25, y_position, width=new_width, height=new_height)

    # Adicionar os gráficos ao PDF
    y_position = height - 250
    for img_path in imagens_temp:
        add_image_to_pdf(c, img_path, y_position)
        y_position -= 250
        if y_position < 50:
            c.showPage()
            y_position = height - 250

    c.save()
    
    # Mover o ponteiro do buffer para o início
    pdf_buffer.seek(0)

    # Remover imagens temporárias
    for img in imagens_temp:
        os.remove(img)

    return pdf_buffer