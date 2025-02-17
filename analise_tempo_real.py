import streamlit as st
import pandas as pd
from db_manager import DBManager, get_db_manager    
import plotly.graph_objects as go
import atexit

from utils import *

# Inicialização do gerenciador de banco de dados
db_manager = get_db_manager()

# Inicializar session_state para os filtros
if "filtro_competicao_time" not in st.session_state:
    st.session_state.filtro_competicao_time = None
if "filtro_partida_time" not in st.session_state:
    st.session_state.filtro_partida_time = None

# Botão de refresh
if st.button("Atualizar Dados"):
    # Apenas redefine os dados, mas mantém os filtros
    st.session_state.dados_atualizados = True

# Container para os filtros
filter_container = st.container()

# Inicialização das variáveis
dados_todos_jogadores_df = extrair_dataframe_jogador(db_manager)
options_competicao = []
options_partidas = []
estatisticas_gerais_fig = go.Figure()
estatisticas_gerais_fig_1 = go.Figure()
grafico_barras_fig = go.Figure()
historico_fig = go.Figure()

if not dados_todos_jogadores_df.empty:
    options_competicao = dados_todos_jogadores_df["competicao"].unique().tolist()
    numero_jogos = int(dados_todos_jogadores_df["jogo_id"].nunique())
    estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
    estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_geral_totais_dict,numero_jogos)
    estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_geral_totais_dict)
    grafico_barras_fig = plotar_grafico_barras(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,)
    historico_fig = plotar_historico_time(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,numero_jogos)
    

with filter_container:
    col1, col2 = st.columns([1, 1])
    # Filtro por competição
    with col1:
        if not dados_todos_jogadores_df.empty:
            filtro_competicao_time = st.selectbox(
                "Selecione uma competição",
                options=options_competicao,
                index=options_competicao.index(st.session_state.filtro_competicao_time) if st.session_state.filtro_competicao_time else None,
            )
            if filtro_competicao_time:
                if filtro_competicao_time != st.session_state.filtro_competicao_time:
                    st.session_state.filtro_partida_time = None
                st.session_state.filtro_competicao_time = filtro_competicao_time
                dados_todos_jogadores_df = dados_todos_jogadores_df[dados_todos_jogadores_df['competicao'] == filtro_competicao_time]
                numero_jogos = int(dados_todos_jogadores_df["jogo_id"].nunique())
                estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_geral_totais_dict,numero_jogos)
                estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_geral_totais_dict)
                grafico_barras_fig = plotar_grafico_barras(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,)
                historico_fig = plotar_historico_time(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,numero_jogos)
                options_partidas = dados_todos_jogadores_df["partida"].unique().tolist()
                
                if st.session_state.filtro_partida_time is not None and st.session_state.filtro_partida_time not in options_partidas:
                    filtro_partida_time = None
                    st.session_state.filtro_partida_time = None

    # Filtro por partida
    with col2:
        if not dados_todos_jogadores_df.empty:
            filtro_partida_time = st.selectbox(
                "Selecione uma partida",
                options=options_partidas,
                index=options_partidas.index(st.session_state.filtro_partida_time) if st.session_state.filtro_partida_time else None,
            )
            if filtro_partida_time:
                st.session_state.filtro_partida_time = filtro_partida_time
                dados_todos_jogadores_df = dados_todos_jogadores_df[dados_todos_jogadores_df['partida'] == filtro_partida_time]
                estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_gerais_fig = plotar_estatisticas_gerais_time(estatisticas_geral_totais_dict,1)
                estatisticas_gerais_fig_1 = plotar_estatisticas_gerais_1(estatisticas_geral_totais_dict)
                grafico_barras_fig = plotar_grafico_barras(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,)

if not dados_todos_jogadores_df.empty:
    col3, col4 = st.columns([1,1])

    with col3:
        with st.container(border=True,height=500):
            sub_column1,sub_column2 = st.columns([1,1])
            with sub_column1:
                st.image("logo_minas.png", width=250)
            with sub_column2:
                st.plotly_chart(estatisticas_gerais_fig, use_container_width=False, key="grafico_geral")
            st.plotly_chart(estatisticas_gerais_fig_1, use_container_width=False)
    
    with col4:
        with st.container(border=True,height=500):
            st.plotly_chart(grafico_barras_fig, use_container_width=True, key="grafico_barras")
    
    with st.container(border=True,height=500):
        st.plotly_chart(historico_fig, use_container_width=True, key="grafico_historico")
    
    filtro_jogada_time = st.selectbox(
                "Selecione uma jogada",
                options=['FIN.C', 'FIN.E', 'FIN.T', 'ASSIST.', 'GOL', 'DES.C/P.', 'DES.S/P.', 'PER.P', 'C.A'],
                index=None,
            )       
    
    if filtro_jogada_time:
        with st.container(border=True, height=550):
            colunas = st.columns(3) 
            localizacao_jogadas = extrair_estatisticas_localizacao(dados_todos_jogadores_df,filtro_jogada_time)
            
            for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                titulo = f"{filtro_jogada_time} - {chave}"
                fig = create_futsal_court(titulo,valor)
                colunas[i].plotly_chart(fig)

if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)
