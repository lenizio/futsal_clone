import streamlit as st
import pandas as pd
from db_manager import DBManager, get_db_manager    
import plotly.graph_objects as go
import atexit

from utils import *

# Inicialização do gerenciador de banco de dados
db_manager = get_db_manager()

# Obter lista de jogadores
lista_atletas = db_manager.listar_jogadores_por_equipe(1)
jogadores_dict = {jogador[1]: [jogador[0],jogador[4]] for jogador in lista_atletas}
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
#Figuras tab total
estatisticas_gerais_total_fig = go.Figure()
estatisticas_gerais_total_fig_1 = go.Figure()
grafico_barras_total_fig = go.Figure()
historico_total_fig = go.Figure()
radar_total_fig = go.Figure()

#Figuras tab primeiro tempo
estatisticas_gerais_pt_fig = go.Figure()
estatisticas_gerais_pt_fig_1 = go.Figure()
grafico_barras_pt_fig = go.Figure()
historico_pt_fig = go.Figure()
radar_pt_fig = go.Figure()

#Figuras tab segundo tempo
estatisticas_gerais_st_fig = go.Figure()
estatisticas_gerais_st_fig_1 = go.Figure()
grafico_barras_st_fig = go.Figure()
historico_st_fig = go.Figure()
radar_st_fig = go.Figure()

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
            jogador_id = jogadores_dict[filtro_jogador][0]
            image_id = jogadores_dict[filtro_jogador][1]
            image_jogador= pegar_imagem_jogador(image_id)
            estatisticas_geral_pt_dict,estatisticas_geral_st_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
            numero_jogos = int(dados_todos_jogadores_df["jogo_id"].nunique())
            dados_jogador_df = dados_jogador_df[dados_jogador_df['jogador_nome'] == filtro_jogador]
            estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
            
            mean_primeiro_tempo, mean_segundo_tempo,mean_total   = get_mean(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_totais_dict,numero_jogos)
            #Figuras tab total
            estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig,radar_total_fig, historico_total_fig = get_athletes_total_figures(estatisticas_totais_dict,estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_geral_totais_dict,numero_jogos,True) 
            #Figuras tab primeiro tempo
            estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig, radar_pt_fig= get_athletes_partial_figures(estatisticas_primeiro_tempo_dict,estatisticas_geral_pt_dict,numero_jogos,mean_primeiro_tempo,False) 
            #Figuras tab segundo tempo
            estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig,radar_st_fig = get_athletes_partial_figures(estatisticas_segundo_tempo_dict,estatisticas_geral_st_dict,numero_jogos,mean_segundo_tempo,False)
            
            
            options_competicao = dados_jogador_df["competicao"].unique().tolist()
            
            if st.session_state.filtro_competicao is not None and st.session_state.filtro_competicao not in options_competicao:
                filtro_competicao = None
                st.session_state.filtro_competicao = None
                filtro_partida=None
                st.session_state.filtro_partida = None

    # Filtro por competição
    with col2:
        if not dados_jogador_df.empty:
            filtro_competicao = st.selectbox(
                "Selecione uma competição",
                options=options_competicao,
                index=options_competicao.index(st.session_state.filtro_competicao) if st.session_state.filtro_competicao else None,
            )
            if filtro_competicao:
                if filtro_competicao != st.session_state.filtro_competicao:
                    st.session_state.filtro_partida = None
                st.session_state.filtro_competicao = filtro_competicao
                dados_jogador_df = dados_jogador_df[dados_jogador_df['competicao'] == filtro_competicao]
                dados_todos_jogadores_df = dados_todos_jogadores_df[dados_todos_jogadores_df['competicao'] == filtro_competicao]
                numero_jogos = int(dados_todos_jogadores_df["jogo_id"].nunique())
                estatisticas_geral_pt_dict,estatisticas_geral_st_dict,  estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
                
                mean_primeiro_tempo, mean_segundo_tempo,mean_total   = get_mean(estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_totais_dict,numero_jogos)
                #Figuras tab total
                estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig,radar_total_fig, historico_total_fig = get_athletes_total_figures(estatisticas_totais_dict,estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_geral_totais_dict,numero_jogos,True) 
                #Figuras tab primeiro tempo
                estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig, radar_pt_fig= get_athletes_partial_figures(estatisticas_primeiro_tempo_dict,estatisticas_geral_pt_dict,numero_jogos,mean_primeiro_tempo,False) 
                #Figuras tab segundo tempo
                estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig,radar_st_fig = get_athletes_partial_figures(estatisticas_segundo_tempo_dict,estatisticas_geral_st_dict,numero_jogos,mean_segundo_tempo,False)
                          
                
                options_partidas = dados_jogador_df["partida"].unique().tolist()
                
                if st.session_state.filtro_partida is not None and st.session_state.filtro_partida not in options_partidas:
                    filtro_partida=None
                    st.session_state.filtro_partida = None

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
                estatisticas_geral_pt_dict,estatisticas_geral_st_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict, estatisticas_totais_dict = extrair_estatisticas_gerais(dados_jogador_df)
                #Figuras tab total
                estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig,radar_total_fig, historico_total_fig = get_athletes_total_figures(estatisticas_totais_dict,estatisticas_primeiro_tempo_dict, estatisticas_segundo_tempo_dict,estatisticas_geral_totais_dict,1,True) 
                #Figuras tab primeiro tempo
                estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig, radar_pt_fig= get_athletes_partial_figures(estatisticas_primeiro_tempo_dict,estatisticas_geral_pt_dict,1,mean_primeiro_tempo,False) 
                #Figuras tab segundo tempo
                estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig,radar_st_fig = get_athletes_partial_figures(estatisticas_segundo_tempo_dict,estatisticas_geral_st_dict,1,mean_segundo_tempo,False)
            


    # # Exibir DataFrame atualizado
    # if not dados_jogador_df.empty:
    #     st.dataframe(estatisticas_jogadores_df)

    
if filtro_jogador:
    
    
    primeiro_tempo_tab, segundo_tempo_tab, total_tab = st.tabs(["Primeiro Tempo", "Segundo Tempo", "Total"])
    
    with primeiro_tempo_tab:
        col3_pt, col4_pt = st.columns([1, 1])

        with col3_pt:
            with st.container(border=True, height=500):
                sub_column1_pt, sub_column2_pt = st.columns([1, 1])
                with sub_column1_pt:
                    if image_jogador is not None:
                        st.image(image_jogador, width=250)
                with sub_column2_pt:
                    st.plotly_chart(estatisticas_gerais_pt_fig, use_container_width=False, key="estatisticas_gerais_pt_fig")
                st.plotly_chart(estatisticas_gerais_pt_fig_1, use_container_width=False, key="estatisticas_gerais_pt_fig_1")

        with col4_pt:
            with st.container(border=True, height=500):
                st.plotly_chart(grafico_barras_pt_fig, use_container_width=True, key="grafico_barras_pt")

        col5_pt, col6_pt = st.columns(2)
        with col5_pt:
            with st.container(border=True, height=500):
                st.plotly_chart(radar_pt_fig, use_container_width=True, key="grafico_radar_pt")

        filtro_jogada_pt = st.selectbox(
            "Selecione o tipo de jogada",
            options=["Ataque","Defesa"],
            index=None,
            key="localizacao_jogada_pt"
        )

        if filtro_jogada_pt:
            with st.container(border=True, height=550):
                colunas_jogadas_ofensivas = st.columns(3)
                colunas_jogadas_defensivas = st.columns(5)
                colunas= {"Ataque": colunas_jogadas_ofensivas, "Defesa":colunas_jogadas_defensivas}  
                figs= get_plots_plays_localization_partial(filtro_jogada_pt,dados_todos_jogadores_df,"Primeiro Tempo")
                
                for i,fig in enumerate(figs):
                    colunas[filtro_jogada_pt][i].plotly_chart(fig,key=f"localizazao_{i}_time_tab_pt")

    with segundo_tempo_tab:
        col3_st, col4_st = st.columns([1, 1])

        with col3_st:
            with st.container(border=True, height=500):
                sub_column1_st, sub_column2_st = st.columns([1, 1])
                with sub_column1_st:
                    if image_jogador is not None:
                        st.image(image_jogador, width=250)
                with sub_column2_st:
                    st.plotly_chart(estatisticas_gerais_st_fig, use_container_width=False, key="estatisticas_gerais_st_fig")
                st.plotly_chart(estatisticas_gerais_st_fig_1, use_container_width=False, key="estatisticas_gerais_st_fig_1")

        with col4_st:
            with st.container(border=True, height=500):
                st.plotly_chart(grafico_barras_st_fig, use_container_width=True, key="grafico_barras_st")

        col5_st, col6_st = st.columns(2)
        with col5_st:
            with st.container(border=True, height=500):
                st.plotly_chart(radar_st_fig, use_container_width=True, key="grafico_radar_st")

        filtro_jogada_st = st.selectbox(
            "Selecione o tipo de  jogada",
            options=["Ataque","Defesa"],
            index=None,
            key="localizacao_jogada_st"
        )

        if filtro_jogada_st:
            with st.container(border=True, height=550):
                colunas_jogadas_ofensivas = st.columns(3)
                colunas_jogadas_defensivas = st.columns(5)
                colunas= {"Ataque": colunas_jogadas_ofensivas, "Defesa":colunas_jogadas_defensivas}  
                figs= get_plots_plays_localization_partial(filtro_jogada_st,dados_todos_jogadores_df,"Segundo Tempo")
                
                for i,fig in enumerate(figs):
                    colunas[filtro_jogada_st][i].plotly_chart(fig,key=f"localizazao_{i}_time_tab_st")

    with total_tab:

        col3, col4 = st.columns([1,1])

        with col3:
            with st.container(border=True,height=500):
                sub_column1,sub_column2 = st.columns([1,1])
                with sub_column1:
                # Exibe a imagem do jogador na primeira coluna
                    if image_jogador is not None:
                        st.image(image_jogador, width=250)

                with sub_column2:
                    # Adiciona um espaçamento antes do gráfico, se necessário
                    # Renderiza o gráfico de estatísticas gerais
                    st.plotly_chart(estatisticas_gerais_total_fig, use_container_width=False, key="estatisticas_gerais_total_fig")
                st.plotly_chart(estatisticas_gerais_total_fig_1, use_container_width=False,key="estatisticas_gerais_pt_total_1")
        
        with col4:
            with st.container(border=True,height=500):
                st.plotly_chart(grafico_barras_total_fig, use_container_width=True, key="grafico_barras_total")          
                    
        col5, col6 = st.columns(2)
        with col5:
            with st.container(border=True,height=500):
                st.plotly_chart(historico_total_fig, use_container_width=True, key="grafico_historico_total")

        with col6:
            with st.container(border=True, height=500):
                
                st.plotly_chart(radar_total_fig, use_container_width=True, key="grafico_radar_total")
        
        
        
        
        filtro_jogada = st.selectbox(
                    "Selecione uma jogada",
                    options=['FIN.C', 'FIN.E', 'FIN.T', 'ASSIST.', 'GOL', 'DES.C/P.', 'DES.S/P.', 'PER.P', 'C.A'],
                    index=None,
                    key="localizacao_jogada_total"
                )       
        
        if filtro_jogada:
            with st.container(border=True, height=550):
                colunas = st.columns(3) 
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_jogador_df,filtro_jogada)
                
                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    titulo = f"{filtro_jogada} - {chave}"
                    fig = create_futsal_court(titulo,valor)
                    colunas[i].plotly_chart(fig)
                
   
    
                

      
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)                   