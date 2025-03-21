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
from PIL import Image
import os
from io import BytesIO


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
    
    percas_de_posse = ['PER.P.', 'C.A']
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
    
    primeiro_tempo=dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P.', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P.', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    estatiscas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo})
    estatiscas_jogadores_df["Total"] = estatiscas_jogadores_df["1ºT"] + estatiscas_jogadores_df["2ºT"]
    estatiscas_jogadores_df.loc['FIN.TOTAL'] = estatiscas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()


    return estatiscas_jogadores_df

def extrair_estatisticas_gerais(dados_jogador_df):
    
    primeiro_tempo=dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S"],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S"],fill_value=0)
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

    
    efetividade_finalizacoes = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL'] if estatisticas_totais_dict['FIN.TOTAL'] > 0 else 0
    efetividade_finalizacoes_certas = estatisticas_totais_dict['GOL'] / estatisticas_totais_dict['FIN.C'] if estatisticas_totais_dict['FIN.C'] > 0 else 0
    
     
     # Indicador 3: Jogos
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=numero_jogos,
        domain={'row': 0, 'column': 1},
        title={"text": "Jogos", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'],
        domain={'row': 1, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))
    
    # Indicador: Finalizações totais
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.TOTAL'],
        domain={'row': 1, 'column': 1},
        title={"text": "Fin.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador: Efetividade Fin.
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade_finalizacoes,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 1, 'column': 2},
        title={"text": "Efet.Fin.", "font": {"size": 12}}
    ))
    
    # Indicador: Gols/jogos
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'] / numero_jogos if numero_jogos > 0 else 0,
        domain={'row': 2, 'column': 0},
        title={"text": "Média Gols", "font": {"size": 12}},
        number={"font": {"size": 20}, "valueformat": ".1f"}
    ))
    
     # Indicador: Finalizações Certas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.C'],
        domain={'row': 2, 'column': 1},
        title={"text": "Fin.C.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador : Efetividade Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade_finalizacoes_certas,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 2, 'column': 2},
        title={"text": "Efet.Fin.C.", "font": {"size": 12}}
    ))

   
    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark",
        margin_t=7,
        margin_b= 0,
        height= 180,
        margin_l=10,
        margin_r=10
        
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig

        


def plotar_estatisticas_gerais(estatisticas_totais_dict,numero_jogos):
    estatisticas_gerais_fig = go.Figure()

    efetividade_finalizacoes = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL'] if estatisticas_totais_dict['FIN.TOTAL'] > 0 else 0
    efetividade_finalizacoes_certas = estatisticas_totais_dict['GOL'] / estatisticas_totais_dict['FIN.C'] if estatisticas_totais_dict['FIN.C'] > 0 else 0
     
     # Indicador 3: Jogos
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=numero_jogos,
        domain={'row': 0, 'column': 1},
        title={"text": "Jogos", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL'],
        domain={'row': 1, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))
    
    # Indicador: Finalizações totais
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.TOTAL'],
        domain={'row': 1, 'column': 1},
        title={"text": "Fin.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador: Efetividade Fin.
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade_finalizacoes,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 1, 'column': 2},
        title={"text": "Efet.Fin.", "font": {"size": 12}}
    ))
    
    # Indicador: Assist
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['ASSIST.'],
        domain={'row': 2, 'column': 0},
        title={"text": "Assist.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))
    
     # Indicador: Finalizações Certas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.C'],
        domain={'row': 2, 'column': 1},
        title={"text": "Fin.C.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))

    # Indicador : Efetividade Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade_finalizacoes_certas,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 2, 'column': 2},
        title={"text": "Efet.Fin.C.", "font": {"size": 12}}
    ))

   
    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark",
        margin_t=7,
        margin_b= 0,
        height= 180,
        margin_l=10,
        margin_r=10
        
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig

def plotar_estatisticas_gerais_1(estatisticas_totais_dict):
    estatisticas_gerais_fig = go.Figure()
    
    percentual_perda_de_posse = (
    estatisticas_totais_dict['C.A.-Contra'] / estatisticas_totais_dict['PER.P.'] 
    if estatisticas_totais_dict['PER.P.'] > 0 else 0
                                    )

    efetividade_desarme_com_posse = (
    estatisticas_totais_dict['C.A.-Pró'] / estatisticas_totais_dict['DES.C/P.'] 
    if estatisticas_totais_dict['DES.C/P.'] > 0 else 0
                                                            )

    # Indicador: DES.C/P
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['DES.C/P.'],
        domain={'row': 0, 'column': 0},
        title={"text": "Des.C/P.", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))
    
    # Indicador: C.A.-Pró
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['C.A.-Pró'],
        domain={'row': 1, 'column': 0},
        title={"text": "C.A. - Pró", "font": {"size": 12}},  # Tamanho do título
        number={"font": {"size": 20}}  # Tamanho do valor
    ))
    # Indicador: Efetividade desarme com posse
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade_desarme_com_posse,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 2, 'column': 0},
        title={"text": "Efetividade", "font": {"size": 12}}
    ))
        
    # Indicador: Desarme sem posse
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['DES.S/P.'],
        domain={'row': 1, 'column': 1},
        title={"text": "Des.S/P.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))
    # Indicador: Perda de posse
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['PER.P.'],
        domain={'row': 0, 'column': 2},
        title={"text": "Per.P.", "font": {"size": 12}},
        number={"font": {"size": 20}}
    ))  
    # Indicador: C.A. Contra
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['C.A.-Contra'],
        number={"font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 1, 'column': 2},
        title={"text": "C.A Sofrido", "font": {"size": 12}}
    ))

   # Indicador: Percentual C.A. sofrido
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=percentual_perda_de_posse,
        number={"valueformat": ".0%", "font": {"size": 20}},  # Formato e tamanho do valor
        domain={'row': 2, 'column': 2},
        title={"text": "Percentual", "font": {"size": 12}}
    ))

    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark",
        height= 270,
        margin_t = 20,
        margin_r=5,
    
        # Opcional: tema do gráfico
    )

    return estatisticas_gerais_fig





def plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,mean_primeiro_tempo, mean_segundo_tempo):
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S"]
    
    # Valores para o 1º e 2º tempo
    valores_1T = [estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict[categoria] for categoria in categorias]
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)', 
         'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)','rgba(0, 255, 255, 0.6)' ]


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
        marker_color=cores,
        text=valores_1T,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")# Cor para as barras do 1º tempo
    ), row=1, col=1)

    # Adicionar o gráfico de barras para o 2º Tempo no subgráfico (1, 2)
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores_2T,
        name='2º Tempo',
        marker_color=cores,
        text=valores_2T,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")# Cor para as barras do 2º tempo
    ), row=1, col=2)
    
    #Adicionar média
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean_primeiro_tempo,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_primeiro_tempo],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Primeiro Tempo"  # Nome da legenda
        
    ),row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean_segundo_tempo,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_segundo_tempo],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Segundo Tempo"  # Nome da legenda
        
    ),row=1, col=2)    
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
        height=450,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=80)  # Ajuste do espaço superior para o título
    )

    return fig

def plotar_grafico_barras_jogador(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,mean_primeiro_tempo, mean_segundo_tempo):
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']
    
    # Valores para o 1º e 2º tempo
    valores_1T = [estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict[categoria] for categoria in categorias]
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)', 
         'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)' ]


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
        marker_color=cores,
        text=valores_1T,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")# Cor para as barras do 1º tempo
    ), row=1, col=1)

    # Adicionar o gráfico de barras para o 2º Tempo no subgráfico (1, 2)
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores_2T,
        name='2º Tempo',
        marker_color=cores,
        text=valores_2T,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")# Cor para as barras do 2º tempo
    ), row=1, col=2)
    
    #Adicionar média
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean_primeiro_tempo,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_primeiro_tempo],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Primeiro Tempo"  # Nome da legenda
        
    ),row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean_segundo_tempo,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_segundo_tempo],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Segundo Tempo"  # Nome da legenda
        
    ),row=1, col=2)    
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
        height=450,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=80)  # Ajuste do espaço superior para o título
    )

    return fig

def plotar_grafico_barras_parcial(estatisticas_parciais_dict,mean):
    # Extração das estatísticas
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S"]
    
    # Valores para o 1º e 2º tempo
    valores = np.array([estatisticas_parciais_dict[categoria] for categoria in categorias])
   
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)','rgba(0, 255, 255, 0.6)']


    fig = go.Figure()
    # Adicionar o gráfico de barras 
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=valores,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")     
    ))
    
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=9, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média"  # Nome da legenda
        
    ))

    
    # Atualizar o layout para personalizar a aparência do gráfico
    fig.update_layout(
        title={
            'text': 'Ações',
            'x': 0.5,  # Centraliza o título
            'xanchor': 'center',  # Garante que o título fique centralizado
            'y': 0.95  # Distância do título do topo
        },
        xaxis_title='Tipo de Ação',
        yaxis_title='Quantidade',
        barmode='group',  # Agrupa as barras para comparação direta
        template='plotly_dark',  # Tema visual
        showlegend=False,  # Não mostra a legenda
        height=450,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=60)  # Ajuste do espaço superior para o título
    )

    return fig

def plotar_grafico_barras_parcial_jogador(estatisticas_parciais_dict,mean):
    # Extração das estatísticas
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']
    
    # Valores para o 1º e 2º tempo
    valores = np.array([estatisticas_parciais_dict[categoria] for categoria in categorias])
   
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)']


    fig = go.Figure()
    # Adicionar o gráfico de barras 
    fig.add_trace(go.Bar(
        x=categorias,
        y=valores,
        marker_color=cores,
        text=valores,  
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color="black")     
    ))
    
    fig.add_trace(go.Scatter(
        x=categorias,
        y=mean,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média"  # Nome da legenda
        
    ))

    
    # Atualizar o layout para personalizar a aparência do gráfico
    fig.update_layout(
        title={
            'text': 'Ações',
            'x': 0.5,  # Centraliza o título
            'xanchor': 'center',  # Garante que o título fique centralizado
            'y': 0.95  # Distância do título do topo
        },
        xaxis_title='Tipo de Ação',
        yaxis_title='Quantidade',
        barmode='group',  # Agrupa as barras para comparação direta
        template='plotly_dark',  # Tema visual
        showlegend=False,  # Não mostra a legenda
        height=450,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=60)  # Ajuste do espaço superior para o título
    )

    return fig


def plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,numero_jogos):

    # Dados para os gráficos
    labels = ['Primeiro Tempo', 'Segundo Tempo']

    # Dados para cada gráfico
    data_finalizacoes =np.array([estatisticas_primeiro_tempo_dict['FIN.TOTAL'], estatisticas_segundo_tempo_dict['FIN.TOTAL']])
    data_desempenho_posse = np.array([estatisticas_primeiro_tempo_dict['DES.C/P.'], estatisticas_segundo_tempo_dict['DES.C/P.']])
    data_perda_posse = np.array([estatisticas_primeiro_tempo_dict['PER.P.'], estatisticas_segundo_tempo_dict['PER.P.']])
    
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
        texttemplate='%{value} (%{percent})',
        rotation=180,
        sort=False,
    ), 1, 1)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=mean_desempenho_posse, 
        name="Des. c/ Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})',
        rotation=180,
        sort=False,
    ), 1, 2)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=mean_perda_posse, 
        name="Perda de Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})',
        rotation=180,
        sort=False,  
        textposition="inside",
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
        "Média Perda de Posse": "PER.P.",
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
            texttemplate='%{value} (%{percent})',
            rotation=180,
            sort=False,
            textposition="inside"
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
        title_x=0.45,  # Centraliza o   
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
    theta = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'DES.S/P.', 'PER.P.']
    
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
def create_futsal_court(titulo, heatmap_data, line_color='white'):
    fig = go.Figure()
    width, height, radius = 280, 470, 60
    heatmap_data = np.array(heatmap_data).reshape(6,3)
    heatmap_data = np.flipud(heatmap_data)

    # Adicionar arcos
    arc_left_bottom, left_bottom_start, left_bottom_end = create_arc(-30, 0, radius, 90, 180, line_color, 2)
    arc_right_bottom, right_bottom_start, right_bottom_end = create_arc(30, 0, radius, 0, 90, line_color, 2)
    fig.add_trace(arc_left_bottom)
    fig.add_trace(arc_right_bottom)
    
    fig.add_shape(type='line', x0=-30, y0=radius, x1=30, y1=radius, line=dict(color=line_color, width=2))
    
    arc_left_top, left_top_start, left_top_end = create_arc(-30, height, radius, 180, 270, line_color, 2)
    arc_right_top, right_top_start, right_top_end = create_arc(30, height, radius, 270, 360, line_color, 2)
    fig.add_trace(arc_left_top)
    fig.add_trace(arc_right_top)
    
    fig.add_shape(type='line', x0=left_top_end[0], y0=left_top_end[1], x1=right_top_start[0], y1=right_top_start[1], line=dict(color=line_color, width=2))
    fig.add_shape(type='line', x0=-140, y0=height / 2, x1=140, y1=height / 2, line=dict(color=line_color, width=2))
    
    # Círculo central
    radius_circle = 40
    theta = np.linspace(0, 2 * np.pi, 100)
    x_center_circle = radius_circle * np.cos(theta)
    y_center_circle = height / 2 + radius_circle * np.sin(theta)
    fig.add_trace(go.Scatter(x=x_center_circle, y=y_center_circle, mode='lines', line=dict(color=line_color, width=2)))
    
    fig.add_shape(type='rect', x0=-140, y0=0, x1=140, y1=height, line=dict(color=line_color, width=2))
    
    # Criar Heatmap
    x_edges = np.linspace(-140, 140, 4)  # 3 colunas
    y_edges = np.linspace(0, 470, 7)  # 6 linhas
    
    x_heatmap = [(x_edges[i] + x_edges[i + 1]) / 2 for i in range(len(x_edges) - 1)]
    y_heatmap = [(y_edges[i] + y_edges[i + 1]) / 2 for i in range(len(y_edges) - 1)]
    
    custom_colorscale = [[0.0, "green"], [0.33, "yellow"], [0.66, "orange"], [1.0, "red"]]
    
    heatmap_trace = go.Heatmap(
    z=heatmap_data,
    x=x_heatmap,
    y=y_heatmap,
    colorscale=custom_colorscale,  
    opacity=0.6,  
    zmin=0,  
    zmax=np.max(heatmap_data),  
    showscale=False,
    text=heatmap_data.astype(str),  # Mostra os valores
    texttemplate="%{text}",  # Define o formato dos textos
    textfont={"size": 17, "color": "white"}  # Ajusta o tamanho e cor dos textos
)
    
    fig.add_trace(heatmap_trace)
    
    fig.update_layout(
        title=dict(text=titulo, x=0.5, xanchor='center', yanchor='top'),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        showlegend=False,
        plot_bgcolor='#121212',
        template="plotly_dark",
        height=250,
        margin_t=10,
        margin_b= 10,

    )
    
    return fig


def pegar_imagem_jogador(image_id):
    if not image_id:
        return None
    
    # URL direta para imagens no Google Drive
    url = f"https://drive.google.com/uc?id={image_id}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Verifica erros HTTP
        
        # Verifica se o conteúdo é uma imagem
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            print(f"Conteúdo não é uma imagem. Tipo: {content_type}")
            return None
        
        # Tenta abrir a imagem com Pillow para validar o formato
        try:
            Image.open(BytesIO(response.content)).verify()
        except Exception as e:
            print(f"Imagem inválida: {e}")
            return None
            
        return response.content
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar imagem: {e}")
        return None


def get_team_total_figures(estatisticas_totais_dict,estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,numero_jogos,mean_primeiro_tempo, mean_segundo_tempo):
    
    estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_totais_dict,numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_totais_dict)
    grafico_barras_fig = plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,mean_primeiro_tempo, mean_segundo_tempo)
        
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig
    
def get_team_partial_figures(estatisticas_parciais_dict,numero_jogos,mean):
    
    estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_parciais_dict,numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_parciais_dict)
    grafico_barras_fig = plotar_grafico_barras_parcial(estatisticas_parciais_dict,mean)
    
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig    
    
    
def get_mean(df):
    
    numero_jogos = int(df["jogo_id"].nunique()) 
    estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_totais_dict= extrair_estatisticas_gerais(df)
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S"]
    
    valores_totais = np.array([estatisticas_totais_dict[categoria] for categoria in categorias])
    mean_total = valores_totais/numero_jogos
    
    valores_primeiro_tempo = np.array([estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias])
    mean_primeiro_tempo = valores_primeiro_tempo/numero_jogos
    
    valores_segundo_tempo = np.array([estatisticas_segundo_tempo_dict[categoria] for categoria in categorias])
    mean_segundo_tempo = valores_segundo_tempo/numero_jogos
    
    
    return mean_primeiro_tempo, mean_segundo_tempo,mean_total



def get_athletes_total_figures(estatisticas_totais_dict,estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_geral_totais_dict,numero_jogos,mean_primeiro_tempo, mean_segundo_tempo):
    
    estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_totais_dict,numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_totais_dict)
    grafico_barras_fig = plotar_grafico_barras_jogador(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,mean_primeiro_tempo, mean_segundo_tempo,)
    radar_fig = plotar_radar_chart(estatisticas_totais_dict,estatisticas_geral_totais_dict)

    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig,radar_fig
    
def get_athletes_partial_figures(estatisticas_parciais_dict,estatisticas_geral_parciais_dict,numero_jogos,mean):
    
    estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_parciais_dict,numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_parciais_dict)
    grafico_barras_fig = plotar_grafico_barras_parcial_jogador(estatisticas_parciais_dict,mean)
    radar_fig = plotar_radar_chart(estatisticas_parciais_dict,estatisticas_geral_parciais_dict)
    
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig,radar_fig 
    
    
def get_plots_plays_localization_team(filtro_jogada,data,tempo):
    
    
    jogadas= {"Ataque":['FIN.C', 'FIN.E', 'FIN.T'], "Defesa":['DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra','FIN.S']}
    jogadas = jogadas[filtro_jogada]
    figs=[]
    
    for jogada in jogadas:
        localizacao_jogadas = extrair_estatisticas_localizacao(data,jogada)
        fig = create_futsal_court(jogada,localizacao_jogadas[tempo])
        figs.append(fig)
        
    
    
    return figs

def get_plots_plays_localization_athletes(filtro_jogada,data,tempo):
    
    
    jogadas= {"Ataque":['FIN.C', 'FIN.E', 'FIN.T'], "Defesa":['DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']}
    jogadas = jogadas[filtro_jogada]
    figs=[]
    
    for jogada in jogadas:
        localizacao_jogadas = extrair_estatisticas_localizacao(data,jogada)
        fig = create_futsal_court(jogada,localizacao_jogadas[tempo])
        figs.append(fig)
        
    
    
    return figs
   
    
    
def create_futsal_subplots(tipo, data, tempo, rows, cols):
    titulos = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T'], "Defesa": ['DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']}
    titulos = titulos[tipo]
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titulos)

    for i, titulo in enumerate(titulos):
        row = (i // cols) + 1
        col = (i % cols) + 1
        heatmap_data = extrair_estatisticas_localizacao(data, titulo)
        court_fig = create_futsal_court(titulo, heatmap_data[tempo])
        for trace in court_fig.data:
            fig.add_trace(trace, row=row, col=col)
        for shape in court_fig.layout.shapes:
            fig.add_shape(shape, row=row, col=col)

        # Atualizar os eixos x e y para cada subplot
        # fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1, row=row, col=col)
        fig.update_xaxes(visible=False, row=row, col=col)

    fig.update_layout(
        # height=rows * 350,
        showlegend=False,
        plot_bgcolor='#121212',
        template="plotly_dark",
        yaxis=dict(visible=False),
        yaxis2=dict(visible=False, scaleanchor="x", scaleratio=1),
        yaxis3=dict(visible=False, scaleanchor="x", scaleratio=1)


    )

    return fig
