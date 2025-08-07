import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import atexit

# Importações de módulos locais
from db_manager import DBManager, get_db_manager
from utils import (
    extrair_dataframe_jogador, pegar_figuras_e_estatisticas, exibir_conteudo_tab,
    pegar_figuras_e_estatisticas_jogadores, exibir_conteudo_tabs_jogadores,
    pegar_imagem_jogador,extrair_estatisticas_gerais # Adicionado para a lógica do jogador
)


# Inicialização do gerenciador de banco de dados
db_manager = get_db_manager()

# Inicializar session_state para os filtros
# Definimos None como valor inicial para indicar que nada foi selecionado
if "filtro_equipes" not in st.session_state:
    st.session_state.filtro_equipes = None
if "filtro_competicao_time" not in st.session_state:
    st.session_state.filtro_competicao_time = None
if "filtro_partida_time" not in st.session_state:
    st.session_state.filtro_partida_time = None

# Novos estados para a página de atleta
if "filtro_equipe_analise" not in st.session_state:
    st.session_state.filtro_equipe_analise = None
if "filtro_jogador" not in st.session_state:
    st.session_state.filtro_jogador = None
if "filtro_competicao_jogador" not in st.session_state:
    st.session_state.filtro_competicao_jogador = None
if "filtro_partida_jogador" not in st.session_state:
    st.session_state.filtro_partida_jogador = None


# Botão de refresh
if st.button("Atualizar Dados"):
    st.session_state.dados_atualizados = True
    # Opcional: resetar todos os filtros ao atualizar dados
    st.session_state.filtro_equipes = None
    st.session_state.filtro_competicao_time = None
    st.session_state.filtro_partida_time = None
    st.session_state.filtro_equipe_analise = None
    st.session_state.filtro_jogador = None
    st.session_state.filtro_competicao_jogador = None
    st.session_state.filtro_partida_jogador = None
    st.rerun() # Força o recarregamento para aplicar o reset

# Extrai o DataFrame inicial com todos os dados
df_dados_completos = extrair_dataframe_jogador(db_manager)
df_time_total = df_dados_completos.copy() # Mantém uma cópia do DataFrame original para cálculos de média

# st.dataframe(df_dados_completos) # Removido para não poluir a UI

if df_dados_completos.empty:
    st.warning("Sem jogos analisados!")
else:
    

   
    st.subheader("Análise de Desempenho do Atleta")
    with st.container():
        # 1. Filtro de Seleção de Equipe (para Análise de Atleta)
        opcoes_equipes_analise_atleta = ["Selecione uma equipe"] + df_dados_completos["equipe_jogada"].unique().tolist()
        indice_equipe_analise_atleta = 0
        if st.session_state.filtro_equipe_analise and st.session_state.filtro_equipe_analise in opcoes_equipes_analise_atleta:
            indice_equipe_analise_atleta = opcoes_equipes_analise_atleta.index(st.session_state.filtro_equipe_analise)

        equipe_analise_selecionada = st.selectbox(
            "Selecione uma equipe para analisar",
            options=opcoes_equipes_analise_atleta,
            index=indice_equipe_analise_atleta,
            key="equipe_analise_select_atleta" # Chave única para esta aba
        )

        # Lógica para atualizar o session_state e forçar rerun
        if equipe_analise_selecionada != "Selecione uma equipe" and equipe_analise_selecionada != st.session_state.filtro_equipe_analise:
            st.session_state.filtro_equipe_analise = equipe_analise_selecionada
            st.session_state.filtro_jogador = None
            st.session_state.filtro_competicao_jogador = None
            st.session_state.filtro_partida_jogador = None
            st.rerun()

        if equipe_analise_selecionada == "Selecione uma equipe":
            st.session_state.filtro_equipe_analise = None
            st.info("Por favor, selecione uma equipe para visualizar os dados do atleta.")
            st.stop() # Interrompe a execução para a aba de atleta

    # A partir daqui, sabemos que uma equipe válida foi selecionada para a aba de atleta
    df_equipe_selecionada = df_dados_completos[df_dados_completos['equipe_jogada'] == st.session_state.filtro_equipe_analise]

    if df_equipe_selecionada.empty:
        st.warning(f"Não há dados para a equipe '{st.session_state.filtro_equipe_analise}'.")
        st.stop() # Interrompe se a equipe selecionada não tiver dados

    # Extrai estatísticas gerais da equipe selecionada (para comparação no radar do jogador)
    estatisticas_gerais_pt, estatisticas_gerais_st, estatisticas_gerais_total, estatisticas_gerais_ptp, estatisticas_gerais_stp = \
        extrair_estatisticas_gerais(df_equipe_selecionada)
    estatisticas_gerais_para_radar = {
        "Primeiro Tempo": estatisticas_gerais_pt,
        "Segundo Tempo": estatisticas_gerais_st,
        "Total": estatisticas_gerais_total,
        "Primeiro Tempo Prorrogação": estatisticas_gerais_ptp,
        "Segundo Tempo Prorrogação": estatisticas_gerais_stp
    }

    
    
    id_equipe_selecionada =  int(df_equipe_selecionada.iloc[0]["equipe_jogada_id"])
    lista_todos_atletas_do_db = db_manager.listar_jogadores_por_equipe(id_equipe_selecionada) 

    
    jogadores_com_dados_na_equipe = [
        j for j in lista_todos_atletas_do_db
        if j[1] in df_equipe_selecionada['jogador_nome'].unique().tolist()
    ]
    
    dicionario_jogadores = {jogador[1]: [jogador[0], jogador[4],jogador[2]] for jogador in jogadores_com_dados_na_equipe}
    lista_nomes_jogadores = list(dicionario_jogadores.keys())

    if not lista_nomes_jogadores:
        st.info(f"Não há jogadores com dados para a equipe '{st.session_state.filtro_equipe_analise}'.")
        st.stop() # Interrompe se não houver jogadores com dados

    with st.container():
        coluna1_atleta, coluna2_atleta, coluna3_atleta = st.columns([1, 1, 2])
        # 2. Filtro por Jogador
        with coluna1_atleta:
            opcoes_jogadores_atleta = ["Selecione um jogador"] + lista_nomes_jogadores
            indice_jogador_atleta = 0
            if st.session_state.filtro_jogador and st.session_state.filtro_jogador in opcoes_jogadores_atleta:
                indice_jogador_atleta = opcoes_jogadores_atleta.index(st.session_state.filtro_jogador)

            jogador_selecionado = st.selectbox(
                "Selecione um jogador",
                options=opcoes_jogadores_atleta,
                index=indice_jogador_atleta,
                key="jogador_select_atleta"
            )

            if jogador_selecionado != "Selecione um jogador" and jogador_selecionado != st.session_state.filtro_jogador:
                st.session_state.filtro_jogador = jogador_selecionado
                st.session_state.filtro_competicao_jogador = None
                st.session_state.filtro_partida_jogador = None
                st.rerun()

            if jogador_selecionado == "Selecione um jogador":
                st.session_state.filtro_jogador = None
                st.info("Por favor, selecione um jogador para visualizar os dados.")
                st.stop() # Interrompe a execução para o jogador

            # Obtém a id da imagem do jogador
            id_imagem = dicionario_jogadores.get(st.session_state.filtro_jogador, [None, None])[1]
            posicao = dicionario_jogadores.get(st.session_state.filtro_jogador, [None, None])[2]
            # Filtra os dados para o jogador selecionado
            df_filtrado_jogador = df_equipe_selecionada[df_equipe_selecionada['jogador_nome'] == st.session_state.filtro_jogador]

        # 3. Filtro por Competição (para o jogador)
        with coluna2_atleta:
            opcoes_competicao_jogador = ["Selecione uma competição"] + df_filtrado_jogador["competicao"].unique().tolist()
            indice_competicao_jogador = 0
            if st.session_state.filtro_competicao_jogador and st.session_state.filtro_competicao_jogador in opcoes_competicao_jogador:
                indice_competicao_jogador = opcoes_competicao_jogador.index(st.session_state.filtro_competicao_jogador)

            competicao_jogador_selecionada = st.selectbox(
                "Selecione uma competição",
                options=opcoes_competicao_jogador,
                index=indice_competicao_jogador,
                key="competicao_jogador_select_atleta"
            )

            if competicao_jogador_selecionada != "Selecione uma competição" and competicao_jogador_selecionada != st.session_state.filtro_competicao_jogador:
                st.session_state.filtro_competicao_jogador = competicao_jogador_selecionada
                st.session_state.filtro_partida_jogador = None
                st.rerun()

            if competicao_jogador_selecionada == "Selecione uma competição":
                st.session_state.filtro_competicao_jogador = None
                df_filtrado_jogador_competicao = df_filtrado_jogador.copy()
            else:
                df_filtrado_jogador_competicao = df_filtrado_jogador[df_filtrado_jogador['competicao'] == st.session_state.filtro_competicao_jogador]

        # 4. Filtro por Partida (para o jogador)
        with coluna3_atleta:
            opcoes_partidas_jogador = ["Selecione uma partida"] + df_filtrado_jogador_competicao["partida"].unique().tolist()
            opcoes_partidas_jogador[1:].reverse() # Inverte a ordem das opções de partida, mantendo o placeholder no início
            
            indice_partida_jogador = 0
            if st.session_state.filtro_partida_jogador and st.session_state.filtro_partida_jogador in opcoes_partidas_jogador:
                indice_partida_jogador = opcoes_partidas_jogador.index(st.session_state.filtro_partida_jogador)

            partida_jogador_selecionada = st.selectbox(
                "Selecione uma partida",
                options=opcoes_partidas_jogador,
                index=indice_partida_jogador,
                key="partida_jogador_select_atleta"
            )
            if partida_jogador_selecionada != "Selecione uma partida" and partida_jogador_selecionada != st.session_state.filtro_partida_jogador:
                st.session_state.filtro_partida_jogador = partida_jogador_selecionada
                st.rerun()

            if partida_jogador_selecionada == "Selecione uma partida":
                st.session_state.filtro_partida_jogador = None
                df_analise_jogador = df_filtrado_jogador_competicao.copy()
                df_media_jogador = df_filtrado_jogador_competicao.copy()
            else:
                df_analise_jogador = df_filtrado_jogador_competicao[
                    df_filtrado_jogador_competicao['partida'] == st.session_state.filtro_partida_jogador
                ]
                df_media_jogador = df_filtrado_jogador_competicao[
                    df_filtrado_jogador_competicao['partida'] != st.session_state.filtro_partida_jogador
                ]
                if df_media_jogador.empty:
                    df_media_jogador = df_analise_jogador.copy()

        # --- Geração dos Gráficos e Exibição das Abas (para o jogador) ---
        if not df_analise_jogador.empty:
            dict_figuras_jogador = pegar_figuras_e_estatisticas_jogadores(
                df_analise_jogador, df_media_jogador, estatisticas_gerais_para_radar,posicao
            )

            nomes_abas_jogador = ["Primeiro Tempo", "Segundo Tempo", "Total"]
            abas_jogador = st.tabs(nomes_abas_jogador)

            for i, conteudo_aba_jogador in enumerate(abas_jogador):
                with conteudo_aba_jogador:
                    nome_aba_jogador = nomes_abas_jogador[i]
                    if dict_figuras_jogador[nome_aba_jogador][0] and dict_figuras_jogador[nome_aba_jogador][0].data:
                        exibir_conteudo_tabs_jogadores(nome_aba_jogador,
                             dict_figuras_jogador[nome_aba_jogador],
                            df_analise_jogador, id_imagem,posicao
                        )
                    else:
                        st.info(f"Não há dados para exibir em '{nome_aba_jogador}' para a seleção atual.")
        else:
            st.info("Não há dados para a seleção atual do atleta. Por favor, ajuste os filtros.")

# --- Fechamento da Conexão com o Banco de Dados ---
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)
