import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.tools import mpl_to_plotly
import io

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


def extrair_dataframe_jogador(db_manager):
    dados_jogador = db_manager.listar_dados_analise_individual()
    dados_jogador_df = pd.DataFrame(dados_jogador, columns=["jogo_id","equipe_mandante_nome","equipe_visitante_nome","fase","rodada","competicao","jogador_nome","jogada","tempo","x_loc","y_loc"])
    dados_jogador_df["partida"] = dados_jogador_df.apply(
        lambda row: f"{row['equipe_mandante_nome']} x {row['equipe_visitante_nome']} - {row['competicao']} - {row['fase']} - {row['rodada']}",
        axis=1
    ) 
    
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


def plotar_estatisticas_gerais(estatisticas_totais_dict):
    
    estatisticas_gerais_fig = go.Figure()
    
    if estatisticas_totais_dict['FIN.TOTAL'] == 0:
        efetividade = 0
    else:
        efetividade = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL']
    # Indicador 1: Finalizações Certas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",  # Apenas o número será exibido
        value=estatisticas_totais_dict['GOL'],  # Valor do indicador
        domain={'row': 0, 'column': 0},  # Posição no grid
        title={"text": "Gols"}))  # Título

    # Indicador 2: Finalizações Erradas
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.TOTAL'],
        domain={'row': 0, 'column': 1},
        title={"text": "Finalizações"}))

    # Indicador 3: Gols
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['ASSIST.'],
        domain={'row': 1, 'column': 0},
        title={"text": "Assistências"}))

    # Indicador 4: Assistências
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=efetividade,
        number={"valueformat": ".0%", "suffix": ""},
        domain={'row': 1, 'column': 1},
        title={"text": "Efetividade"}))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['GOL']+estatisticas_totais_dict['ASSIST.'],
        domain={'row': 2, 'column': 0},
        title={"text": "Participações em Gols"}))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number",
        value=estatisticas_totais_dict['FIN.C'],
        domain={'row': 2, 'column': 1},
        title={"text": "Fin. Certas"}))

    # Configuração do layout
    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 2, 'pattern': "independent"},  # Grid 2x2
        template="plotly_dark"  # Opcional: tema do gráfico
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



def plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict):

    # Dados para os gráficos
    labels = ['Primeiro Tempo', 'Segundo Tempo']

    # Dados para cada gráfico
    data_finalizacoes = [estatisticas_primeiro_tempo_dict['FIN.TOTAL'], estatisticas_segundo_tempo_dict['FIN.TOTAL']]
    data_desempenho_posse = [estatisticas_primeiro_tempo_dict['DES.C/P.'], estatisticas_segundo_tempo_dict['DES.C/P.']]
    data_perda_posse = [estatisticas_primeiro_tempo_dict['PER.P'], estatisticas_segundo_tempo_dict['PER.P']]

    # Criar subplots com 1 linha e 3 colunas
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=['Média de Finalizações', 'Média Des. c/ Posse', 'Média Perda de Posse']
    )

    # Adicionar gráficos de "rosca" (hole > 0)
    fig.add_trace(go.Pie(
        labels=labels, 
        values=data_finalizacoes, 
        name="Finalizações", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 1)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=data_desempenho_posse, 
        name="Des. c/ Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 2)

    fig.add_trace(go.Pie(
        labels=labels, 
        values=data_perda_posse, 
        name="Perda de Posse", 
        hole=0.5, 
        textinfo='percent',
        texttemplate='%{value} (%{percent})'
    ), 1, 3)

    # Atualizar layout
    fig.update_layout(
        title_text="Análise por Tempo",
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
