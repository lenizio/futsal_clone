import streamlit as st
import pandas as pd
from db_manager import DBManager
import plotly.graph_objects as go
from utils import extrair_dataframe_jogador, extrair_estatisticas_jogadores,plotar_estatisticas_gerais,extrair_estatisticas_gerais,plotar_grafico_barras,plotar_historico,plotar_radar_chart

# Inicialização do gerenciador de banco de dados
db_manager = DBManager()

# Obter lista de jogadores
lista_atletas = db_manager.listar_nome_id_jogadores_por_equipe(1)
jogadores_dict = {jogador[1]: jogador[0] for jogador in lista_atletas}
nomes_jogadores_list = list(jogadores_dict.keys())

# Inicializar session_state para os filtros
if "filtro_jogador" not in st.session_state:
    st.session_state.filtro_jogador = None
if "filtro_competicao" not in st.session_state:
    st.session_state.filtro_competicao = None
if "filtro_partida" not in st.session_state:
    st.session_state.filtro_partida = None

# Botão de refresh
if st.button("Atualizar Dados"):
    # Apenas redefine os dados, mas mantém os filtros
    st.session_state.dados_atualizados = True

# Container para os filtros
filter_container = st.container()

# Inicialização das variáveis
dados_jogador_df = extrair_dataframe_jogador(db_manager)
dados_todos_jogadores_df = dados_jogador_df.copy()
options_competicao = []
options_partidas = []
estatisticas_gerais_fig = go.Figure()
grafico_barras_fig = go.Figure()
historico_fig = go.Figure()
radar_fig = go.Figure()

with filter_container:
    col1, col2, col3 = st.columns([1, 1, 2])
    # Filtro por jogador
    with col1:
        filtro_jogador = st.selectbox(
            "Selecione um jogador",
            options=nomes_jogadores_list,
            index=nomes_jogadores_list.index(st.session_state.filtro_jogador) if st.session_state.filtro_jogador else None,
        )
        if filtro_jogador:
            st.session_state.filtro_jogador = filtro_jogador
            jogador_id = jogadores_dict[filtro_jogador]
            estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
            dados_jogador_df = dados_jogador_df[dados_jogador_df['jogador_nome'] == filtro_jogador]
            estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
            estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_totais_dict)
            grafico_barras_fig = plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict)
            historico_fig = plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict)
            radar_fig = plotar_radar_chart(estatisticas_totais_dict,estatisticas_geral_totais_dict)
            options_competicao = dados_jogador_df["competicao"].unique().tolist()

    # Filtro por competição
    with col2:
        if not dados_jogador_df.empty:
            filtro_competicao = st.selectbox(
                "Selecione uma competição",
                options=options_competicao,
                index=options_competicao.index(st.session_state.filtro_competicao) if st.session_state.filtro_competicao else None,
            )
            if filtro_competicao:
                st.session_state.filtro_competicao = filtro_competicao
                dados_jogador_df = dados_jogador_df[dados_jogador_df['competicao'] == filtro_competicao]
                dados_todos_jogadores_df = dados_todos_jogadores_df[dados_todos_jogadores_df['competicao'] == filtro_competicao]
                estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
                estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_totais_dict)
                grafico_barras_fig = plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict)
                historico_fig = plotar_historico(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict)
                radar_fig = plotar_radar_chart(estatisticas_totais_dict,estatisticas_geral_totais_dict)               
                options_partidas = dados_jogador_df["partida"].unique().tolist()

    # Filtro por partida
    with col3:
        if not dados_jogador_df.empty:
            filtro_partida = st.selectbox(
                "Selecione uma partida",
                options=options_partidas,
                index=options_partidas.index(st.session_state.filtro_partida) if st.session_state.filtro_partida else None,
            )
            if filtro_partida:
                st.session_state.filtro_partida = filtro_partida
                dados_jogador_df = dados_jogador_df[dados_jogador_df['partida'] == filtro_partida]
                dados_todos_jogadores_df = dados_todos_jogadores_df[dados_todos_jogadores_df['partida'] == filtro_partida]
                estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
                estatisticas_gerais_fig = plotar_estatisticas_gerais(estatisticas_totais_dict)
                grafico_barras_fig = plotar_grafico_barras(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict)
                radar_fig = plotar_radar_chart(estatisticas_totais_dict,estatisticas_geral_totais_dict)


    # # Exibir DataFrame atualizado
    # if not dados_jogador_df.empty:
    #     st.dataframe(estatisticas_jogadores_df)

    
if filtro_jogador:

    col3, col4 = st.columns([1,1])

    with col3:
        with st.container(border=True,height=500):
            st.plotly_chart(estatisticas_gerais_fig, use_container_width=True, key="grafico_geral")

    with col4:
        with st.container(border=True,height=500):
            st.plotly_chart(grafico_barras_fig, use_container_width=True, key="grafico_barras")          
                
    col5, col6 = st.columns(2)
    with col5:
        with st.container(border=True,height=500):
            st.plotly_chart(historico_fig, use_container_width=True, key="grafico_historico")

    with col6:
        with st.container(border=True, height=500):
            st.plotly_chart(radar_fig, use_container_width=True, key="grafico_radar")
        
                  