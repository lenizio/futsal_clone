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

def extrair_dataframe_analise_gols(db_manager):
    dados_analise_gols = db_manager.listar_gols()
    dados_analise_gols = pd.DataFrame(dados_analise_gols,columns=['id','jogo_id','Mandante', 'Visitante', 'Competição','Fase', 'Rodada',"Data", 'Equipe Analisada', 'Tipo','Característica','Tempo', 'Autor', 'Assistente', 'Jogadores em quadra','xloc','yloc'])
    dados_analise_gols =  dados_analise_gols.set_index('id')
    dados_analise_gols['quadrante'] = dados_analise_gols.apply(lambda row: calcular_quadrante(row['xloc'], row['yloc']), axis=1)
    dados_analise_gols.drop(['xloc','yloc'], inplace=True,axis=1)
    dados_analise_gols.fillna("",inplace=True)
    return dados_analise_gols
def extrair_estatisticas_jogadores(dados_jogador_df):
    
    primeiro_tempo=dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P.', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T",'DES.C/P.', 'DES.S/P.','PER.P.', 'C.A', 'ASSIST.', 'GOL'],fill_value=0)
    estatiscas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo})
    estatiscas_jogadores_df["Total"] = estatiscas_jogadores_df["1ºT"] + estatiscas_jogadores_df["2ºT"]
    estatiscas_jogadores_df.loc['FIN.TOTAL'] = estatiscas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()


    return estatiscas_jogadores_df

def extrair_estatisticas_gerais(dados_jogador_df):
    
    primeiro_tempo= dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"],fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"],fill_value=0)
    primeiro_tempo_prorrogacao= dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='1ºP'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"],fill_value=0)
    segundo_tempo_prorrogacao = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"]=='2ºP'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"],fill_value=0)

    estatisticas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo, "1ºP": primeiro_tempo_prorrogacao, "2ºP": segundo_tempo_prorrogacao})
    estatisticas_jogadores_df["Total"] = estatisticas_jogadores_df["1ºT"] + estatisticas_jogadores_df["2ºT"]
    estatisticas_jogadores_df.loc['FIN.TOTAL'] = estatisticas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()
    estatisticas_jogadores_df.loc['FIN.S.TOTAL'] = estatisticas_jogadores_df.loc[["FIN.S.C", "FIN.S.E", "FIN.S.T"]].sum()
    
    estatisticas_primeiro_tempo_dict = estatisticas_jogadores_df["1ºT"].to_dict()
    estatisticas_segundo_tempo_dict = estatisticas_jogadores_df["2ºT"].to_dict()
    estatisticas_totais_dict = estatisticas_jogadores_df["Total"].to_dict()
    estatisticas_pt_prorrogacao_dict = estatisticas_jogadores_df["1ºP"].to_dict()
    estatisticas_st_prorrogacao_dict = estatisticas_jogadores_df["2ºP"].to_dict()
    
    return estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict, estatisticas_pt_prorrogacao_dict, estatisticas_st_prorrogacao_dict 


def extrair_estatisticas_localizacao(dados_jogador_df,jogada):
    primeiro_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '1ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    segundo_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '2ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    total = primeiro_tempo + segundo_tempo
    primeiro_tempo_prorrogacao = dados_jogador_df[(dados_jogador_df["tempo"] == '1ºP') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    segundo_tempo_prorrogacao = dados_jogador_df[(dados_jogador_df["tempo"] == '2ºP') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(
    ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0'], fill_value=0)
    
    localizacao_jogadas = {
        "Primeiro Tempo": primeiro_tempo,
        "Segundo Tempo" : segundo_tempo,
        "Total": total,
        "Primeiro Tempo Prorrogação": primeiro_tempo_prorrogacao,
        "Segundo Tempo Prorrogação": segundo_tempo_prorrogacao
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
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"]
    
    # Valores para o 1º e 2º tempo
    valores_1T = [estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict[categoria] for categoria in categorias]
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)', 
         'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)','rgba(0, 255, 255, 0.6)' ]


    # Criar a figura com 2 subgráficos (um para o 1º tempo e outro para o 2º tempo)
    fig = make_subplots(
        rows=1, cols=2,  # Definir a quantidade de linhas e colunas
        subplot_titles=('1º Tempo', '2º Tempo'),  # Títulos para os subgráficos
        shared_yaxes=True , # Eixo Y compartilhado para comparação
        
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
        textfont=dict(color="black"),# Cor para as barras do 2º tempo
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
        name="Média Segundo Tempo",  # Nome da legenda
    
    
        
    ),row=1, col=2)    
    
   
    
    # Atualizar o layout para personalizar a aparência do gráfico
    fig.update_layout(
        title={
            'text': 'Comparação de Ações por Tempo',
            'x': 0.5,  # Centraliza o título
            'xanchor': 'center',  # Garante que o título fique centralizado
            'y': 0.95  # Distância do título do topo
        },
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
    categorias_ataque = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró']
    categorias_defesa =[ 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"]
    mean_ataque = [mean[i] for i in range(5)]
    mean_defesa = [mean[i] for i in range(5,11)]
    
    # Valores para o 1º e 2º tempo
    valores_ataque = np.array([estatisticas_parciais_dict[categoria] for categoria in categorias_ataque])
    valores_defesa= np.array([estatisticas_parciais_dict[categoria] for categoria in categorias_defesa])
    
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)','rgba(255, 165, 0, 1.0)','rgba(0, 255, 255, 0.6)']
    
    fig = make_subplots(
        rows=1, cols=2,  # Definir a quantidade de linhas e colunas
        subplot_titles=('Ataque', 'Defesa'),  # Títulos para os subgráficos
        shared_yaxes=True,
    )

    
    # Adicionar o gráfico de barras 
    
    fig.add_trace(go.Bar(
        x=categorias_ataque,
        y=valores_ataque,
        name='1º Tempo',
        marker_color=cores,
        text=valores_ataque,  
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(color="black")# Cor para as barras do 1º tempo
    ), row=1, col=1)

    # Adicionar o gráfico de barras para o 2º Tempo no subgráfico (1, 2)
    fig.add_trace(go.Bar(
        x=categorias_defesa,
        y=valores_defesa,
        name='2º Tempo',
        marker_color=cores,
        text=valores_defesa,  
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(color="black")# Cor para as barras do 2º tempo
    ), row=1, col=2)
    
    #Adicionar média
    fig.add_trace(go.Scatter(
        x=categorias_ataque,
        y=mean_ataque,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_ataque],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Ataque"  # Nome da legenda
        
    ),row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=categorias_defesa,
        y=mean_defesa,
        mode="lines+markers+text",  # Exibe linha, pontos e valores
        text=[f"{m:.2f}" for m in mean_defesa],  # Exibir valores da média
        textposition="top center",  # Posição dos valores da linha
        marker=dict(size=8, color="white"),  # Personaliza os pontos
        line=dict(width=2, color="cyan"),  # Personaliza a linha
        name="Média Defesa"  # Nome da legenda
        
    ),row=1, col=2)    
    
    
    
    # Atualizar o layout para personalizar a aparência do gráfico
    fig.update_layout(
       
        yaxis_title='Quantidade',
        barmode='group',  # Agrupa as barras para comparação direta
        template='plotly_dark',  # Tema visual
        showlegend=False,  # Não mostra a legenda
        height=450,  # Altura total da figura (ajustável conforme necessário)
        margin=dict(t=80)  # Ajuste do espaço superior para o título
    )

   

    
  
    return fig

def plotar_grafico_barras_parcial_1(estatisticas_parciais_dict,mean):
    # Extração das estatísticas
    
    # Categorias a serem usadas no gráfico
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']
    
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
        template="plotly_dark",  # Tema visual
        
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
    
    numero_jogos = int(df["jogo_id"].nunique()),
    numero_jogos_prorrogacao = int(df[df["tempo"] == "1ºP"]["jogo_id"].nunique())

    estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_totais_dict,estatisticas_pt_prorrogacao_dict, estatisticas_st_prorrogacao_dict= extrair_estatisticas_gerais(df)
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"]
    
    valores_totais = np.array([estatisticas_totais_dict[categoria] for categoria in categorias])
    mean_total = valores_totais/numero_jogos
    
    valores_primeiro_tempo = np.array([estatisticas_primeiro_tempo_dict[categoria] for categoria in categorias])
    mean_primeiro_tempo = valores_primeiro_tempo/numero_jogos
    
    valores_segundo_tempo = np.array([estatisticas_segundo_tempo_dict[categoria] for categoria in categorias])
    mean_segundo_tempo = valores_segundo_tempo/numero_jogos 
    
    valores_primeiro_tempo_prorrogacao = np.array([estatisticas_pt_prorrogacao_dict[categoria] for categoria in categorias])
    mean_primeiro_tempo_prorrogacao = valores_primeiro_tempo_prorrogacao/numero_jogos_prorrogacao if numero_jogos_prorrogacao != 0 else np.zeros((11,), dtype=int)

    
    valores_segundo_tempo_prorrogacao = np.array([estatisticas_st_prorrogacao_dict[categoria] for categoria in categorias])
    mean_segundo_tempo_prorrogacao = valores_segundo_tempo_prorrogacao/numero_jogos_prorrogacao if numero_jogos_prorrogacao != 0 else np.zeros((11,), dtype=int)
 
    
    
    return mean_primeiro_tempo, mean_segundo_tempo,mean_total,mean_primeiro_tempo_prorrogacao, mean_segundo_tempo_prorrogacao



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
    jogadas= {"Ataque":['FIN.C', 'FIN.E', 'FIN.T','DES.C/P.','C.A.-Pró'], "Defesa":[ 'DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"]}
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

def plotar_caracteristicas_gols(df_gols, equipe1, equipe2):
    jogos_e1,gols_marcados_e1, gols_sofridos_e1, jogos_e2,gols_marcados_e2, gols_sofridos_e2=extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2)
    
    labels = [
        "Total","4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]
    
    
    fig = go.Figure()
    # Dados para os gráficos
    values_gols_marcados = gols_marcados_e1.values
    total_gols_marcados = sum(values_gols_marcados)
    values_gols_marcados=np.insert(values_gols_marcados,0,total_gols_marcados)
    percentual_gols_marcados = values_gols_marcados/total_gols_marcados if total_gols_marcados != 0 else np.zeros((len(values_gols_marcados),), dtype=int)
    
    values_gols_sofridos = gols_sofridos_e2.values
    total_gols_sofridos = sum(values_gols_sofridos)
    values_gols_sofridos=np.insert(values_gols_sofridos,0,total_gols_sofridos)
    percentual_gols_sofridos = values_gols_sofridos/total_gols_sofridos if total_gols_sofridos != 0 else np.zeros((len(values_gols_sofridos),), dtype=int)
   
    fig.add_trace(go.Bar(
        y=labels,
        x=percentual_gols_sofridos,
        name=f'Gols Sofridos {equipe2}',
        orientation='h',
        text=[f"{v} ({(v/total_gols_sofridos)*100:.2f}%)" for v in values_gols_sofridos],
        textposition='inside',
        insidetextanchor='start',
        marker=dict(color='rgb(214, 39, 40)'),
        width=0.82, 
    ))

    fig.add_trace(go.Bar(
        y=labels,
        x= [-v for v in percentual_gols_marcados] ,
        name=f'Gols Marcados {equipe1}',
        orientation='h',
        text=[f"({(v/total_gols_marcados)*100:.2f}%) {v} " for v in values_gols_marcados],
        textposition='inside',
        insidetextanchor='start',
        marker=dict(color='rgb(44, 160, 44)'),
        width=0.82,
    ))


    titulo_esquerda = f'Gols Marcados {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2}(nº de jogos: {jogos_e2})'
    # Atualizar layout
    fig.update_layout(
        showlegend=False,
        barmode='relative',
        height=600,
        legend=dict(x=0.85),
        xaxis=dict(
            showgrid=True,        # Ativa o grid horizontal
            gridcolor='white',     # Cor da linha do grid
            gridwidth=0.5,
            tickvals=[-1,-0.5,0,0.5,1],
            ticktext=['100%', "50%",'0%',"50%",'100%'],
            range=[-1.03,1.03],
            tickfont=dict(size=15)
        ),
        yaxis=dict(
            showgrid=True,
            tickfont=dict(size=14)
                    ),
        annotations=[
        dict(
            text=titulo_esquerda,
            x=0.4, y=1.1,
            xref='paper', yref='paper',
            xanchor='right',  # texto se expande à direita
            yanchor='top',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        dict(
            text='X',
            x=0.5, y=1.1,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        dict(
            text=titulo_direita,
            x=0.6, y=1.1,
            xanchor='left',  # texto se expande à direita
            yanchor='top',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        
    ]

        )
        
    return fig

def plotar_caracteristicas_gols_1(df_gols, equipe1, equipe2):
    jogos_e1,gols_marcados_e1, gols_sofridos_e1, jogos_e2,gols_marcados_e2, gols_sofridos_e2=extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)
    total_gm_e1= int(gols_marcados_e1.sum())
    total_gs_e2=int(gols_sofridos_e2.sum())
    tempos = gols_marcados_e1.index.get_level_values(0).unique().tolist()
    labels = gols_marcados_e1.index.get_level_values(1).unique().tolist()
    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()
    tons_de_vermelho = ['#FF0000', '#CC0000', '#FF6666', '#990000', '#FF3333', '#E60000']
    tons_de_verde = ['#00FF00', '#00CC00', '#66FF66', '#009900', '#33FF33', '#00E600']
    data =[]
    for i,tempo in enumerate(tempos):
        valores = gols_marcados_e1.loc[tempo].values
        percentual = valores/total_gm_e1
        valores1 = gols_sofridos_e2.loc[tempo].values
        percentual1 = valores1/total_gs_e2
        cor = tons_de_vermelho[i % len(tons_de_vermelho)]
        cor1 = tons_de_verde[i % len(tons_de_verde)]
        data.append(
            go.Bar(
            name=f'{equipe1} - {tempo}',
            x=percentual,
            y=labels,
            offsetgroup=1,
            base = acumulado.copy(),
            orientation='h',
            text=[f"{valores[i]} ({(percentual[i]*100):.2f}%)" for i in range(len(valores))],
            textposition='inside',
            insidetextanchor='middle',  
            marker_color = cor,
            width=0.82, 
        )
        )
        data.append(
            go.Bar(
            name=f'{equipe2} - {tempo}',
            x=-percentual1,
            y=labels,
            offsetgroup=2,
            base = -acumulado1.copy(),
            orientation='h',
            text=[f"{valores1[i]} ({(percentual1[i]*100):.2f}%)" for i in range(len(valores1))],
            textposition='inside',
            insidetextanchor='middle',
            marker_color = cor1,
            width=0.822, 
        )
        )
        
        acumulado+=percentual
        acumulado1+=percentual1
    for i, tempo in enumerate(tempos):
        cor_vermelho_legenda = tons_de_vermelho[i % len(tons_de_vermelho)]
        cor_verde_legenda = tons_de_verde[i % len(tons_de_verde)]

        # Legenda para Equipe 1 (gols marcados)
        data.append(
            go.Bar(
                name=f'{equipe1} - {tempo}',
                x=[0],
                y=[None] * len(labels),
                marker_color=cor_vermelho_legenda,
                showlegend=True
            )
        )

        # Legenda para Equipe 2 (gols sofridos)
        data.append(
            go.Bar(
                name=f'{equipe2} - {tempo}',
                x=[0],
                y=[None] * len(labels),
                marker_color=cor_verde_legenda,
                showlegend=True
            )
        )
        
    titulo_esquerda = f'Gols Marcados {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2}(nº de jogos: {jogos_e2})'
    
    
    fig = go.Figure(
        
        data =data,
        layout=go.Layout(
        barmode='relative',
        showlegend=True,
        height=600,
        legend=dict(x=0.85),
        xaxis=dict(
            showgrid=True,        # Ativa o grid horizontal
            gridcolor='white',     # Cor da linha do grid
            gridwidth=0.5,
            tickfont=dict(size=14),
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=['100%', '50%', '0%', '50%', '100%'],
            range=[-1.03, 1.03],
        ),
        yaxis=dict(
            showgrid=True,
            tickfont=dict(size=13)
                    ),
        annotations=[
        dict(
            text=titulo_esquerda,
            x=0.4, y=1.1,
            xref='paper', yref='paper',
            xanchor='right',  # texto se expande à direita
            yanchor='top',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        dict(
            text='X',
            x=0.5, y=1.1,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        dict(
            text=titulo_direita,
            x=0.6, y=1.1,
            xanchor='left',  # texto se expande à direita
            yanchor='top',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20 ,family="Arial Black")
        ),
        
    ]

    ) 
        )
        
    return fig

def plotar_caracteristicas_gols_2(df_gols, equipe1, equipe2):
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)
    
    total_gm_e1 = int(gols_marcados_e1.sum())
    total_gs_e2 = int(gols_sofridos_e2.sum())
    
    tempos = gols_marcados_e1.index.get_level_values(0).unique().tolist()
    labels = gols_marcados_e1.index.get_level_values(1).unique().tolist()

    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()
    
    tons_sofridos = ['#800000', '#FF9999','#ff0000','#FF6666','#CC0000', '#E63939']

    tons_marcados =['#003300','#4dff4d', '#00A600','#b3ffb3', '#00CC00', '#39E639']
    
    data = []
    
    for i, tempo in enumerate(tempos):
        valores = gols_marcados_e1.loc[tempo].values 
        percentual = valores / total_gm_e1 if total_gm_e1 != 0 else np.zeros((len(valores),), dtype=int)
        valores1 = gols_sofridos_e2.loc[tempo].values
        percentual1 = valores1 / total_gs_e2 if total_gs_e2 != 0 else np.zeros((len(valores1),), dtype=int)
        
        cor_vermelho = tons_sofridos[i % len(tons_sofridos)]
        cor_verde = tons_marcados[i % len(tons_marcados)]
        
        #gols_sofridos
        data.append(go.Bar(
            name=f'{equipe2} - {tempo}',
            x=percentual1,
            y=labels,
            offsetgroup=1,
            base=acumulado1.copy(),
            orientation='h',
            text=[f"{valores1[i]} ({(percentual1[i]*100):.2f}%)" for i in range(len(valores1))],
            textposition='inside',
            insidetextanchor='middle',
            marker_color=cor_vermelho,
            width=0.82,
        ))
        
        #gol_marcados
        data.append(go.Bar(
            name=f'{equipe1} - {tempo}',
            x=-percentual,
            y=labels,
            offsetgroup=2,
            base=-acumulado.copy(),
            orientation='h',
            text=[f"({(percentual[i]*100):.2f}%) {valores[i]}" for i in range(len(valores))],
            textposition='inside',
            insidetextanchor='middle',
            marker_color=cor_verde,
            width=0.822,
        ))
        
        acumulado += percentual
        acumulado1 += percentual1
    
    # Títulos
    titulo_esquerda = f'Gols Marcados {equipe1} (nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2} (nº de jogos: {jogos_e2})'
    
    # Anotações existentes
    existing_annotations = [
        dict(
            text=titulo_esquerda,
            x=0.4, y=1.2,
            xref='paper', yref='paper',
            xanchor='right',
            yanchor='top',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        ),
        dict(
            text='X',
            x=0.5, y=1.2,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        ),
        dict(
            text=titulo_direita,
            x=0.6, y=1.2,
            xanchor='left',
            yanchor='top',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        )
    ]
    
    # Criar legenda personalizada
    legend_shapes = []
    legend_annotations = []
    
    # Configurações da legenda
    y_legend = 1.07
    x_start_esq = 0.10
    x_start_dir = 0.6
    delta_x = 0.053
    delta_shape = 0.05

    # Legenda ESQUERDA (equipe1) - Ordem invertida
    for i, tempo in enumerate(reversed(tempos)):  # Iterar em ordem reversa
        original_idx = len(tempos) - 1 - i  # Índice original para cores
        
        # # Bloco verde
        legend_shapes.append(dict(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x_start_esq + (i * delta_shape),
            y0=y_legend - 0.03,
            x1=x_start_esq + (i * delta_shape) + 0.05,
            y1=y_legend + 0.03,
            fillcolor=tons_marcados[original_idx % len(tons_marcados)],  # Usar índice original
            line=dict(width=0)
        ))
        
        # Texto
        legend_annotations.append(dict(
            xref="paper",
            yref="paper",
            x=x_start_esq + (i * delta_x) + 0.015,
            y=y_legend - 0.03,
            text=tempo,  # Já está invertido
            showarrow=False,
            font=dict(size=10),
            align="right"
        ))

    # Legenda DIREITA (equipe2) - Ordem normal
    for i, tempo in enumerate(tempos):
        # Bloco vermelho
        legend_shapes.append(dict(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x_start_dir + (i * delta_shape),
            y0=y_legend - 0.03,
            x1=x_start_dir + (i * delta_shape) + 0.05,
            y1=y_legend+0.03,
            fillcolor=tons_sofridos[i % len(tons_sofridos)],
            line=dict(width=0)
        ))
        
        # Texto
        legend_annotations.append(dict(
            xref="paper",
            yref="paper",
            x=x_start_dir + (i * delta_x) + 0.015,
            y=y_legend - 0.03,
            text=tempo,
            showarrow=False,
            font=dict(size=10),
            align="center"
        ))

    # Juntar todas as anotações
    all_annotations = existing_annotations + legend_annotations
    
    fig = go.Figure(
        data=data,
        layout=go.Layout(
            barmode='relative',
            showlegend=False,
            height=600,
            xaxis=dict(
                showgrid=True,
                gridcolor='white',
                gridwidth=0.5,
                tickfont=dict(size=14),
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['100%', '50%', '0%', '50%', '100%'],
                range=[-1.03, 1.03],
            ),
            yaxis=dict(
                showgrid=True,
                tickfont=dict(size=13)
            ),
            annotations=all_annotations,
            shapes=legend_shapes,
            margin=dict(r=150)  # Aumentar margem direita para caber a legenda
        )
    )
    
    return fig

def plotar_caracteristicas_gols_2_invertido(df_gols, equipe1, equipe2):
    # Extrair dados invertidos (sofridos para equipe1, marcados para equipe2)
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)
    
    # Totais invertidos
    total_gs_e1 = int(gols_sofridos_e1.sum())  # Total de gols sofridos pela equipe1
    total_gm_e2 = int(gols_marcados_e2.sum())  # Total de gols marcados pela equipe2
    
    tempos = gols_sofridos_e1.index.get_level_values(0).unique().tolist()
    labels = gols_sofridos_e1.index.get_level_values(1).unique().tolist()

    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()
    
    # Tons invertidos
    tons_sofridos = ['#800000', '#FF9999','#ff0000','#FF6666','#CC0000', '#E63939']  # Vermelhos (sofridos)
    tons_marcados = ['#003300','#4dff4d', '#00A600','#b3ffb3', '#00CC00', '#39E639']  # Verdes (marcados)
    
    data = []
    
    for i, tempo in enumerate(tempos):
        # Dados invertidos
        valores = gols_sofridos_e1.loc[tempo].values  # Sofridos equipe1
        percentual = valores / total_gs_e1 if total_gs_e1 != 0 else np.zeros((len(valores),), dtype=int)
        valores1 = gols_marcados_e2.loc[tempo].values  # Marcados equipe2
        percentual1 = valores1 / total_gm_e2 if total_gm_e2 != 0 else np.zeros((len(valores1),), dtype=int)
        
        cor_vermelho = tons_sofridos[i % len(tons_sofridos)]
        cor_verde = tons_marcados[i % len(tons_marcados)]
        
        # Barras invertidas
        data.append(go.Bar(
            name=f'{equipe1} - {tempo}',  # Sofridos
            x=-percentual,
            y=labels,
            offsetgroup=1,
            base=-acumulado.copy(),
            orientation='h',
            text=[f"{valores[i]} ({(percentual[i]*100):.2f}%)" for i in range(len(valores))],
            textposition='inside',
            insidetextanchor='middle',
            marker_color=cor_vermelho,  # Vermelho para sofridos
            width=0.82,
        ))
        
        data.append(go.Bar(
            name=f'{equipe2} - {tempo}',  # Marcados
            x=percentual1,
            y=labels,
            offsetgroup=2,
            base=acumulado1.copy(),
            orientation='h',
            text=[f"({(percentual1[i]*100):.2f}%) {valores1[i]}" for i in range(len(valores1))],
            textposition='inside',
            insidetextanchor='middle',
            marker_color=cor_verde,  # Verde para marcados
            width=0.822,
        ))
        
        acumulado += percentual
        acumulado1 += percentual1
    
    # Títulos invertidos
    titulo_esquerda = f'Gols Sofridos {equipe1} (nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Marcados {equipe2} (nº de jogos: {jogos_e2})'
    
    existing_annotations = [
        dict(
            text=titulo_esquerda,
            x=0.4, y=1.2,
            xref='paper', yref='paper',
            xanchor='right',
            yanchor='top',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        ),
        dict(
            text='X',
            x=0.5, y=1.2,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        ),
        dict(
            text=titulo_direita,
            x=0.6, y=1.2,
            xanchor='left',
            yanchor='top',
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=20, family="Arial Black")
        )
    ]
    
    # Legenda invertida
    legend_shapes = []
    legend_annotations = []
    
    y_legend = 1.07
    x_start_esq = 0.10
    x_start_dir = 0.6
    delta_x = 0.053
    delta_shape = 0.05

    # Legenda ESQUERDA (sofridos - vermelho)
    for i, tempo in enumerate(reversed(tempos)):
        original_idx = len(tempos) - 1 - i
        legend_shapes.append(dict(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x_start_esq + (i * delta_shape),
            y0=y_legend - 0.03,
            x1=x_start_esq + (i * delta_shape) + 0.05,
            y1=y_legend+ 0.03,
            fillcolor=tons_sofridos[original_idx % len(tons_sofridos)],
            line=dict(width=0)
        ))
        
        legend_annotations.append(dict(
            xref="paper",
            yref="paper",
            x=x_start_esq + (i * delta_x) + 0.015,
            y=y_legend - 0.03,
            text=tempo,
            showarrow=False,
            font=dict(size=10),
            align="right"
        ))

    # Legenda DIREITA (marcados - verde)
    for i, tempo in enumerate(tempos):
        legend_shapes.append(dict(
            type="rect",
            xref="paper",
            yref="paper",
            x0=x_start_dir + (i * delta_shape),
            y0=y_legend - 0.03,
            x1=x_start_dir + (i * delta_shape) + 0.05,
            y1=y_legend+ 0.03,
            fillcolor=tons_marcados[i % len(tons_marcados)],
            line=dict(width=0)
        ))
        
        legend_annotations.append(dict(
            xref="paper",
            yref="paper",
            x=x_start_dir + (i * delta_x) + 0.015,
            y=y_legend - 0.03,
            text=tempo,
            showarrow=False,
            font=dict(size=10),
            align="center"
        ))

    all_annotations = existing_annotations + legend_annotations
    
    fig = go.Figure(
        data=data,
        layout=go.Layout(
            barmode='relative',
            showlegend=False,
            height=600,
            xaxis=dict(
                showgrid=True,
                gridcolor='white',
                gridwidth=0.5,
                tickfont=dict(size=14),
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['100%', '50%', '0%', '50%', '100%'],
                range=[-1.03, 1.03],
            ),
            yaxis=dict(
                showgrid=True,
                tickfont=dict(size=13)
            ),
            annotations=all_annotations,
            shapes=legend_shapes,
            margin=dict(r=150)
        )
    )
    
    return fig

def plotar_caracteristicas_gols_invertido(df_gols, equipe1, equipe2):
    jogos_e1,gols_marcados_e1, gols_sofridos_e1,jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2)

    labels = [
        "Total","4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]
    
    fig = go.Figure()

    # Dados para o novo gráfico
    values_gols_sofridos_e1 = gols_sofridos_e1.values
    total_gols_sofridos_e1 = sum(values_gols_sofridos_e1)
    values_gols_sofridos_e1=np.insert(values_gols_sofridos_e1,0,total_gols_sofridos_e1)
    percentual_gols_sofridos_e1 = values_gols_sofridos_e1 / total_gols_sofridos_e1 if total_gols_sofridos_e1 != 0 else np.zeros((len(values_gols_sofridos_e1),), dtype=int)

    values_gols_marcados_e2 = gols_marcados_e2.values
    total_gols_marcados_e2 = sum(values_gols_marcados_e2)
    values_gols_marcados_e2=np.insert(values_gols_marcados_e2,0,total_gols_marcados_e2)
    percentual_gols_marcados_e2 = values_gols_marcados_e2 / total_gols_marcados_e2 if total_gols_marcados_e2 != 0 else np.zeros((len(values_gols_marcados_e2),), dtype=int)

    # Barras - Gols Sofridos (Equipe 1) à esquerda
    fig.add_trace(go.Bar(
        y=labels,
        x=[-v for v in percentual_gols_sofridos_e1],
        name=f'Gols Sofridos {equipe1}',
        orientation='h',
        text=[f"{v} ({(v/total_gols_sofridos_e1)*100:.2f}%)" for v in values_gols_sofridos_e1],
        textposition='inside',
        insidetextanchor='start',
        marker=dict(color='rgb(214, 39, 40)'),
        width=0.82
    ))

    # Barras - Gols Marcados (Equipe 2) à direita
    fig.add_trace(go.Bar(
        y=labels,
        x=percentual_gols_marcados_e2,
        name=f'Gols Marcados {equipe2}',
        orientation='h',
        text=[f"({(v/total_gols_marcados_e2)*100:.2f}%) {v}" for v in values_gols_marcados_e2],
        textposition='inside',
        insidetextanchor='start',
        marker=dict(color='rgb(44, 160, 44)'),
        width=0.82
    ))

    titulo_esquerda = f'Gols Sofridos {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Marcados {equipe2}(nº de jogos:{jogos_e2})'

    # Layout
    fig.update_layout(
        showlegend=False,
        barmode='relative',
        height=600,
        xaxis=dict(
            showgrid=True,
            gridcolor='white',
            gridwidth=0.5,
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=['100%', '50%', '0%', '50%', '100%'],
            range=[-1.03, 1.03],
            tickfont=dict(size=15)
        ),
        yaxis=dict(
            showgrid=True,
            tickfont=dict(size=14)
        ),
        annotations=[
            dict(
                text=titulo_esquerda,
                x=0.4, y=1.1,
                xref='paper', yref='paper',
                xanchor='right',
                yanchor='top',
                showarrow=False,
                font=dict(size=20, family="Arial Black")
            ),
            dict(
                text='X',
                x=0.5, y=1.1,
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=20, family="Arial Black")
            ),
            dict(
                text=titulo_direita,
                x=0.6, y=1.1,
                xref='paper', yref='paper',
                xanchor='left',
                yanchor='top',
                showarrow=False,
                font=dict(size=20, family="Arial Black")
            )
        ]
    )

    return fig

def extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2):
    # Lista de características padronizadas para reindexar
    caracteristicas_padrao = [
        "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]
    try:
        jogos_e1 =df_gols.loc[df_gols['Equipe Analisada']==equipe1]['jogo_id'].nunique()
    except Exception as e:
        jogos_e1 = 0    
    try:
        jogos_e2 =df_gols.loc[df_gols['Equipe Analisada']==equipe2]['jogo_id'].nunique()
    except Exception as e:
        jogos_e2 = 0    
    
    # Agrupamento
    df_gols_group = df_gols.groupby(['Equipe Analisada', 'Tipo', 'Característica'])['Tipo'].count()

    # Função auxiliar para acessar e reindexar
    def get_valor(df, chave):
        try:
            s = df.loc[chave]
        except KeyError:
            s = pd.Series(dtype=int)  # Series vazia se não encontrar
        return s.reindex(caracteristicas_padrao, fill_value=0)

    # Coleta e reindexação
    gols_marcados_e1 = get_valor(df_gols_group, (equipe1, "Marcado"))
    gols_sofridos_e1 = get_valor(df_gols_group, (equipe1, "Sofrido"))
    gols_marcados_e2 = get_valor(df_gols_group, (equipe2, "Marcado"))
    gols_sofridos_e2 = get_valor(df_gols_group, (equipe2, "Sofrido"))

    return jogos_e1,gols_marcados_e1, gols_sofridos_e1,jogos_e2, gols_marcados_e2, gols_sofridos_e2

def extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2):
    
    tempos =['1ºQ','2ºQ','3ºQ','4ºQ', '1ºP', '2ºP']
    caracteristicas_padrao = [
        "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]
    
    novo_index = pd.MultiIndex.from_product([tempos, caracteristicas_padrao], names=['Tempo', 'Característica'])

    try:
        jogos_e1 =df_gols.loc[df_gols['Equipe Analisada']==equipe1]['jogo_id'].nunique()
    except Exception as e:
        jogos_e1 = 0    
    try:
        jogos_e2 =df_gols.loc[df_gols['Equipe Analisada']==equipe2]['jogo_id'].nunique()
    except Exception as e:
        jogos_e2 = 0    
    
    # Agrupamento
    df_gols_group = df_gols.groupby(['Equipe Analisada', 'Tipo', 'Tempo','Característica'])['Tipo'].count()


    # Função auxiliar para acessar e reindexar
    def get_valor(df, chave):
        try:
            s = df.loc[chave]
        except KeyError:
            s = pd.Series(dtype=int)  # Series vazia se não encontrar
        return s.reindex(novo_index, fill_value=0)

    # Coleta e reindexação
    gols_marcados_e1 = get_valor(df_gols_group, (equipe1, "Marcado"))
    gols_sofridos_e1 = get_valor(df_gols_group, (equipe1, "Sofrido"))
    gols_marcados_e2 = get_valor(df_gols_group, (equipe2, "Marcado"))
    gols_sofridos_e2 = get_valor(df_gols_group, (equipe2, "Sofrido"))

    return jogos_e1,gols_marcados_e1, gols_sofridos_e1,jogos_e2, gols_marcados_e2, gols_sofridos_e2
    
    

def exibir_seta(direcao="↑"):
    """
    Exibe um indicador visual com uma seta e o texto "ATAQUE".

    Parâmetros:
        direcao (str): O símbolo da seta. Exemplo: "↑", "↓", "←", "→".
    """
    st.markdown(f"""
        <style>
            .container-ataque {{
                display: flex;
                flex-direction: column;
                align-items: center;
                margin: 80px 0;
                position: relative;
            }}
            
            .seta {{
                font-size: 50px;
                transform: translateX(-120px);  /* Ajuste fino da posição horizontal */
            }}
            
            .texto-ataque {{
                font-size: 20px;
                font-weight: bold;
                margin-top: -10px;  /* Espaço entre seta e texto */
                transform: translateX(-120px);  /* Alinhar com o ajuste da seta */
            }}
        </style>

        <div class="container-ataque">
            <div class="seta">{direcao}</div>
            <div class="texto-ataque">ATAQUE</div>
        </div>
        """, unsafe_allow_html=True)
