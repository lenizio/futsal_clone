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
#Figuras tab total
estatisticas_gerais_total_fig = go.Figure()
estatisticas_gerais_total_fig_1 = go.Figure()
grafico_barras_total_fig = go.Figure()
historico_total_fig = go.Figure()
#Figuras tab primeiro tempo
estatisticas_gerais_pt_fig = go.Figure()
estatisticas_gerais_pt_fig_1 = go.Figure()
grafico_barras_pt_fig = go.Figure()
historico_pt_fig = go.Figure()
#Figuras tab segundo tempo
estatisticas_gerais_st_fig = go.Figure()
estatisticas_gerais_st_fig_1 = go.Figure()
grafico_barras_st_fig = go.Figure()
historico_st_fig = go.Figure()


if not dados_todos_jogadores_df.empty:
    options_competicao = dados_todos_jogadores_df["competicao"].unique().tolist()
    numero_jogos = int(dados_todos_jogadores_df["jogo_id"].nunique())
    estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
    mean_primeiro_tempo, mean_segundo_tempo,mean_total   = get_mean(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,estatisticas_geral_totais_dict,numero_jogos)
    #Figuras tab total
    estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig, historico_total_fig = get_team_total_figures(estatisticas_geral_totais_dict,estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_primeiro_tempo, mean_segundo_tempo,True) 
    #Figuras tab primeiro tempo
    estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig = get_team_partial_figures(estatisticas_geral_primeiro_tempo_dict,numero_jogos,mean_primeiro_tempo,False) 
    #Figuras tab segundo tempo
    estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig = get_team_partial_figures(estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_segundo_tempo,False) 

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
                mean_primeiro_tempo, mean_segundo_tempo,mean_total   = get_mean(estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,estatisticas_geral_totais_dict,numero_jogos)
                #Figuras tab total
                estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig, historico_total_fig = get_team_total_figures(estatisticas_geral_totais_dict,estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_primeiro_tempo, mean_segundo_tempo,True) 
                #Figuras tab primeiro tempo
                estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig = get_team_partial_figures(estatisticas_geral_primeiro_tempo_dict,numero_jogos,mean_primeiro_tempo,False) 
                #Figuras tab segundo tempo
                estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig = get_team_partial_figures(estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_segundo_tempo,False)
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
                
                estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict, estatisticas_geral_totais_dict = extrair_estatisticas_gerais(dados_todos_jogadores_df)
                #Figuras tab total
                estatisticas_gerais_total_fig, estatisticas_gerais_total_fig_1,  grafico_barras_total_fig, historico_total_fig = get_team_total_figures(estatisticas_geral_totais_dict,estatisticas_geral_primeiro_tempo_dict, estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_primeiro_tempo, mean_segundo_tempo,True) 
                #Figuras tab primeiro tempo
                estatisticas_gerais_pt_fig, estatisticas_gerais_pt_fig_1,  grafico_barras_pt_fig = get_team_partial_figures(estatisticas_geral_primeiro_tempo_dict,numero_jogos,mean_primeiro_tempo,False) 
                #Figuras tab segundo tempo
                estatisticas_gerais_st_fig, estatisticas_gerais_st_fig_1,  grafico_barras_st_fig = get_team_partial_figures(estatisticas_geral_segundo_tempo_dict,numero_jogos,mean_segundo_tempo,False)


if not dados_todos_jogadores_df.empty:
    
    primeiro_tempo_tab, segundo_tempo_tab, total_tab = st.tabs(["Primeiro Tempo", "Segundo Tempo", "Total"])
    
    with primeiro_tempo_tab:
        
        col3, col4 = st.columns([1,1])

        with col3:
            with st.container(border=True,height=500):
                sub_column1,sub_column2 = st.columns([1,1.5])
                with sub_column1:
                    st.image("minas-tenis-clube-logo-png.png",output_format="PNG", width=300)
                with sub_column2:
                    with st.container(border=True, height=220):
                        st.plotly_chart(estatisticas_gerais_pt_fig, use_container_width=True, key="estatisticas_gerais_pt_fig",config={'displayModeBar': False})
                with st.container(border=True, height=230):
                    st.plotly_chart(estatisticas_gerais_pt_fig_1, use_container_width=True,key="estatisticas_gerais_pt_fig_1",config={'displayModeBar': False})
        
        with col4:
            with st.container(border=True,height=500):
                st.plotly_chart(grafico_barras_pt_fig, use_container_width=True, key="grafico_barras_pt",config={'displayModeBar': False})
        
        # with st.container(border=True,height=500):
            # st.plotly_chart(historico_pt_fig, use_container_width=True, key="grafico_historico_pt")
        
        filtro_jogada_time = st.selectbox(
                    "Selecione o tipo de jogada",
                    options=["Ataque","Defesa"],
                    index=None,
                    key="filtro_jogada_time_tab_pt"
                )       
        
        if filtro_jogada_time:
            with st.container(border=True, height=400):
                
                # fig = create_futsal_subplots(filtro_jogada_time,dados_todos_jogadores_df,"Primeiro Tempo",1,3)
                # st.plotly_chart(fig,key=f"localizazao_time_tab_pt")
                colunas_jogadas_ofensivas = st.columns(3)
                colunas_jogadas_defensivas = st.columns(5)
                colunas= {"Ataque": colunas_jogadas_ofensivas, "Defesa":colunas_jogadas_defensivas}  
                figs= get_plots_plays_localization_partial(filtro_jogada_time,dados_todos_jogadores_df,"Primeiro Tempo")
                
                for i,fig in enumerate(figs):
                    colunas[filtro_jogada_time][i].plotly_chart(fig,key=f"localizazao_{i}_time_tab_pt",config={'displayModeBar': False})

                    
                # localizacao_jogadas = extrair_estatisticas_localizacao(dados_todos_jogadores_df,filtro_jogada_time)
                # fig_localizacao_pt = create_futsal_court(filtro_jogada_time,localizacao_jogadas["Primeiro Tempo"])
                # st.plotly_chart(fig_localizacao_pt,key="localizazao_jogada_time_tab_pt")
                
    with segundo_tempo_tab:
        
        col3, col4 = st.columns([1,1])

        with col3:
            with st.container(border=True,height=500):
                sub_column1,sub_column2 = st.columns([1,1.5])
                with sub_column1:
                    st.image("minas-tenis-clube-logo-png.png",output_format="PNG", width=300)
                with sub_column2:
                    with st.container(border=True, height=220):
                        st.plotly_chart(estatisticas_gerais_st_fig, use_container_width=False, key="estatisticas_gerais_st_fig",config={'displayModeBar': False})
                with st.container(border=True, height=230):
                    st.plotly_chart(estatisticas_gerais_st_fig_1, use_container_width=False,key="estatisticas_gerais_st_fig_1",config={'displayModeBar': False})
        
        with col4:
            with st.container(border=True,height=500):
                st.plotly_chart(grafico_barras_st_fig, use_container_width=True, key="grafico_barras_st",config={'displayModeBar': False})
        
        # with st.container(border=True,height=500):
        #     st.plotly_chart(historico_st_fig, use_container_width=True, key="grafico_historico_st")
        
        filtro_jogada_time = st.selectbox(
                    "Selecione o tipo de jogada",
                    options=["Ataque","Defesa"],
                    index=None,
                    key="filtro_jogada_time_tab_st"
                )        
        
        if filtro_jogada_time:
            with st.container(border=True, height=400):
                colunas_jogadas_ofensivas = st.columns(3)
                colunas_jogadas_defensivas = st.columns(5)
                colunas= {"Ataque": colunas_jogadas_ofensivas, "Defesa":colunas_jogadas_defensivas}  
                figs= get_plots_plays_localization_partial(filtro_jogada_time,dados_todos_jogadores_df,"Segundo Tempo")
                
                for i,fig in enumerate(figs):
                    colunas[filtro_jogada_time][i].plotly_chart(fig,key=f"localizazao_{i}_time_tab_st",config={'displayModeBar': False})
                
                
                # localizacao_jogadas = extrair_estatisticas_localizacao(dados_todos_jogadores_df,filtro_jogada_time)
                # fig_localizacao_st = create_futsal_court(filtro_jogada_time,localizacao_jogadas["Segundo Tempo"])
                # st.plotly_chart(fig_localizacao_st,key="localizazao_jogada_time_tab_st")    
                    
    
    
    with total_tab:
    
        col3, col4 = st.columns([1,1.6])

        with col3:
            with st.container(border=True,height=500):
                sub_column1,sub_column2 = st.columns([1,1.5])
                with sub_column1:
                    st.image("minas-tenis-clube-logo-png.png",output_format="PNG", width=300)
                with sub_column2:
                    with st.container(border=True, height=220):
                        st.plotly_chart(estatisticas_gerais_total_fig, use_container_width=False, key="estatisticas_gerais_total_fig",config={'displayModeBar': False})
                with st.container(border=True, height=230):
                    st.plotly_chart(estatisticas_gerais_total_fig_1, use_container_width=False,key="estatisticas_gerais_total_fig_1",config={'displayModeBar': False})
        
        with col4:
            with st.container(border=True,height=500):
                st.plotly_chart(grafico_barras_total_fig, use_container_width=True, key="grafico_barras_total_fig",config={'displayModeBar': False})
        
        with st.container(border=True,height=500):
            st.plotly_chart(historico_total_fig, use_container_width=True, key="historico_total_fig")
        
        filtro_jogada_time = st.selectbox(
                    "Selecione uma jogada",
                    options=['FIN.C', 'FIN.E', 'FIN.T', 'ASSIST.', 'GOL','DES.C/P.','C.A.-Pró', 'DES.S/P.', 'PER.P.', 'C.A.-Contra'],
                    index=None,
                    key="filtro_jogada_time_tab_total"
                )       
        
        if filtro_jogada_time:
            with st.container(border=True, height=400):
                colunas = st.columns(3) 
                localizacao_jogadas = extrair_estatisticas_localizacao(dados_todos_jogadores_df,filtro_jogada_time)
                
                for i, (chave, valor) in enumerate(localizacao_jogadas.items()):
                    titulo = f"{filtro_jogada_time} - {chave}"
                    fig_localizacao_total = create_futsal_court(titulo,valor)
                    colunas[i].plotly_chart(fig_localizacao_total,config={'displayModeBar': False})









if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)
