import pandas as pd
import streamlit as st
import numpy as np
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
    """Converte um DataFrame pandas para uma string CSV.

    Args:
        df (pd.DataFrame): O DataFrame a ser convertido.

    Returns:
        str: Uma string contendo os dados do DataFrame em formato CSV.
    """
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, encoding="utf-8", index=False)
    return csv_buffer.getvalue()


def listar_opcoes_jogadores(lista_jogadores):
    """
    Lista opções de jogadores e goleiros, organizando-os em dicionários e uma lista combinada.

    Args:
        lista_jogadores (list): Uma lista de tuplas, onde cada tupla representa um jogador
                                e contém informações como ID, nome, posição, etc.
                                Espera-se o formato: (id, nome, posicao, nome_completo, image_id).

    Returns:
        tuple: Uma tupla contendo:
            - dict: Um dicionário onde as chaves são os nomes completos dos jogadores
                    e os valores são listas [ID do jogador, ID da imagem].
            - list: Uma lista ordenada dos nomes completos dos jogadores.
    """
    opcoes_jogadores_dict = {}
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
    opcoes_jogadores_list = opcoes_goleiro_list + opcoes_jogadores_linha_list
    opcoes_jogadores_dict.update(opcoes_jogadores_linha_dict)

    return opcoes_jogadores_dict, opcoes_jogadores_list


def calcular_quadrante(x, y):
    """
    Calcula o quadrante de uma coordenada (x, y) dentro de uma quadra de futsal virtual.
    A quadra é dividida em 6 linhas e 3 colunas.

    Args:
        x (float): Coordenada X da jogada.
        y (float): Coordenada Y da jogada.

    Returns:
        str: Uma string no formato "linha-coluna" representando o quadrante.
    """
    num_colunas = 3
    num_linhas = 6
    width_quadrante = 280 / num_colunas
    height_quadrante = 470 / num_linhas
    coluna = (x // width_quadrante) + 1
    linha = (y // height_quadrante) + 1
    return f"{linha}-{coluna}"

def extrair_dataframe_jogador(db_manager):
    """
    Extrai e processa o DataFrame de dados de jogadas individuais de jogadores
    a partir do banco de dados. Adiciona uma coluna 'partida' e 'quadrante'.

    Args:
        db_manager (DBManager): Uma instância do gerenciador de banco de dados.

    Returns:
        pd.DataFrame: DataFrame contendo os dados das jogadas com as seguintes colunas:
        ["jogo_id", "equipe_mandante_nome", "equipe_visitante_nome", "fase", "rodada", "competicao","equipe_jogada_id", "equipe_jogada", "jogador_nome", "jogada", "tempo","partida","quadrante"]   .
    """
    dados_jogador = db_manager.listar_dados_analise_individual()
    dados_jogador_df = pd.DataFrame(dados_jogador, columns=["jogo_id", "equipe_mandante_nome", "equipe_visitante_nome", "fase", "rodada", "competicao","equipe_jogada_id", "equipe_jogada", "jogador_nome", "jogada", "tempo", "x_loc", "y_loc"])
    dados_jogador_df["partida"] = dados_jogador_df.apply(
        lambda row: f"{row['equipe_mandante_nome']} x {row['equipe_visitante_nome']} - {row['competicao']} - {row['fase']} - {row['rodada']}",
        axis=1
    )
    dados_jogador_df['quadrante'] = dados_jogador_df.apply(lambda row: calcular_quadrante(row['x_loc'], row['y_loc']), axis=1)
    return dados_jogador_df

def extrair_dataframe_analise_gols(db_manager):
    """
    Extrai e processa o DataFrame de dados de análise de gols a partir do banco de dados.
    Adiciona uma coluna 'quadrante' e remove 'xloc' e 'yloc'.

    Args:
        db_manager (DBManager): Uma instância do gerenciador de banco de dados.

    Returns:
        pd.DataFrame: DataFrame contendo os dados dos gols com colunas processadas.
    """
    dados_analise_gols = db_manager.listar_gols()
    dados_analise_gols = pd.DataFrame(dados_analise_gols, columns=['id', 'jogo_id', 'Mandante', 'Visitante', 'Competição', 'Fase', 'Rodada', "Data", 'Equipe Analisada', 'Tipo', 'Característica', 'Tempo', 'Autor', 'Assistente', 'Jogadores em quadra', 'xloc', 'yloc'])
    dados_analise_gols = dados_analise_gols.set_index('id')
    dados_analise_gols['quadrante'] = dados_analise_gols.apply(lambda row: calcular_quadrante(row['xloc'], row['yloc']), axis=1)
    dados_analise_gols.drop(['xloc', 'yloc'], inplace=True, axis=1)
    dados_analise_gols.fillna("", inplace=True)
    return dados_analise_gols

def extrair_estatisticas_jogadores(dados_jogador_df):
    """
    Extrai estatísticas de jogadas por tempo (1ºT, 2ºT, Total) para um jogador
    e as organiza em um DataFrame.

    Args:
        dados_jogador_df (pd.DataFrame): DataFrame contendo os dados das jogadas do jogador.

    Returns:
        pd.DataFrame: DataFrame com as contagens de jogadas por tipo e tempo.
    """
    primeiro_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '1ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T", 'DES.C/P.', 'DES.S/P.', 'PER.P.', 'C.A', 'ASSIST.', 'GOL'], fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '2ºT'].value_counts().reindex(["FIN.C", "FIN.E", "FIN.T", 'DES.C/P.', 'DES.S/P.', 'PER.P.', 'C.A', 'ASSIST.', 'GOL'], fill_value=0)
    estatiscas_jogadores_df = pd.DataFrame({"1ºT": primeiro_tempo, "2ºT": segundo_tempo})
    estatiscas_jogadores_df["Total"] = estatiscas_jogadores_df["1ºT"] + estatiscas_jogadores_df["2ºT"]
    estatiscas_jogadores_df.loc['FIN.TOTAL'] = estatiscas_jogadores_df.loc[['FIN.C', 'FIN.E', 'FIN.T']].sum()
    return estatiscas_jogadores_df

def extrair_estatisticas_gerais(dados_jogador_df):
    """
    Extrai estatísticas gerais de jogadas por tempo (1ºT, 2ºT, 1ºP, 2ºP) e total,
    reindexando para garantir todas as categorias de jogadas.

    Args:
        dados_jogador_df (pd.DataFrame): DataFrame contendo os dados das jogadas.

    Returns:
        tuple: Uma tupla de dicionários, cada um contendo as estatísticas para:
               1º Tempo, 2º Tempo, Total, 1º Tempo Prorrogação, 2º Tempo Prorrogação.
    """
    primeiro_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '1ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"], fill_value=0)
    segundo_tempo = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '2ºT'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"], fill_value=0)
    primeiro_tempo_prorrogacao = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '1ºP'].value_counts().reindex(['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"], fill_value=0)
    segundo_tempo_prorrogacao = dados_jogador_df.jogada.loc[dados_jogador_df["tempo"] == '2ºP'].value_counts().reindex(['FIN.C', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"], fill_value=0)

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


def extrair_estatisticas_localizacao(dados_jogador_df, jogada):
    """
    Extrai estatísticas de localização de uma jogada específica por quadrante e tempo.

    Args:
        dados_jogador_df (pd.DataFrame): DataFrame contendo os dados das jogadas.
        jogada (str): O tipo de jogada a ser analisado (ex: 'FIN.C', 'DES.S/P.').

    Returns:
        dict: Um dicionário onde as chaves são os tempos ('Primeiro Tempo', 'Segundo Tempo', 'Total', etc.)
              e os valores são Series pandas com as contagens por quadrante.
    """
    quadrantes_padrao = ['1.0-1.0', '1.0-2.0', '1.0-3.0', '2.0-1.0', '2.0-2.0', '2.0-3.0', '3.0-1.0', '3.0-2.0', '3.0-3.0', '4.0-1.0', '4.0-2.0', '4.0-3.0', '5.0-1.0', '5.0-2.0', '5.0-3.0', '6.0-1.0', '6.0-2.0', '6.0-3.0']

    primeiro_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '1ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(quadrantes_padrao, fill_value=0)
    segundo_tempo = dados_jogador_df[(dados_jogador_df["tempo"] == '2ºT') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(quadrantes_padrao, fill_value=0)
    total = primeiro_tempo + segundo_tempo
    primeiro_tempo_prorrogacao = dados_jogador_df[(dados_jogador_df["tempo"] == '1ºP') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(quadrantes_padrao, fill_value=0)
    segundo_tempo_prorrogacao = dados_jogador_df[(dados_jogador_df["tempo"] == '2ºP') & (dados_jogador_df["jogada"] == jogada)].quadrante.value_counts().reindex(quadrantes_padrao, fill_value=0)

    localizacao_jogadas = {
        "Primeiro Tempo": primeiro_tempo,
        "Segundo Tempo": segundo_tempo,
        "Total": total,
        "Primeiro Tempo Prorrogação": primeiro_tempo_prorrogacao,
        "Segundo Tempo Prorrogação": segundo_tempo_prorrogacao
    }
    return localizacao_jogadas

def plotar_estatisticas_gerais_time(estatisticas_totais_dict, numero_jogos):
    """
    Plota as estatísticas gerais de um time em um gráfico de indicadores (KPIs).

    Args:
        estatisticas_totais_dict (dict): Dicionário contendo as estatísticas totais do time.
        numero_jogos (int): O número de jogos considerados para as estatísticas.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com os indicadores de desempenho do time.
    """
    estatisticas_gerais_fig = go.Figure()

    efetividade_finalizacoes = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL'] if estatisticas_totais_dict['FIN.TOTAL'] > 0 else 0
    efetividade_finalizacoes_certas = estatisticas_totais_dict['GOL'] / estatisticas_totais_dict['FIN.C'] if estatisticas_totais_dict['FIN.C'] > 0 else 0

    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=numero_jogos, domain={'row': 0, 'column': 1},
        title={"text": "Jogos", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['GOL'], domain={'row': 1, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['FIN.TOTAL'], domain={'row': 1, 'column': 1},
        title={"text": "Fin.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=efetividade_finalizacoes, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 1, 'column': 2}, title={"text": "Efet.Fin.", "font": {"size": 12}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['GOL'] / numero_jogos if numero_jogos > 0 else 0,
        domain={'row': 2, 'column': 0}, title={"text": "Média Gols", "font": {"size": 12}},
        number={"font": {"size": 20}, "valueformat": ".1f"}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['FIN.C'], domain={'row': 2, 'column': 1},
        title={"text": "Fin.C.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=efetividade_finalizacoes_certas, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 2, 'column': 2}, title={"text": "Efet.Fin.C.", "font": {"size": 12}}
    ))

    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark", margin_t=7, margin_b=0, height=180, margin_l=10, margin_r=10
    )
    return estatisticas_gerais_fig


def plotar_estatisticas_gerais(estatisticas_totais_dict, numero_jogos):
    """
    Plota as estatísticas gerais de um jogador em um gráfico de indicadores (KPIs).

    Args:
        estatisticas_totais_dict (dict): Dicionário contendo as estatísticas totais do jogador.
        numero_jogos (int): O número de jogos considerados para as estatísticas.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com os indicadores de desempenho do jogador.
    """
    estatisticas_gerais_fig = go.Figure()

    efetividade_finalizacoes = estatisticas_totais_dict['FIN.C'] / estatisticas_totais_dict['FIN.TOTAL'] if estatisticas_totais_dict['FIN.TOTAL'] > 0 else 0
    efetividade_finalizacoes_certas = estatisticas_totais_dict['GOL'] / estatisticas_totais_dict['FIN.C'] if estatisticas_totais_dict['FIN.C'] > 0 else 0

    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=numero_jogos, domain={'row': 0, 'column': 1},
        title={"text": "Jogos", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['GOL'], domain={'row': 1, 'column': 0},
        title={"text": "Gols", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['FIN.TOTAL'], domain={'row': 1, 'column': 1},
        title={"text": "Fin.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=efetividade_finalizacoes, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 1, 'column': 2}, title={"text": "Efet.Fin.", "font": {"size": 12}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['ASSIST.'], domain={'row': 2, 'column': 0},
        title={"text": "Assist.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['FIN.C'], domain={'row': 2, 'column': 1},
        title={"text": "Fin.C.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=efetividade_finalizacoes_certas, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 2, 'column': 2}, title={"text": "Efet.Fin.C.", "font": {"size": 12}}
    ))

    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark", margin_t=7, margin_b=0, height=180, margin_l=10, margin_r=10
    )
    return estatisticas_gerais_fig


def plotar_estatisticas_gerais_1(estatisticas_totais_dict):
    """
    Plota estatísticas gerais adicionais (desarmes, perdas de posse, contra-ataques)
    em um gráfico de indicadores (KPIs).

    Args:
        estatisticas_totais_dict (dict): Dicionário contendo as estatísticas totais.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com os indicadores de desempenho.
    """
    estatisticas_gerais_fig = go.Figure()

    percentual_perda_de_posse = (
        estatisticas_totais_dict['C.A.-Contra'] / estatisticas_totais_dict['PER.P.']
        if estatisticas_totais_dict['PER.P.'] > 0 else 0
    )
    efetividade_desarme_com_posse = (
        estatisticas_totais_dict['C.A.-Pró'] / estatisticas_totais_dict['DES.C/P.']
        if estatisticas_totais_dict['DES.C/P.'] > 0 else 0
    )

    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['DES.C/P.'], domain={'row': 0, 'column': 0},
        title={"text": "Des.C/P.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['C.A.-Pró'], domain={'row': 1, 'column': 0},
        title={"text": "C.A. - Pró", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=efetividade_desarme_com_posse, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 2, 'column': 0}, title={"text": "Efetividade", "font": {"size": 12}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['DES.S/P.'], domain={'row': 1, 'column': 1},
        title={"text": "Des.S/P.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['PER.P.'], domain={'row': 0, 'column': 2},
        title={"text": "Per.P.", "font": {"size": 12}}, number={"font": {"size": 20}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=estatisticas_totais_dict['C.A.-Contra'], number={"font": {"size": 20}},
        domain={'row': 1, 'column': 2}, title={"text": "C.A Sofrido", "font": {"size": 12}}
    ))
    estatisticas_gerais_fig.add_trace(go.Indicator(
        mode="number", value=percentual_perda_de_posse, number={"valueformat": ".0%", "font": {"size": 20}},
        domain={'row': 2, 'column': 2}, title={"text": "Percentual", "font": {"size": 12}}
    ))

    estatisticas_gerais_fig.update_layout(
        grid={'rows': 3, 'columns': 3, 'pattern': "independent"},
        template="plotly_dark", height=270, margin_t=20, margin_r=5
    )
    return estatisticas_gerais_fig


def plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, mean_primeiro_tempo, mean_segundo_tempo):
    """
    Plota um gráfico de barras comparando as ações de um time no 1º e 2º tempo,
    incluindo linhas de média para comparação.

    Args:
        estatisticas_primeiro_tempo_dict (dict): Estatísticas do 1º tempo.
        estatisticas_segundo_tempo_dict (dict): Estatísticas do 2º tempo.
        mean_primeiro_tempo (np.array): Média das ações no 1º tempo.
        mean_segundo_tempo (np.array): Média das ações no 2º tempo.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com gráficos de barras comparativos.
    """
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]
    valores_1T = [estatisticas_primeiro_tempo_dict.get(categoria, 0) for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict.get(categoria, 0) for categoria in categorias]

    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)', 'rgba(255, 165, 0, 1.0)', 'rgba(0, 255, 255, 0.6)']

    fig = make_subplots(
        rows=1, cols=2, subplot_titles=('1º Tempo', '2º Tempo'), shared_yaxes=True
    )

    fig.add_trace(go.Bar(
        x=categorias, y=valores_1T, name='1º Tempo', marker_color=cores,
        text=valores_1T, textposition='inside', insidetextanchor='start', textfont=dict(color="black")
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=categorias, y=valores_2T, name='2º Tempo', marker_color=cores,
        text=valores_2T, textposition='inside', insidetextanchor='start', textfont=dict(color="black")
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=categorias, y=mean_primeiro_tempo, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_primeiro_tempo], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Primeiro Tempo"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=categorias, y=mean_segundo_tempo, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_segundo_tempo], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Segundo Tempo"
    ), row=1, col=2)

    fig.update_layout(
        title={'text': 'Comparação de Ações por Tempo', 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
        yaxis_title='Quantidade', barmode='group', template='plotly_dark', showlegend=False,
        height=450, margin=dict(t=80)
    )
    return fig

def plotar_grafico_barras_jogador(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, mean_primeiro_tempo, mean_segundo_tempo,posicao):
    """
    Plota um gráfico de barras comparando as ações de um jogador no 1º e 2º tempo,
    incluindo linhas de média para comparação.

    Args:
        estatisticas_primeiro_tempo_dict (dict): Estatísticas do 1º tempo do jogador.
        estatisticas_segundo_tempo_dict (dict): Estatísticas do 2º tempo do jogador.
        mean_primeiro_tempo (np.array): Média das ações do jogador no 1º tempo.
        mean_segundo_tempo (np.array): Média das ações do jogador no 2º tempo.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com gráficos de barras comparativos para o jogador.
    """
    
    if posicao == 'Goleiro':    
        categorias = ['DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra','FIN.S.C', 'FIN.S.E', 'FIN.S.T', ]
        mean_primeiro_tempo = mean_primeiro_tempo[3:]
        mean_segundo_tempo = mean_segundo_tempo[3:]
    else:
        categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']   
    
    valores_1T = [estatisticas_primeiro_tempo_dict.get(categoria, 0) for categoria in categorias]
    valores_2T = [estatisticas_segundo_tempo_dict.get(categoria, 0) for categoria in categorias]

    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)', 'rgba(255, 165, 0, 1.0)']

    fig = make_subplots(
        rows=1, cols=2, subplot_titles=('1º Tempo', '2º Tempo'), shared_yaxes=True
    )

    fig.add_trace(go.Bar(
        x=categorias, y=valores_1T, name='1º Tempo', marker_color=cores,
        text=valores_1T, textposition='inside', insidetextanchor='start', textfont=dict(color="black")
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=categorias, y=valores_2T, name='2º Tempo', marker_color=cores,
        text=valores_2T, textposition='inside', insidetextanchor='start', textfont=dict(color="black")
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=categorias, y=mean_primeiro_tempo, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_primeiro_tempo], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Primeiro Tempo"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=categorias, y=mean_segundo_tempo, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_segundo_tempo], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Segundo Tempo"
    ), row=1, col=2)

    fig.update_layout(
        title={'text': 'Comparação de Ações por Tempo', 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
        xaxis_title='Tipo de Ação', yaxis_title='Quantidade', barmode='group', template='plotly_dark',
        showlegend=False, height=450, margin=dict(t=80)
    )
    return fig

def plotar_grafico_barras_parcial(estatisticas_parciais_dict, mean):
    """
    Plota um gráfico de barras para ações parciais (ataque/defesa) de um time,
    incluindo linhas de média para comparação.

    Args:
        estatisticas_parciais_dict (dict): Dicionário de estatísticas parciais do time.
        mean (np.array): Média das ações para comparação.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com gráficos de barras para ataque e defesa.
    """
    categorias_ataque = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró']
    categorias_defesa = ['DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]
    mean_ataque = [mean[i] for i in range(len(categorias_ataque))]
    mean_defesa = [mean[i] for i in range(len(categorias_ataque), len(categorias_ataque) + len(categorias_defesa))]

    valores_ataque = np.array([estatisticas_parciais_dict.get(categoria, 0) for categoria in categorias_ataque])
    valores_defesa = np.array([estatisticas_parciais_dict.get(categoria, 0) for categoria in categorias_defesa])

    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)', 'rgba(255, 165, 0, 1.0)', 'rgba(0, 255, 255, 0.6)']

    fig = make_subplots(
        rows=1, cols=2, subplot_titles=('Ataque', 'Defesa'), shared_yaxes=True
    )

    fig.add_trace(go.Bar(
        x=categorias_ataque, y=valores_ataque, name='Ataque', marker_color=cores[:len(categorias_ataque)],
        text=valores_ataque, textposition='inside', insidetextanchor='end', textfont=dict(color="black")
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=categorias_defesa, y=valores_defesa, name='Defesa', marker_color=cores[len(categorias_ataque):],
        text=valores_defesa, textposition='inside', insidetextanchor='end', textfont=dict(color="black")
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=categorias_ataque, y=mean_ataque, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_ataque], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Ataque"
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=categorias_defesa, y=mean_defesa, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean_defesa], textposition="top center",
        marker=dict(size=8, color="white"), line=dict(width=2, color="cyan"), name="Média Defesa"
    ), row=1, col=2)

    fig.update_layout(
        yaxis_title='Quantidade', barmode='group', template='plotly_dark', showlegend=False,
        height=450, margin=dict(t=80)
    )
    return fig

def plotar_grafico_barras_parcial_jogador(estatisticas_parciais_dict, mean,posicao):
    """
    Plota um gráfico de barras para ações parciais de um jogador,
    incluindo uma linha de média para comparação.

    Args:
        estatisticas_parciais_dict (dict): Dicionário de estatísticas parciais do jogador.
        mean (np.array): Média das ações para comparação.
        posicao (str): Posicao do jogador.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras das ações do jogador.
    """
    if posicao == "Goleiro":
        categorias = [ 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra','FIN.S.C', 'FIN.S.E', 'FIN.S.T'] 
        mean = mean[3:]
    else:    
        categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']
    
    
    valores = np.array([estatisticas_parciais_dict.get(categoria, 0) for categoria in categorias])
    cores = ['rgba(0, 255, 0, 0.6)', 'rgba(255, 0, 0, 0.6)', 'rgba(255, 255, 0, 0.6)',
             'rgba(0, 0, 255, 0.6)', 'rgba(0, 255, 255, 0.6)', 'rgba(128, 0, 128, 0.6)', 'rgba(0, 60, 0, 1.0)', 'rgba(255, 165, 0, 1.0)']

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categorias, y=valores, marker_color=cores,
        text=valores, textposition='inside', insidetextanchor='start', textfont=dict(color="black")
    ))
    fig.add_trace(go.Scatter(
        x=categorias, y=mean, mode="lines+markers+text",
        text=[f"{m:.2f}" for m in mean], textposition="top center",
        marker=dict(size=9, color="white"), line=dict(width=2, color="cyan"), name="Média"
    ))

    fig.update_layout(
        title={'text': 'Ações', 'x': 0.5, 'xanchor': 'center', 'y': 0.95},
        xaxis_title='Tipo de Ação', yaxis_title='Quantidade', barmode='group', template='plotly_dark',
        showlegend=False, height=450, margin=dict(t=60)
    )
    return fig


def plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, numero_jogos):
    """
    Plota gráficos de rosca para o histórico de desempenho de um time,
    mostrando a média de finalizações, desarmes com posse e perdas de posse por tempo.

    Args:
        estatisticas_primeiro_tempo_dict (dict): Estatísticas do 1º tempo do time.
        estatisticas_segundo_tempo_dict (dict): Estatísticas do 2º tempo do time.
        numero_jogos (int): O número de jogos considerados.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com gráficos de rosca.
    """
    labels = ['Primeiro Tempo', 'Segundo Tempo']
    data_finalizacoes = np.array([estatisticas_primeiro_tempo_dict.get('FIN.TOTAL', 0), estatisticas_segundo_tempo_dict.get('FIN.TOTAL', 0)])
    data_desempenho_posse = np.array([estatisticas_primeiro_tempo_dict.get('DES.C/P.', 0), estatisticas_segundo_tempo_dict.get('DES.C/P.', 0)])
    data_perda_posse = np.array([estatisticas_primeiro_tempo_dict.get('PER.P.', 0), estatisticas_segundo_tempo_dict.get('PER.P.', 0)])

    mean_finalizacoes = (data_finalizacoes / numero_jogos).astype(int) if numero_jogos > 0 else np.zeros_like(data_finalizacoes)
    mean_desempenho_posse = (data_desempenho_posse / numero_jogos).astype(int) if numero_jogos > 0 else np.zeros_like(data_desempenho_posse)
    mean_perda_posse = (data_perda_posse / numero_jogos).astype(int) if numero_jogos > 0 else np.zeros_like(data_perda_posse)

    fig = make_subplots(
        rows=1, cols=3, specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=['Média de Finalizações', 'Média Des. c/ Posse', 'Média Perda de Posse']
    )

    fig.add_trace(go.Pie(
        labels=labels, values=mean_finalizacoes, name="Finalizações", hole=0.5,
        textinfo='percent', texttemplate='%{value} (%{percent})', rotation=180, sort=False,
    ), 1, 1)

    fig.add_trace(go.Pie(
        labels=labels, values=mean_desempenho_posse, name="Des. c/ Posse", hole=0.5,
        textinfo='percent', texttemplate='%{value} (%{percent})', rotation=180, sort=False,
    ), 1, 2)

    fig.add_trace(go.Pie(
        labels=labels, values=mean_perda_posse, name="Perda de Posse", hole=0.5,
        textinfo='percent', texttemplate='%{value} (%{percent})', rotation=180, sort=False,
        textposition="inside",
    ), 1, 3)

    fig.update_layout(
        title_text="Histórico", title_x=0.4, showlegend=True,
        legend=dict(x=0.5, y=-0.2, xanchor="center", yanchor="middle", orientation="h")
    )
    return fig


def plotar_historico_time(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, numero_jogos):
    """
    Plota gráficos de rosca para o histórico de desempenho de um time, detalhado por tipo de ação.

    Args:
        estatisticas_primeiro_tempo_dict (dict): Estatísticas do 1º tempo do time.
        estatisticas_segundo_tempo_dict (dict): Estatísticas do 2º tempo do time.
        numero_jogos (int): O número de jogos considerados.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com gráficos de rosca detalhados.
    """
    labels = ['Primeiro Tempo', 'Segundo Tempo']
    categorias = {
        "Média Finalizações Certas": "FIN.C",
        "Média Finalizações Erradas": "FIN.E",
        "Média Finalizações Travadas": "FIN.T",
        "Média Des. c/ Posse": "DES.C/P.",
        "Média Des. s/ Posse": "DES.S/P.",
        "Média Perda de Posse": "PER.P.",
    }

    fig = make_subplots(
        rows=2, cols=3, specs=[[{'type': 'domain'}] * 3, [{'type': 'domain'}] * 3],
        subplot_titles=list(categorias.keys())
    )

    for i, (titulo, chave) in enumerate(categorias.items()):
        row = (i // 3) + 1
        col = (i % 3) + 1
        valores = np.array([
            estatisticas_primeiro_tempo_dict.get(chave, 0),
            estatisticas_segundo_tempo_dict.get(chave, 0)
        ])
        mean_valores = (valores / numero_jogos).astype(int) if numero_jogos > 0 else [0, 0]

        fig.add_trace(go.Pie(
            labels=labels, values=mean_valores, name=titulo, hole=0.5,
            textinfo='percent', texttemplate='%{value} (%{percent})', rotation=180, sort=False,
            textposition="inside"
        ), row=row, col=col)

    fig.update_annotations(
        font_size=14, xanchor="center", yanchor="bottom", yshift=20
    )
    fig.update_layout(
        title_text="Histórico", title_x=0.45, title_y=0.98, showlegend=True, height=450,
        legend=dict(x=0.5, y=-0.2, xanchor="center", yanchor="bottom", orientation="h")
    )
    return fig


def plotar_radar_chart(estatisticas_totais_dict, estatisticas_geral_totais_dict,posicao):
    """
    Plota um gráfico de radar comparando as estatísticas de um jogador
    com as estatísticas gerais (da equipe ou de todos os jogadores).

    Args:
        estatisticas_totais_dict (dict): Dicionário contendo as estatísticas totais do jogador.
        estatisticas_geral_totais_dict (dict): Dicionário contendo as estatísticas gerais para comparação.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de radar.
    """
    if posicao == "Goleiro":
        theta = ['FIN.S.C', 'FIN.S.E', 'FIN.S.T', 'DES.C/P.', 'DES.S/P.', 'PER.P.']
    else:
        theta = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'DES.S/P.', 'PER.P.']

    numerador = [estatisticas_totais_dict.get(i, 0) for i in theta]
    denominador = [estatisticas_geral_totais_dict.get(i, 0) for i in theta]

    valores = [n / d if d != 0 else 0 for n, d in zip(numerador, denominador)]

    valores.append(valores[0]) # Fechar o ciclo

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores, theta=theta + [theta[0]], fill='toself', name="Desempenho",
        text=[f"{v:.1%}" for v in valores], # Formato de porcentagem com uma casa decimal
        hoverinfo="text",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 1.0], showticklabels=True,
                tickvals=[0.2, 0.4, 0.6, 0.8, 1.0], ticktext=["20%", "40%", "60%", "80%", "100%"],
                tickformat="%", tickangle=0,
            ),
        ),
        showlegend=False, template="plotly_dark",
    )
    return fig

def create_arc(x_center, y_center, radius, theta1, theta2, color='gray', width=2):
    """
    Cria um traço de arco para ser usado na representação da quadra de futsal.

    Args:
        x_center (float): Coordenada X do centro do arco.
        y_center (float): Coordenada Y do centro do arco.
        radius (float): Raio do arco.
        theta1 (float): Ângulo inicial do arco em graus.
        theta2 (float): Ângulo final do arco em graus.
        color (str, optional): Cor do arco. Padrão é 'gray'.
        width (int, optional): Espessura da linha do arco. Padrão é 2.

    Returns:
        tuple: Uma tupla contendo:
               - dict: Dicionário de configuração do traço Scatter para o Plotly.
               - tuple: Coordenadas (x, y) do ponto inicial do arco.
               - tuple: Coordenadas (x, y) do ponto final do arco.
    """
    theta = np.linspace(np.radians(theta1), np.radians(theta2), 100)
    x = x_center + radius * np.cos(theta)
    y = y_center + radius * np.sin(theta)
    return dict(type='scatter', x=x, y=y, mode='lines', line=dict(color=color, width=width)), (x[0], y[0]), (x[-1], y[-1])

def create_futsal_court(titulo, heatmap_data, line_color='white'):
    """
    Cria uma figura Plotly representando uma quadra de futsal com um heatmap
    sobreposto para visualizar a distribuição de jogadas.

    Args:
        titulo (str): Título do gráfico da quadra.
        heatmap_data (list or np.array): Dados para o heatmap, que serão remodelados para 6x3.
        line_color (str, optional): Cor das linhas da quadra. Padrão é 'white'.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly da quadra de futsal com heatmap.
    """
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
    """
    Busca uma imagem de jogador de uma URL do Google Drive.

    Args:
        image_id (str): O ID da imagem no Google Drive.

    Returns:
        bytes: O conteúdo binário da imagem se a requisição for bem-sucedida e o conteúdo for uma imagem,
               caso contrário, retorna None.
    """
    if not image_id:
        return None

    url = f"https://drive.google.com/uc?id={image_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            print(f"Conteúdo não é uma imagem. Tipo: {content_type}")
            return None

        try:
            Image.open(BytesIO(response.content)).verify()
        except Exception as e:
            print(f"Imagem inválida: {e}")
            return None

        return response.content

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar imagem: {e}")
        return None

def get_player_photo(image_id):
    """
    Busca uma imagem de jogador de uma URL genérica.

    Args:
        image_id (str): A URL direta da imagem.

    Returns:
        bytes: O conteúdo binário da imagem se a requisição for bem-sucedida e o conteúdo for uma imagem,
               caso contrário, retorna None.
    """
    if not image_id:
        return None

    url = f"{image_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            print(f"Conteúdo não é uma imagem. Tipo: {content_type}")
            return None

        try:
            Image.open(BytesIO(response.content)).verify()
        except Exception as e:
            print(f"Imagem inválida: {e}")
            return None

        return response.content

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar imagem: {e}")
        return None


def listar_competicoes_unicas(lista_jogos):
    """
    Lista competições únicas a partir de uma lista de jogos.

    Args:
        lista_jogos (list): Uma lista de tuplas, onde cada tupla representa um jogo.
                            Assume-se que o índice 6 contém o nome da competição.

    Returns:
        list: Uma lista ordenada de strings, cada uma representando uma competição única.
    """
    competicoes = {jogo[6] for jogo in lista_jogos if jogo[6]}
    return sorted(competicoes)

def get_team_total_figures(estatisticas_totais_dict, estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, numero_jogos, mean_primeiro_tempo, mean_segundo_tempo):
    """
    Retorna as figuras totais para a análise de um time, incluindo gráficos de indicadores
    e gráficos de barras comparativos.

    Args:
        estatisticas_totais_dict (dict): Dicionário com as estatísticas totais do time.
        estatisticas_primeiro_tempo_dict (dict): Dicionário com as estatísticas do 1º tempo do time.
        estatisticas_segundo_tempo_dict (dict): Dicionário com as estatísticas do 2º tempo do time.
        numero_jogos (int): O número total de jogos analisados.
        mean_primeiro_tempo (np.array): Média das ações no 1º tempo.
        mean_segundo_tempo (np.array): Média das ações no 2º tempo.

    Returns:
        tuple: Uma tupla contendo:
               - plotly.graph_objects.Figure: Figura de estatísticas gerais (KPIs).
               - plotly.graph_objects.Figure: Figura de estatísticas gerais adicionais (KPIs).
               - plotly.graph_objects.Figure: Figura de gráfico de barras comparativo.
    """
    estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_totais_dict, numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_totais_dict)
    grafico_barras_fig = plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, mean_primeiro_tempo, mean_segundo_tempo)
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig

def get_team_partial_figures(estatisticas_parciais_dict, numero_jogos, mean):
    """
    Retorna as figuras parciais para a análise de um time, focando em um período específico
    (ex: 1º tempo, 2º tempo, prorrogação), incluindo gráficos de indicadores e gráficos de barras parciais.

    Args:
        estatisticas_parciais_dict (dict): Dicionário com as estatísticas parciais do time.
        numero_jogos (int): O número de jogos analisados para este período.
        mean (np.array): Média das ações para este período.

    Returns:
        tuple: Uma tupla contendo:
               - plotly.graph_objects.Figure: Figura de estatísticas gerais (KPIs).
               - plotly.graph_objects.Figure: Figura de estatísticas gerais adicionais (KPIs).
               - plotly.graph_objects.Figure: Figura de gráfico de barras parcial.
    """
    estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_parciais_dict, numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_parciais_dict)
    grafico_barras_fig = plotar_grafico_barras_parcial(estatisticas_parciais_dict, mean)
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig


def get_mean(df):
    """
    Calcula as médias de diferentes categorias de jogadas para vários períodos de tempo
    (1ºT, 2ºT, Total, 1ºP, 2ºP) a partir de um DataFrame.

    Args:
        df (pd.DataFrame): DataFrame contendo os dados das jogadas.

    Returns:
        tuple: Uma tupla de arrays NumPy, cada um contendo as médias para:
               1º Tempo, 2º Tempo, Total, 1º Tempo Prorrogação, 2º Tempo Prorrogação.
    """
    numero_jogos = int(df["jogo_id"].nunique())
    # Garante que numero_jogos_prorrogacao seja pelo menos 1 para evitar divisão por zero
    numero_jogos_prorrogacao = int(df[df["tempo"].isin(["1ºP", "2ºP"])]["jogo_id"].nunique())
    numero_jogos_prorrogacao = numero_jogos_prorrogacao if numero_jogos_prorrogacao > 0 else 1


    estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict, estatisticas_pt_prorrogacao_dict, estatisticas_st_prorrogacao_dict = extrair_estatisticas_gerais(df)
    categorias = ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]

    valores_totais = np.array([estatisticas_totais_dict.get(categoria, 0) for categoria in categorias])
    mean_total = valores_totais / numero_jogos if numero_jogos > 0 else np.zeros_like(valores_totais)

    valores_primeiro_tempo = np.array([estatisticas_primeiro_tempo_dict.get(categoria, 0) for categoria in categorias])
    mean_primeiro_tempo = valores_primeiro_tempo / numero_jogos if numero_jogos > 0 else np.zeros_like(valores_primeiro_tempo)

    valores_segundo_tempo = np.array([estatisticas_segundo_tempo_dict.get(categoria, 0) for categoria in categorias])
    mean_segundo_tempo = valores_segundo_tempo / numero_jogos if numero_jogos > 0 else np.zeros_like(valores_segundo_tempo)

    valores_primeiro_tempo_prorrogacao = np.array([estatisticas_pt_prorrogacao_dict.get(categoria, 0) for categoria in categorias])
    mean_primeiro_tempo_prorrogacao = valores_primeiro_tempo_prorrogacao / numero_jogos_prorrogacao if numero_jogos_prorrogacao != 0 else np.zeros_like(valores_primeiro_tempo_prorrogacao)

    valores_segundo_tempo_prorrogacao = np.array([estatisticas_st_prorrogacao_dict.get(categoria, 0) for categoria in categorias])
    mean_segundo_tempo_prorrogacao = valores_segundo_tempo_prorrogacao / numero_jogos_prorrogacao if numero_jogos_prorrogacao != 0 else np.zeros_like(valores_segundo_tempo_prorrogacao)

    return mean_primeiro_tempo, mean_segundo_tempo, mean_total, mean_primeiro_tempo_prorrogacao, mean_segundo_tempo_prorrogacao


def get_athletes_total_figures(estatisticas_totais_dict, estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_geral_totais_dict, numero_jogos, mean_primeiro_tempo, mean_segundo_tempo,posicao):
    """
    Retorna as figuras totais para a análise de um atleta, incluindo gráficos de indicadores,
    gráficos de barras comparativos e um gráfico de radar.

    Args:
        estatisticas_totais_dict (dict): Dicionário com as estatísticas totais do atleta.
        estatisticas_primeiro_tempo_dict (dict): Dicionário com as estatísticas do 1º tempo do atleta.
        estatisticas_segundo_tempo_dict (dict): Dicionário com as estatísticas do 2º tempo do atleta.
        estatisticas_geral_totais_dict (dict): Dicionário com as estatísticas gerais para comparação no radar.
        numero_jogos (int): O número total de jogos analisados para o atleta.
        mean_primeiro_tempo (np.array): Média das ações do atleta no 1º tempo.
        mean_segundo_tempo (np.array): Média das ações do atleta no 2º tempo.

    Returns:
        tuple: Uma tupla contendo:
               - plotly.graph_objects.Figure: Figura de estatísticas gerais (KPIs).
               - plotly.graph_objects.Figure: Figura de estatísticas gerais adicionais (KPIs).
               - plotly.graph_objects.Figure: Figura de gráfico de barras comparativo.
               - plotly.graph_objects.Figure: Figura do gráfico de radar.
    """
    estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_totais_dict, numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_totais_dict)
    grafico_barras_fig = plotar_grafico_barras_jogador(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, mean_primeiro_tempo, mean_segundo_tempo,posicao)
    radar_fig = plotar_radar_chart(estatisticas_totais_dict, estatisticas_geral_totais_dict,posicao)
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig, radar_fig

def get_athletes_partial_figures(estatisticas_parciais_dict, estatisticas_geral_parciais_dict, numero_jogos, mean,posicao):
    """
    Retorna as figuras parciais para a análise de um atleta, focando em um período específico
    (ex: 1º tempo, 2º tempo), incluindo gráficos de indicadores, gráficos de barras parciais e um gráfico de radar.

    Args:
        estatisticas_parciais_dict (dict): Dicionário com as estatísticas parciais do atleta.
        estatisticas_geral_parciais_dict (dict): Dicionário com as estatísticas gerais para comparação no radar.
        numero_jogos (int): O número de jogos analisados para este período.
        mean (np.array): Média das ações para este período.
        posicao (str): Posicao do jogador.

    Returns:
        tuple: Uma tupla contendo:
               - plotly.graph_objects.Figure: Figura de estatísticas gerais (KPIs).
               - plotly.graph_objects.Figure: Figura de estatísticas gerais adicionais (KPIs).
               - plotly.graph_objects.Figure: Figura de gráfico de barras parcial.
               - plotly.graph_objects.Figure: Figura do gráfico de radar.
    """
    
    
    estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_parciais_dict, numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_parciais_dict)
    grafico_barras_fig = plotar_grafico_barras_parcial_jogador(estatisticas_parciais_dict, mean,posicao)
    radar_fig = plotar_radar_chart(estatisticas_parciais_dict, estatisticas_geral_parciais_dict,posicao)
    return estatisticas_gerais_fig, estatisticas_gerais_fig_1, grafico_barras_fig, radar_fig


def get_plots_plays_localization_team(filtro_jogada, data, tempo):
    """
    Retorna uma lista de figuras da quadra de futsal com heatmaps de localização
    para jogadas específicas de um time, filtradas por tipo de jogada e tempo.

    Args:
        filtro_jogada (str): O tipo de jogada a ser filtrado ("Ataque" ou "Defesa").
        data (pd.DataFrame): DataFrame contendo os dados das jogadas.
        tempo (str): O período de tempo a ser analisado (ex: 'Primeiro Tempo', 'Segundo Tempo').

    Returns:
        list: Uma lista de figuras Plotly (quadras de futsal com heatmaps).
    """
    jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró'], "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]}
    jogadas_selecionadas = jogadas[filtro_jogada]
    figs = []
    for jogada in jogadas_selecionadas:
        localizacao_jogadas = extrair_estatisticas_localizacao(data, jogada)
        fig = create_futsal_court(jogada, localizacao_jogadas[tempo])
        figs.append(fig)
    return figs

def get_plots_plays_localization_athletes(filtro_jogada, data, tempo,posicao):
    """
    Retorna uma lista de figuras da quadra de futsal com heatmaps de localização
    para jogadas específicas de um atleta, filtradas por tipo de jogada e tempo.

    Args:
        filtro_jogada (str): O tipo de jogada a ser filtrado ("Ataque" ou "Defesa").
        data (pd.DataFrame): DataFrame contendo os dados das jogadas do atleta.
        tempo (str): O período de tempo a ser analisado (ex: 'Primeiro Tempo', 'Segundo Tempo').

    Returns:
        list: Uma lista de figuras Plotly (quadras de futsal com heatmaps).
    """
    if posicao == 'Goleiro':
    
        jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T','DES.C/P.', 'C.A.-Pró'], 
                   "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra',"FIN.S.C", "FIN.S.E", "FIN.S.T"]}
    else:
        jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T','DES.C/P.', 'C.A.-Pró'], 
                   "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra']}
            
    
    jogadas_selecionadas = jogadas[filtro_jogada]
    figs = []
    for jogada in jogadas_selecionadas:
        localizacao_jogadas = extrair_estatisticas_localizacao(data, jogada)
        fig = create_futsal_court(jogada, localizacao_jogadas[tempo])
        figs.append(fig)
    return figs


def create_futsal_subplots(tipo, data, tempo, rows, cols):
    """
    Cria uma figura Plotly com múltiplos subplots de quadras de futsal,
    cada um exibindo um heatmap de localização para diferentes tipos de jogadas
    (ataque ou defesa) em um período de tempo específico.

    Args:
        tipo (str): O tipo de jogada a ser exibido ("Ataque" ou "Defesa").
        data (pd.DataFrame): DataFrame contendo os dados das jogadas.
        tempo (str): O período de tempo a ser analisado (ex: 'Primeiro Tempo', 'Segundo Tempo').
        rows (int): Número de linhas para os subplots.
        cols (int): Número de colunas para os subplots.

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com múltiplos subplots de quadras.
    """
    titulos = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T'], "Defesa": ['DES.C/P.', 'C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra']}
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

        fig.update_xaxes(visible=False, row=row, col=col)

    fig.update_layout(
        showlegend=False, plot_bgcolor='#121212', template="plotly_dark",
        yaxis=dict(visible=False),
        yaxis2=dict(visible=False, scaleanchor="x", scaleratio=1),
        yaxis3=dict(visible=False, scaleanchor="x", scaleratio=1)
    )
    return fig

def plotar_caracteristicas_gols(df_gols, equipe1, equipe2):
    """
    Plota um gráfico de barras horizontal comparando as características de gols
    marcados por uma equipe e sofridos por outra.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe (para gols marcados).
        equipe2 (str): Nome da segunda equipe (para gols sofridos).

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras comparativo de gols.
    """
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2)

    labels = [
        "Total", "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]

    fig = go.Figure()
    values_gols_marcados = gols_marcados_e1.values
    total_gols_marcados = sum(values_gols_marcados)
    values_gols_marcados = np.insert(values_gols_marcados, 0, total_gols_marcados)
    percentual_gols_marcados = values_gols_marcados / total_gols_marcados if total_gols_marcados != 0 else np.zeros_like(values_gols_marcados)

    values_gols_sofridos = gols_sofridos_e2.values
    total_gols_sofridos = sum(values_gols_sofridos)
    values_gols_sofridos = np.insert(values_gols_sofridos, 0, total_gols_sofridos)
    percentual_gols_sofridos = values_gols_sofridos / total_gols_sofridos if total_gols_sofridos != 0 else np.zeros_like(values_gols_sofridos)

    fig.add_trace(go.Bar(
        y=labels, x=percentual_gols_sofridos, name=f'Gols Sofridos {equipe2}', orientation='h',
        text=[f"{v} ({(v/total_gols_sofridos)*100:.2f}%)" for v in values_gols_sofridos],
        textposition='inside', insidetextanchor='start', marker=dict(color='rgb(214, 39, 40)'), width=0.82,
    ))

    fig.add_trace(go.Bar(
        y=labels, x=[-v for v in percentual_gols_marcados], name=f'Gols Marcados {equipe1}', orientation='h',
        text=[f"({(v/total_gols_marcados)*100:.2f}%) {v} " for v in values_gols_marcados],
        textposition='inside', insidetextanchor='start', marker=dict(color='rgb(44, 160, 44)'), width=0.82,
    ))

    titulo_esquerda = f'Gols Marcados {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2}(nº de jogos: {jogos_e2})'

    fig.update_layout(
        showlegend=False, barmode='relative', height=600, legend=dict(x=0.85),
        xaxis=dict(
            showgrid=True, gridcolor='white', gridwidth=0.5,
            tickvals=[-1, -0.5, 0, 0.5, 1], ticktext=['100%', "50%", '0%', "50%", '100%'],
            range=[-1.03, 1.03], tickfont=dict(size=15)
        ),
        yaxis=dict(showgrid=True, tickfont=dict(size=14)),
        annotations=[
            dict(text=titulo_esquerda, x=0.4, y=1.1, xref='paper', yref='paper', xanchor='right', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
            dict(text='X', x=0.5, y=1.1, xref='paper', yref='paper', showarrow=False, font=dict(size=20, family="Arial Black")),
            dict(text=titulo_direita, x=0.6, y=1.1, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
        ]
    )
    return fig

def plotar_caracteristicas_gols_1(df_gols, equipe1, equipe2):
    """
    Plota um gráfico de barras horizontal empilhado comparando as características de gols
    marcados por uma equipe e sofridos por outra, divididos por tempo (quartos/prorrogação).

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe (para gols marcados).
        equipe2 (str): Nome da segunda equipe (para gols sofridos).

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras empilhado de gols.
    """
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)
    total_gm_e1 = int(gols_marcados_e1.sum())
    total_gs_e2 = int(gols_sofridos_e2.sum())
    tempos = gols_marcados_e1.index.get_level_values(0).unique().tolist()
    labels = gols_marcados_e1.index.get_level_values(1).unique().tolist()
    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()
    tons_de_vermelho = ['#FF0000', '#CC0000', '#FF6666', '#990000', '#FF3333', '#E60000']
    tons_de_verde = ['#00FF00', '#00CC00', '#66FF66', '#009900', '#33FF33', '#00E600']
    data = []
    for i, tempo in enumerate(tempos):
        valores = gols_marcados_e1.loc[tempo].values
        percentual = valores / total_gm_e1 if total_gm_e1 != 0 else np.zeros_like(valores)
        valores1 = gols_sofridos_e2.loc[tempo].values
        percentual1 = valores1 / total_gs_e2 if total_gs_e2 != 0 else np.zeros_like(valores1)
        cor = tons_de_vermelho[i % len(tons_de_vermelho)]
        cor1 = tons_de_verde[i % len(tons_de_verde)]
        data.append(
            go.Bar(
                name=f'{equipe1} - {tempo}', x=percentual, y=labels, offsetgroup=1, base=acumulado.copy(), orientation='h',
                text=[f"{valores[i]} ({(percentual[i]*100):.2f}%)" for i in range(len(valores))],
                textposition='inside', insidetextanchor='middle', marker_color=cor, width=0.82,
            )
        )
        data.append(
            go.Bar(
                name=f'{equipe2} - {tempo}', x=-percentual1, y=labels, offsetgroup=2, base=-acumulado1.copy(), orientation='h',
                text=[f"{valores1[i]} ({(percentual1[i]*100):.2f}%)" for i in range(len(valores1))],
                textposition='inside', insidetextanchor='middle', marker_color=cor1, width=0.822,
            )
        )
        acumulado += percentual
        acumulado1 += percentual1

    for i, tempo in enumerate(tempos):
        cor_vermelho_legenda = tons_de_vermelho[i % len(tons_de_vermelho)]
        cor_verde_legenda = tons_de_verde[i % len(tons_de_verde)]
        data.append(go.Bar(name=f'{equipe1} - {tempo}', x=[0], y=[None] * len(labels), marker_color=cor_vermelho_legenda, showlegend=True))
        data.append(go.Bar(name=f'{equipe2} - {tempo}', x=[0], y=[None] * len(labels), marker_color=cor_verde_legenda, showlegend=True))

    titulo_esquerda = f'Gols Marcados {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2}(nº de jogos: {jogos_e2})'

    fig = go.Figure(
        data=data,
        layout=go.Layout(
            barmode='relative', showlegend=True, height=600, legend=dict(x=0.85),
            xaxis=dict(
                showgrid=True, gridcolor='white', gridwidth=0.5,
                tickfont=dict(size=14), tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['100%', '50%', '0%', '50%', '100%'], range=[-1.03, 1.03],
            ),
            yaxis=dict(showgrid=True, tickfont=dict(size=13)),
            annotations=[
                dict(text=titulo_esquerda, x=0.4, y=1.1, xref='paper', yref='paper', xanchor='right', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
                dict(text='X', x=0.5, y=1.1, xref='paper', yref='paper', showarrow=False, font=dict(size=20, family="Arial Black")),
                dict(text=titulo_direita, x=0.6, y=1.1, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
            ]
        )
    )
    return fig

def plotar_caracteristicas_gols_2(df_gols, equipe1, equipe2):
    """
    Plota um gráfico de barras horizontal empilhado comparando as características de gols
    marcados por uma equipe e sofridos por outra, divididos por tempo (quartos/prorrogação),
    com legendas personalizadas.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe (para gols marcados).
        equipe2 (str): Nome da segunda equipe (para gols sofridos).

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras empilhado de gols e legendas.
    """
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)

    total_gm_e1 = int(gols_marcados_e1.sum())
    total_gs_e2 = int(gols_sofridos_e2.sum())

    tempos = gols_marcados_e1.index.get_level_values(0).unique().tolist()
    labels = gols_marcados_e1.index.get_level_values(1).unique().tolist()

    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()

    tons_sofridos = ['#800000', '#FF9999', '#ff0000', '#FF6666', '#CC0000', '#E63939']
    tons_marcados = ['#003300', '#4dff4d', '#00A600', '#b3ffb3', '#00CC00', '#39E639']

    data = []

    for i, tempo in enumerate(tempos):
        valores = gols_marcados_e1.loc[tempo].values
        percentual = valores / total_gm_e1 if total_gm_e1 != 0 else np.zeros_like(valores)
        valores1 = gols_sofridos_e2.loc[tempo].values
        percentual1 = valores1 / total_gs_e2 if total_gs_e2 != 0 else np.zeros_like(valores1)

        cor_vermelho = tons_sofridos[i % len(tons_sofridos)]
        cor_verde = tons_marcados[i % len(tons_marcados)]

        data.append(go.Bar(
            name=f'{equipe2} - {tempo}', x=percentual1, y=labels, offsetgroup=1, base=acumulado1.copy(), orientation='h',
            text=[f"{valores1[i]} ({(percentual1[i]*100):.2f}%)" for i in range(len(valores1))],
            textposition='inside', insidetextanchor='middle', marker_color=cor_vermelho, width=0.82,
        ))

        data.append(go.Bar(
            name=f'{equipe1} - {tempo}', x=-percentual, y=labels, offsetgroup=2, base=-acumulado.copy(), orientation='h',
            text=[f"({(percentual[i]*100):.2f}%) {valores[i]}" for i in range(len(valores))],
            textposition='inside', insidetextanchor='middle', marker_color=cor_verde, width=0.822,
        ))

        acumulado += percentual
        acumulado1 += percentual1

    titulo_esquerda = f'Gols Marcados {equipe1} (nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Sofridos {equipe2} (nº de jogos: {jogos_e2})'

    existing_annotations = [
        dict(text=titulo_esquerda, x=0.4, y=1.2, xref='paper', yref='paper', xanchor='right', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
        dict(text='X', x=0.5, y=1.2, xref='paper', yref='paper', showarrow=False, font=dict(size=20, family="Arial Black")),
        dict(text=titulo_direita, x=0.6, y=1.2, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black"))
    ]

    legend_shapes = []
    legend_annotations = []

    y_legend = 1.07
    x_start_esq = 0.10
    x_start_dir = 0.6
    delta_x = 0.053
    delta_shape = 0.05

    for i, tempo in enumerate(reversed(tempos)):
        original_idx = len(tempos) - 1 - i
        legend_shapes.append(dict(
            type="rect", xref="paper", yref="paper",
            x0=x_start_esq + (i * delta_shape), y0=y_legend - 0.03,
            x1=x_start_esq + (i * delta_shape) + 0.05, y1=y_legend + 0.03,
            fillcolor=tons_marcados[original_idx % len(tons_marcados)], line=dict(width=0)
        ))
        legend_annotations.append(dict(
            xref="paper", yref="paper", x=x_start_esq + (i * delta_x) + 0.015, y=y_legend - 0.03,
            text=tempo, showarrow=False, font=dict(size=10), align="right"
        ))

    for i, tempo in enumerate(tempos):
        legend_shapes.append(dict(
            type="rect", xref="paper", yref="paper",
            x0=x_start_dir + (i * delta_shape), y0=y_legend - 0.03,
            x1=x_start_dir + (i * delta_shape) + 0.05, y1=y_legend + 0.03,
            fillcolor=tons_sofridos[i % len(tons_sofridos)], line=dict(width=0)
        ))
        legend_annotations.append(dict(
            xref="paper", yref="paper", x=x_start_dir + (i * delta_x) + 0.015, y=y_legend - 0.03,
            text=tempo, showarrow=False, font=dict(size=10), align="center"
        ))

    all_annotations = existing_annotations + legend_annotations

    fig = go.Figure(
        data=data,
        layout=go.Layout(
            barmode='relative', showlegend=False, height=600,
            xaxis=dict(
                showgrid=True, gridcolor='white', gridwidth=0.5,
                tickfont=dict(size=14), tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['100%', '50%', '0%', '50%', '100%'], range=[-1.03, 1.03],
            ),
            yaxis=dict(showgrid=True, tickfont=dict(size=13)),
            annotations=all_annotations, shapes=legend_shapes,
            margin=dict(r=150)
        )
    )
    return fig

def plotar_caracteristicas_gols_2_invertido(df_gols, equipe1, equipe2):
    """
    Plota um gráfico de barras horizontal empilhado comparando as características de gols
    sofridos por uma equipe e marcados por outra, divididos por tempo (quartos/prorrogação),
    com legendas personalizadas e eixos invertidos.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe (para gols sofridos).
        equipe2 (str): Nome da segunda equipe (para gols marcados).

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras empilhado de gols e legendas.
    """
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2)

    total_gs_e1 = int(gols_sofridos_e1.sum())
    total_gm_e2 = int(gols_marcados_e2.sum())

    tempos = gols_sofridos_e1.index.get_level_values(0).unique().tolist()
    labels = gols_sofridos_e1.index.get_level_values(1).unique().tolist()

    acumulado = np.zeros(len(labels))
    acumulado1 = acumulado.copy()

    tons_sofridos = ['#800000', '#FF9999', '#ff0000', '#FF6666', '#CC0000', '#E63939']
    tons_marcados = ['#003300', '#4dff4d', '#00A600', '#b3ffb3', '#00CC00', '#39E639']

    data = []

    for i, tempo in enumerate(tempos):
        valores = gols_sofridos_e1.loc[tempo].values
        percentual = valores / total_gs_e1 if total_gs_e1 != 0 else np.zeros_like(valores)
        valores1 = gols_marcados_e2.loc[tempo].values
        percentual1 = valores1 / total_gm_e2 if total_gm_e2 != 0 else np.zeros_like(valores1)

        cor_vermelho = tons_sofridos[i % len(tons_sofridos)]
        cor_verde = tons_marcados[i % len(tons_marcados)]

        data.append(go.Bar(
            name=f'{equipe1} - {tempo}', x=-percentual, y=labels, offsetgroup=1, base=-acumulado.copy(), orientation='h',
            text=[f"{valores[i]} ({(percentual[i]*100):.2f}%)" for i in range(len(valores))],
            textposition='inside', insidetextanchor='middle', marker_color=cor_vermelho, width=0.82,
        ))

        data.append(go.Bar(
            name=f'{equipe2} - {tempo}', x=percentual1, y=labels, offsetgroup=2, base=acumulado1.copy(), orientation='h',
            text=[f"({(percentual1[i]*100):.2f}%) {valores1[i]}" for i in range(len(valores1))],
            textposition='inside', insidetextanchor='middle', marker_color=cor_verde, width=0.822,
        ))

        acumulado += percentual
        acumulado1 += percentual1

    titulo_esquerda = f'Gols Sofridos {equipe1} (nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Marcados {equipe2} (nº de jogos: {jogos_e2})'

    existing_annotations = [
        dict(text=titulo_esquerda, x=0.4, y=1.2, xref='paper', yref='paper', xanchor='right', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
        dict(text='X', x=0.5, y=1.2, xref='paper', yref='paper', showarrow=False, font=dict(size=20, family="Arial Black")),
        dict(text=titulo_direita, x=0.6, y=1.2, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black"))
    ]

    legend_shapes = []
    legend_annotations = []

    y_legend = 1.07
    x_start_esq = 0.10
    x_start_dir = 0.6
    delta_x = 0.053
    delta_shape = 0.05

    for i, tempo in enumerate(reversed(tempos)):
        original_idx = len(tempos) - 1 - i
        legend_shapes.append(dict(
            type="rect", xref="paper", yref="paper",
            x0=x_start_esq + (i * delta_shape), y0=y_legend - 0.03,
            x1=x_start_esq + (i * delta_shape) + 0.05, y1=y_legend + 0.03,
            fillcolor=tons_sofridos[original_idx % len(tons_sofridos)], line=dict(width=0)
        ))
        legend_annotations.append(dict(
            xref="paper", yref="paper", x=x_start_esq + (i * delta_x) + 0.015, y=y_legend - 0.03,
            text=tempo, showarrow=False, font=dict(size=10), align="right"
        ))

    for i, tempo in enumerate(tempos):
        legend_shapes.append(dict(
            type="rect", xref="paper", yref="paper",
            x0=x_start_dir + (i * delta_shape), y0=y_legend - 0.03,
            x1=x_start_dir + (i * delta_shape) + 0.05, y1=y_legend + 0.03,
            fillcolor=tons_marcados[i % len(tons_marcados)], line=dict(width=0)
        ))
        legend_annotations.append(dict(
            xref="paper", yref="paper", x=x_start_dir + (i * delta_x) + 0.015, y=y_legend - 0.03,
            text=tempo, showarrow=False, font=dict(size=10), align="center"
        ))

    all_annotations = existing_annotations + legend_annotations

    fig = go.Figure(
        data=data,
        layout=go.Layout(
            barmode='relative', showlegend=False, height=600,
            xaxis=dict(
                showgrid=True, gridcolor='white', gridwidth=0.5,
                tickfont=dict(size=14), tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=['100%', '50%', '0%', '50%', '100%'], range=[-1.03, 1.03],
            ),
            yaxis=dict(showgrid=True, tickfont=dict(size=13)),
            annotations=all_annotations, shapes=legend_shapes,
            margin=dict(r=150)
        )
    )
    return fig

def plotar_caracteristicas_gols_invertido(df_gols, equipe1, equipe2):
    """
    Plota um gráfico de barras horizontal comparando as características de gols
    sofridos por uma equipe e marcados por outra, com eixos invertidos.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe (para gols sofridos).
        equipe2 (str): Nome da segunda equipe (para gols marcados).

    Returns:
        plotly.graph_objects.Figure: Uma figura Plotly com o gráfico de barras comparativo de gols invertido.
    """
    jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2 = extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2)

    labels = [
        "Total", "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]

    fig = go.Figure()

    values_gols_sofridos_e1 = gols_sofridos_e1.values
    total_gols_sofridos_e1 = sum(values_gols_sofridos_e1)
    values_gols_sofridos_e1 = np.insert(values_gols_sofridos_e1, 0, total_gols_sofridos_e1)
    percentual_gols_sofridos_e1 = values_gols_sofridos_e1 / total_gols_sofridos_e1 if total_gols_sofridos_e1 != 0 else np.zeros_like(values_gols_sofridos_e1)

    values_gols_marcados_e2 = gols_marcados_e2.values
    total_gols_marcados_e2 = sum(values_gols_marcados_e2)
    values_gols_marcados_e2 = np.insert(values_gols_marcados_e2, 0, total_gols_marcados_e2)
    percentual_gols_marcados_e2 = values_gols_marcados_e2 / total_gols_marcados_e2 if total_gols_marcados_e2 != 0 else np.zeros_like(values_gols_marcados_e2)

    fig.add_trace(go.Bar(
        y=labels, x=[-v for v in percentual_gols_sofridos_e1], name=f'Gols Sofridos {equipe1}', orientation='h',
        text=[f"{v} ({(v/total_gols_sofridos_e1)*100:.2f}%)" for v in values_gols_sofridos_e1],
        textposition='inside', insidetextanchor='start', marker=dict(color='rgb(214, 39, 40)'), width=0.82
    ))

    fig.add_trace(go.Bar(
        y=labels, x=percentual_gols_marcados_e2, name=f'Gols Marcados {equipe2}', orientation='h',
        text=[f"({(v/total_gols_marcados_e2)*100:.2f}%) {v}" for v in values_gols_marcados_e2],
        textposition='inside', insidetextanchor='start', marker=dict(color='rgb(44, 160, 44)'), width=0.82
    ))

    titulo_esquerda = f'Gols Sofridos {equipe1}(nº de jogos: {jogos_e1})'
    titulo_direita = f'Gols Marcados {equipe2}(nº de jogos:{jogos_e2})'

    fig.update_layout(
        showlegend=False, barmode='relative', height=600,
        xaxis=dict(
            showgrid=True, gridcolor='white', gridwidth=0.5,
            tickvals=[-1, -0.5, 0, 0.5, 1], ticktext=['100%', '50%', '0%', '50%', '100%'],
            range=[-1.03, 1.03], tickfont=dict(size=15)
        ),
        yaxis=dict(showgrid=True, tickfont=dict(size=14)),
        annotations=[
            dict(text=titulo_esquerda, x=0.4, y=1.1, xref='paper', yref='paper', xanchor='right', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black")),
            dict(text='X', x=0.5, y=1.1, xref='paper', yref='paper', showarrow=False, font=dict(size=20, family="Arial Black")),
            dict(text=titulo_direita, x=0.6, y=1.1, xref='paper', yref='paper', xanchor='left', yanchor='top', showarrow=False, font=dict(size=20, family="Arial Black"))
        ]
    )
    return fig

def extrair_dados_caracteristicas_gols(df_gols, equipe1, equipe2):
    """
    Extrai dados de características de gols (marcados e sofridos) para duas equipes
    e reindexa as Series resultantes para garantir categorias padronizadas.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe.
        equipe2 (str): Nome da segunda equipe.

    Returns:
        tuple: Uma tupla contendo:
               - int: Número de jogos da equipe 1.
               - pd.Series: Gols marcados pela equipe 1.
               - pd.Series: Gols sofridos pela equipe 1.
               - int: Número de jogos da equipe 2.
               - pd.Series: Gols marcados pela equipe 2.
               - pd.Series: Gols sofridos pela equipe 2.
    """
    caracteristicas_padrao = [
        "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]
    try:
        jogos_e1 = df_gols.loc[df_gols['Equipe Analisada'] == equipe1]['jogo_id'].nunique()
    except Exception:
        jogos_e1 = 0
    try:
        jogos_e2 = df_gols.loc[df_gols['Equipe Analisada'] == equipe2]['jogo_id'].nunique()
    except Exception:
        jogos_e2 = 0

    df_gols_group = df_gols.groupby(['Equipe Analisada', 'Tipo', 'Característica'])['Tipo'].count()

    def get_valor(df, chave):
        try:
            s = df.loc[chave]
        except KeyError:
            s = pd.Series(dtype=int)
        return s.reindex(caracteristicas_padrao, fill_value=0)

    gols_marcados_e1 = get_valor(df_gols_group, (equipe1, "Marcado"))
    gols_sofridos_e1 = get_valor(df_gols_group, (equipe1, "Sofrido"))
    gols_marcados_e2 = get_valor(df_gols_group, (equipe2, "Marcado"))
    gols_sofridos_e2 = get_valor(df_gols_group, (equipe2, "Sofrido"))

    return jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2

def extrair_dados_caracteristicas_gols_1(df_gols, equipe1, equipe2):
    """
    Extrai dados de características de gols (marcados e sofridos) para duas equipes,
    divididos por tempo (quartos/prorrogação), e reindexa as Series resultantes
    para garantir categorias e tempos padronizados.

    Args:
        df_gols (pd.DataFrame): DataFrame contendo os dados dos gols.
        equipe1 (str): Nome da primeira equipe.
        equipe2 (str): Nome da segunda equipe.

    Returns:
        tuple: Uma tupla contendo:
               - int: Número de jogos da equipe 1.
               - pd.Series: Gols marcados pela equipe 1, com MultiIndex (Tempo, Característica).
               - pd.Series: Gols sofridos pela equipe 1, com MultiIndex (Tempo, Característica).
               - int: Número de jogos da equipe 2.
               - pd.Series: Gols marcados pela equipe 2, com MultiIndex (Tempo, Característica).
               - pd.Series: Gols sofridos pela equipe 2, com MultiIndex (Tempo, Característica).
    """
    tempos = ['1ºQ', '2ºQ', '3ºQ', '4ºQ', '1ºP', '2ºP']
    caracteristicas_padrao = [
        "4x3", "3x4", "Ataque Posicional PA", "Ataque Posicional PB",
        "Goleiro Linha", "Defesa Goleiro Linha", "Goleiro no Jogo",
        "Escanteio", "Falta", "Lateral", "Pênalti", "Tiro de 10",
        "Gol Contra", "Transição Alta", "Transição Baixa"
    ]

    novo_index = pd.MultiIndex.from_product([tempos, caracteristicas_padrao], names=['Tempo', 'Característica'])

    try:
        jogos_e1 = df_gols.loc[df_gols['Equipe Analisada'] == equipe1]['jogo_id'].nunique()
    except Exception:
        jogos_e1 = 0
    try:
        jogos_e2 = df_gols.loc[df_gols['Equipe Analisada'] == equipe2]['jogo_id'].nunique()
    except Exception:
        jogos_e2 = 0

    df_gols_group = df_gols.groupby(['Equipe Analisada', 'Tipo', 'Tempo', 'Característica'])['Tipo'].count()

    def get_valor(df, chave):
        try:
            s = df.loc[chave]
        except KeyError:
            s = pd.Series(dtype=int)
        return s.reindex(novo_index, fill_value=0)

    gols_marcados_e1 = get_valor(df_gols_group, (equipe1, "Marcado"))
    gols_sofridos_e1 = get_valor(df_gols_group, (equipe1, "Sofrido"))
    gols_marcados_e2 = get_valor(df_gols_group, (equipe2, "Marcado"))
    gols_sofridos_e2 = get_valor(df_gols_group, (equipe2, "Sofrido"))

    return jogos_e1, gols_marcados_e1, gols_sofridos_e1, jogos_e2, gols_marcados_e2, gols_sofridos_e2


def exibir_seta(direcao="↑"):
    """
    Exibe um indicador visual com uma seta e o texto "ATAQUE" usando Markdown e CSS.

    Args:
        direcao (str, optional): O símbolo da seta a ser exibido. Padrão é "↑".
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
                transform: translateX(-120px);
            }}
            .texto-ataque {{
                font-size: 20px;
                font-weight: bold;
                margin-top: -10px;
                transform: translateX(-120px);
            }}
        </style>
        <div class="container-ataque">
            <div class="seta">{direcao}</div>
            <div class="texto-ataque">ATAQUE</div>
        </div>
        """, unsafe_allow_html=True)


def exibir_graficos_tempo(fig1, fig2, fig_barras, key_prefix,logo_path):
    """
    Exibe os gráficos principais para um período de tempo (análise de time),
    incluindo um logo e três figuras Plotly organizadas em colunas.

    Args:
        fig1 (plotly.graph_objects.Figure): Primeira figura Plotly (indicadores gerais).
        fig2 (plotly.graph_objects.Figure): Segunda figura Plotly (indicadores adicionais).
        fig_barras (plotly.graph_objects.Figure): Figura do gráfico de barras.
        key_prefix (str): Prefixo para as chaves únicas dos componentes Streamlit.
        logo_path (str, optional): Caminho para a imagem do logo. Padrão é "minas-tenis-clube-logo-png.png".
    """
    
    
    imagem = pegar_imagem_jogador(logo_path)
    
    col3, col4 = st.columns([1, 1.3])

    with col3:
        with st.container(border=True, height=500):
            sub_column1, sub_column2 = st.columns([1, 1.5])
            with sub_column1:
                if imagem is not None:
                    st.image(imagem, output_format="PNG", width=300)
            with sub_column2:
                with st.container(border=True, height=220):
                    st.plotly_chart(fig1, use_container_width=True, key=f"{key_prefix}_fig1", config={'displayModeBar': False})
            with st.container(border=True, height=230):
                st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_fig2", config={'displayModeBar': False})

    with col4:
        with st.container(border=True, height=500):
            st.plotly_chart(fig_barras, use_container_width=True, key=f"{key_prefix}_barras", config={'displayModeBar': False})


def exibir_jogadas(tipo, fig_espacamento, fig_barras, key_prefix):
    """
    Exibe gráficos de jogadas por tipo (ataque ou defesa) para análise de time,
    incluindo um gráfico de espaçamento e um gráfico de barras.

    Args:
        tipo (str): O tipo de jogada a ser exibido ("Ataque" ou "Defesa").
        fig_espacamento (plotly.graph_objects.Figure): Figura do gráfico de espaçamento.
        fig_barras (plotly.graph_objects.Figure): Figura do gráfico de barras.
        key_prefix (str): Prefixo para as chaves únicas dos componentes Streamlit.
    """
    st.subheader(f"Jogadas {tipo}")

    col1, col2 = st.columns([1.5, 1])
    with col1:
        with st.container(border=True, height=500):
            st.plotly_chart(fig_espacamento, use_container_width=True, key=f"{key_prefix}_espaco", config={'displayModeBar': False})
    with col2:
        with st.container(border=True, height=500):
            st.plotly_chart(fig_barras, use_container_width=True, key=f"{key_prefix}_barras", config={'displayModeBar': False})


def exibir_localizacao_jogadas_por_tempo(dados_time_df, tempo, key_prefix):
    """
    Exibe a localização das jogadas por tempo para o time, divididas em abas de "Ataque" e "Defesa",
    mostrando heatmaps da quadra.

    Args:
        dados_time_df (pd.DataFrame): DataFrame contendo os dados das jogadas do time.
        tempo (str): O período de tempo a ser analisado (ex: 'Primeiro Tempo', 'Segundo Tempo').
        key_prefix (str): Prefixo para as chaves únicas dos componentes Streamlit.
    """
    tab_ataque, tab_defesa = st.tabs(['Ataque', 'Defesa'])

    with tab_ataque:
        with st.container(border=True, height=300):
            colunas_jogadas_ofensivas = st.columns(5)
            figs = get_plots_plays_localization_team("Ataque", dados_time_df, tempo)
            for i, fig in enumerate(figs):
                colunas_jogadas_ofensivas[i].plotly_chart(fig, key=f"localizazao_{i}_time_tab_ataque_{key_prefix}", config={'displayModeBar': False})
    with tab_defesa:
        with st.container(border=True, height=600):
            colunas_jogadas_defensivas_1 = st.columns(3)
            colunas_jogadas_defensivas_2 = st.columns(3)
            figs = get_plots_plays_localization_team("Defesa", dados_time_df, tempo)

            for i in range(3):
                colunas_jogadas_defensivas_1[i].plotly_chart(figs[i], key=f"localizazao_{i}_time_tab_defesa_{key_prefix}", config={'displayModeBar': False})
            if len(figs) > 3:
                for i in range(3, len(figs)):
                    colunas_jogadas_defensivas_2[i-3].plotly_chart(figs[i], key=f"localizazao_1{i}_time_tab_defesa_{key_prefix}", config={'displayModeBar': False})


def exibir_localizacao_jogadas_por_tempo_jogador(dados_time_df, tempo, key_prefix,posicao):
    """
    Exibe a localização das jogadas por tempo para o time, divididas em abas de "Ataque" e "Defesa",
    mostrando heatmaps da quadra.

    Args:
        dados_time_df (pd.DataFrame): DataFrame contendo os dados das jogadas do time.
        tempo (str): O período de tempo a ser analisado (ex: 'Primeiro Tempo', 'Segundo Tempo').
        key_prefix (str): Prefixo para as chaves únicas dos componentes Streamlit.
        posicao (string): Posição do jogador.
    """
    tab_ataque, tab_defesa = st.tabs(['Ataque', 'Defesa'])
    if posicao == "Goleiro":
        height_container_defesa = 600
    else:   
        height_container_defesa = 300
    
    with tab_ataque:
        with st.container(border=True, height=300):
            colunas_jogadas_ofensivas = st.columns(5)
            figs = get_plots_plays_localization_athletes("Ataque", dados_time_df, tempo,posicao)
            for i, fig in enumerate(figs):
                colunas_jogadas_ofensivas[i].plotly_chart(fig, key=f"localizazao_{i}_time_tab_ataque_{key_prefix}", config={'displayModeBar': False})
    with tab_defesa:
        with st.container(border=True, height=height_container_defesa):
            colunas_jogadas_defensivas_1 = st.columns(3)
            colunas_jogadas_defensivas_2 = st.columns(3)
            figs = get_plots_plays_localization_athletes("Defesa", dados_time_df, tempo,posicao)

            for i in range(3):
                colunas_jogadas_defensivas_1[i].plotly_chart(figs[i], key=f"localizazao_{i}_time_tab_defesa_{key_prefix}", config={'displayModeBar': False})
            if len(figs) > 3:
                for i in range(3, len(figs)):
                    colunas_jogadas_defensivas_2[i-3].plotly_chart(figs[i], key=f"localizazao_1{i}_time_tab_defesa_{key_prefix}", config={'displayModeBar': False})



def exibir_localizacao_jogadas_total(dados_time_df):
    """
    Exibe a localização total das jogadas para o time, divididas em abas de "Ataque" e "Defesa",
    mostrando heatmaps da quadra para cada período de tempo (1ºT, 2ºT, Total).

    Args:
        dados_time_df (pd.DataFrame): DataFrame contendo os dados das jogadas do time.
    """
    jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró'], "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]}

    tab_ataque, tab_defesa = st.tabs(['Ataque', 'Defesa'])

    with tab_ataque:
        with st.container(border=True, height=1500):
            for jogada in jogadas['Ataque']:
                colunas = st.columns(3)
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_time_df, jogada)

                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    if i == 3: # Exibe apenas os 3 primeiros (1T, 2T, Total)
                        break
                    titulo = f"{jogada} - {chave}"
                    fig_localizacao_total = create_futsal_court(titulo, valor)
                    colunas[i].plotly_chart(fig_localizacao_total, key=f"localizacao_{jogada}_{chave}", config={'displayModeBar': False})

    with tab_defesa:
        with st.container(border=True, height=1800):
            for jogada in jogadas['Defesa']:
                colunas = st.columns(3)
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_time_df, jogada)

                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    if i == 3: # Exibe apenas os 3 primeiros (1T, 2T, Total)
                        break
                    titulo = f"{jogada} - {chave}"
                    fig_localizacao_total = create_futsal_court(titulo, valor)
                    colunas[i].plotly_chart(fig_localizacao_total, key=f"localizacao_{jogada}_{chave}", config={'displayModeBar': False})

def exibir_localizacao_jogadas_total_jogador(dados_time_df,posicao):
    """
    Exibe a localização total das jogadas para o time, divididas em abas de "Ataque" e "Defesa",
    mostrando heatmaps da quadra para cada período de tempo (1ºT, 2ºT, Total).

    Args:
        dados_time_df (pd.DataFrame): DataFrame contendo os dados das jogadas do time.
        posicao (string): Posiçao do jogador.
    """
    
    if posicao == "Goleiro":
        jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró'], 
                "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra', "FIN.S.C", "FIN.S.E", "FIN.S.T"]}
    else:
        jogadas = {"Ataque": ['FIN.C', 'FIN.E', 'FIN.T', 'DES.C/P.', 'C.A.-Pró'],
                   "Defesa": ['DES.S/P.', 'PER.P.', 'C.A.-Contra']}

        
    tab_ataque, tab_defesa = st.tabs(['Ataque', 'Defesa'])

    with tab_ataque:
        with st.container(border=True, height=1500):
            for jogada in jogadas['Ataque']:
                colunas = st.columns(3)
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_time_df, jogada)

                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    if i == 3: # Exibe apenas os 3 primeiros (1T, 2T, Total)
                        break
                    titulo = f"{jogada} - {chave}"
                    fig_localizacao_total = create_futsal_court(titulo, valor)
                    colunas[i].plotly_chart(fig_localizacao_total, key=f"localizacao_{jogada}_{chave}", config={'displayModeBar': False})

    with tab_defesa:
        with st.container(border=True, height=1800):
            for jogada in jogadas['Defesa']:
                colunas = st.columns(3)
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_time_df, jogada)

                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    if i == 3: # Exibe apenas os 3 primeiros (1T, 2T, Total)
                        break
                    titulo = f"{jogada} - {chave}"
                    fig_localizacao_total = create_futsal_court(titulo, valor)
                    colunas[i].plotly_chart(fig_localizacao_total, key=f"localizacao_{jogada}_{chave}", config={'displayModeBar': False})


def pegar_figuras_e_estatisticas_jogadores(df_analise, df_media, estatisticas_gerais_para_radar,posicao):
    """
    Calcula estatísticas e gera figuras para um DataFrame específico do jogador (df_analise),
    comparando com uma média de referência (df_media) e estatísticas gerais para o radar.

    Args:
        df_analise (pd.DataFrame): DataFrame com os dados a serem analisados para o jogador.
        df_media (pd.DataFrame): DataFrame com os dados para calcular as médias de comparação.
        estatisticas_gerais_para_radar (dict): Dicionário de estatísticas gerais (da equipe ou todos os jogadores)
                                                para a comparação no gráfico de radar, estruturado por período.
        posicao (str): Posiçao jogador.
    Returns:
        dict: Um dicionário contendo tuplas de figuras e rótulos para cada aba.
    """
    numero_jogos_jogador = df_analise["jogo_id"].nunique() if df_analise["jogo_id"].nunique() > 0 else 1

    estatisticas_pt, estatisticas_st, estatisticas_total, estatisticas_ptp, estatisticas_stp = \
        extrair_estatisticas_gerais(df_analise)

    media_pt, media_st, media_total, media_ptp, media_stp = get_mean(df_media)

    # Para a aba 'Total':
    fig_total_1, fig_total_2, bar_total, radar_total = get_athletes_total_figures(
        estatisticas_total, estatisticas_pt, estatisticas_st, estatisticas_gerais_para_radar['Total'], numero_jogos_jogador, media_pt, media_st,posicao
    )
    # Para a aba 'Primeiro Tempo':
    fig_pt_1, fig_pt_2, bar_pt, radar_pt = get_athletes_partial_figures(
        estatisticas_pt, estatisticas_gerais_para_radar['Primeiro Tempo'], numero_jogos_jogador, media_pt,posicao
    )
    # Para a aba 'Segundo Tempo':
    fig_st_1, fig_st_2, bar_st, radar_st = get_athletes_partial_figures(
        estatisticas_st, estatisticas_gerais_para_radar['Segundo Tempo'], numero_jogos_jogador, media_st,posicao
    )

    return {
        "Primeiro Tempo": (fig_pt_1, fig_pt_2, bar_pt, radar_pt, "Primeiro Tempo"),
        "Segundo Tempo": (fig_st_1, fig_st_2, bar_st, radar_st, "Segundo Tempo"),
        "Total": (fig_total_1, fig_total_2, bar_total, radar_total, "Total"),
    }

def exibir_conteudo_tabs_jogadores(nome_tab, figuras, df,logo_path,posicao):
    """
    Exibe o conteúdo nas abas do Streamlit com os gráficos e dados do jogador por tempo.

    Args:
        figuras_estatisticas_jogador (dict): Dicionário com tuplas de figuras por tempo.
        dados_time_df (pd.DataFrame): DataFrame com dados da equipe no jogo.
        posicao (str): Posição do jogador.
    """
   

    
    fig1, fig2, bar_fig,radar_fig, tempo_label = figuras
    exibir_graficos_tempo(fig1, fig2, bar_fig,nome_tab,logo_path)
    with st.container(border=True, height=500):
        st.plotly_chart(radar_fig, use_container_width=True, key=f"{tempo_label}_radar", config={'displayModeBar': False})
    st.subheader("Localização Jogadas")
    if tempo_label == "Total":
        exibir_localizacao_jogadas_total_jogador(df,posicao)
    else:
        exibir_localizacao_jogadas_por_tempo_jogador(df, tempo_label,nome_tab,posicao)   



def pegar_figuras_e_estatisticas(df_para_analisar, df_para_media):
    """
    Calcula estatísticas e gera figuras para um DataFrame específico (df_to_analyze),
    comparando com uma média de referência (df_for_mean).

    Args:
        df_para_analisar (pd.DataFrame): DataFrame com os dados a serem analisados (ex: dados de um único jogo).
        df_for_mean (pd.DataFrame): DataFrame com os dados para calcular as médias de comparação.

    Returns:
        dict: Um dicionário contendo tuplas de figuras e rótulos para cada aba.
    """
    # Garante que o número de jogos é pelo menos 1 para evitar divisão por zero
    numero_jogos = df_para_analisar["jogo_id"].nunique() if df_para_analisar["jogo_id"].nunique() > 0 else 1
    # Conta jogos com prorrogação (1ºP ou 2ºP)
    numero_jogos_prorrogacao = df_para_analisar[df_para_analisar["tempo"].isin(["1ºP", "2ºP"])]["jogo_id"].nunique()
    numero_jogos_prorrogacao = numero_jogos_prorrogacao if numero_jogos_prorrogacao > 0 else 1

    # Extrai estatísticas gerais para o DataFrame a ser analisado
    estatisticas_pt, estatisticas_st, estatisticas_total, estatisticas_ptp, estatisticas_stp = \
        extrair_estatisticas_gerais(df_para_analisar)

    # Calcula as médias de comparação usando o DataFrame de referência
    mean_pt, mean_st, mean_total, mean_ptp, mean_stp = get_mean(df_para_media)

    # Geração das figuras para cada aba
    fig_total_1, fig_total_2, bar_total = get_team_total_figures(
        estatisticas_total, estatisticas_pt, estatisticas_st, numero_jogos, mean_pt, mean_st
    )
    fig_pt_1, fig_pt_2, bar_pt = get_team_partial_figures(
        estatisticas_pt, numero_jogos, mean_pt
    )
    fig_st_1, fig_st_2, bar_st = get_team_partial_figures(
        estatisticas_st, numero_jogos, mean_st
    )
    fig_ptp_1, fig_ptp_2, bar_ptp = get_team_partial_figures(
        estatisticas_ptp, numero_jogos_prorrogacao, mean_ptp
    )
    fig_stp_1, fig_stp_2, bar_stp = get_team_partial_figures(
        estatisticas_stp, numero_jogos_prorrogacao, mean_stp
    )

    return {
        "Primeiro Tempo": (fig_pt_1, fig_pt_2, bar_pt, "Primeiro Tempo"),
        "Segundo Tempo": (fig_st_1, fig_st_2, bar_st, "Segundo Tempo"),
        "Total": (fig_total_1, fig_total_2, bar_total, "Total"),
        "Primeiro Tempo Prorrogação": (fig_ptp_1, fig_ptp_2, bar_ptp, "Primeiro Tempo Prorrogação"),
        "Segundo Tempo Prorrogação": (fig_stp_1, fig_stp_2, bar_stp, "Segundo Tempo Prorrogação")
    }

def exibir_conteudo_tab(nome_tab, figuras, df,logo_path):
    """
    Exibe o conteúdo de uma aba específica (gráficos e localização de jogadas).

    Args:
        tab_name (str): Nome da aba.
        figures (tuple): Tupla contendo as figuras Plotly para a aba.
        df (pd.DataFrame): DataFrame com os dados atuais para a localização das jogadas.
    """
    fig1, fig2, bar_fig, tempo_label = figuras
    exibir_graficos_tempo(fig1, fig2, bar_fig,nome_tab,logo_path)
    st.subheader("Localização Jogadas")
    if tempo_label == "Total":
        exibir_localizacao_jogadas_total(df)
    else:
        exibir_localizacao_jogadas_por_tempo(df, tempo_label, key_prefix=nome_tab)            