import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import atexit

# Importações de módulos locais
from db_manager import DBManager, get_db_manager
from utils import (
    extrair_dataframe_jogador, pegar_figuras_e_estatisticas, exibir_conteudo_tab,pegar_imagem_jogador
)

# --- Configuração da Página e Inicialização ---

# Inicialização do gerenciador de banco de dados
db_manager = get_db_manager()

# Inicializar session_state para os filtros, se ainda não existirem
# Definimos None como valor inicial para indicar que nada foi selecionado
if "filtro_equipes" not in st.session_state:
    st.session_state.filtro_equipes = None
if "filtro_competicao_time" not in st.session_state:
    st.session_state.filtro_competicao_time = None
if "filtro_partida_time" not in st.session_state:
    st.session_state.filtro_partida_time = None

# Botão de refresh
if st.button("Atualizar Dados"):
    # Esta flag pode ser usada para forçar um recarregamento de dados, se necessário
    # No entanto, o Streamlit já recarrega o script em cada interação,
    # então pode não ser estritamente necessário dependendo da sua lógica de cache.
    st.session_state.dados_atualizados = True
  
# Extrai o DataFrame inicial com todos os dados
dados_time_df = extrair_dataframe_jogador(db_manager)
dados_time_total_df = dados_time_df.copy() # Mantém uma cópia do DataFrame original para cálculos de média


if dados_time_df.empty:
    st.warning("Sem jogos analisados!")
else:
    with st.container():
        # 1. Filtro por Equipe
        # Adiciona uma opção de placeholder no início da lista
        options_equipes = ["Selecione uma equipe"] + dados_time_df["equipe_jogada"].unique().tolist()

        # Define o índice inicial para o selectbox como 0 (o placeholder)
        # Se um filtro já foi selecionado e é válido, usa seu índice
        equipe_index = 0
        if st.session_state.filtro_equipes and st.session_state.filtro_equipes in options_equipes:
            equipe_index = options_equipes.index(st.session_state.filtro_equipes)

        filtro_equipes_selecionado = st.selectbox(
            "Selecione uma equipe para analisar",
            options=options_equipes,
            index=equipe_index,
            key="equipe_select"
        )

        # Lógica para atualizar o session_state e forçar rerun
        # Só atualiza se a seleção não for o placeholder e for diferente do estado atual
        if filtro_equipes_selecionado != "Selecione uma equipe" and filtro_equipes_selecionado != st.session_state.filtro_equipes:
            st.session_state.filtro_equipes = filtro_equipes_selecionado
            st.session_state.filtro_competicao_time = None # Reseta filtros dependentes
            st.session_state.filtro_partida_time = None
            st.rerun() # Força o recarregamento para aplicar os resets

        # Se o usuário selecionou o placeholder, ou se ainda não selecionou nenhuma equipe válida
        if filtro_equipes_selecionado == "Selecione uma equipe":
            st.session_state.filtro_equipes = None # Garante que o estado seja None
            st.info("Por favor, selecione uma equipe para visualizar os dados.")
            # Sai da execução para não mostrar dados antes da seleção da equipe
            st.stop()

    # A partir daqui, sabemos que uma equipe válida foi selecionada (st.session_state.filtro_equipes não é None)

    # Filtra os dados pela equipe selecionada
    dados_filtrados_por_equipe = dados_time_df[dados_time_df['equipe_jogada'] == st.session_state.filtro_equipes]
    
    id_equipe_selecionada =  int(dados_filtrados_por_equipe.iloc[0]["equipe_jogada_id"])
    dados_equipe = db_manager.listar_dados_equipe(id_equipe_selecionada)
    
    if dados_equipe:
        nome_equipe, categoria_equipe,logo_id = dados_equipe
    col1, col2 = st.columns([1, 1])

    # 2. Filtro por Competição
    with col1:
        # Adiciona placeholder para competição
        options_competicao = ["Selecione uma competição"] + dados_filtrados_por_equipe["competicao"].unique().tolist()
        competicao_index = 0
        if st.session_state.filtro_competicao_time and st.session_state.filtro_competicao_time in options_competicao:
            competicao_index = options_competicao.index(st.session_state.filtro_competicao_time)

        filtro_competicao_selecionado = st.selectbox(
            "Selecione uma competição",
            options=options_competicao,
            index=competicao_index,
            key="competicao_select"
        )

        if filtro_competicao_selecionado != "Selecione uma competição" and filtro_competicao_selecionado != st.session_state.filtro_competicao_time:
            st.session_state.filtro_competicao_time = filtro_competicao_selecionado
            st.session_state.filtro_partida_time = None # Reseta filtro dependente
            st.rerun()

        # Se o usuário selecionou o placeholder para competição, ou se ainda não selecionou nenhuma competição válida
        if filtro_competicao_selecionado == "Selecione uma competição":
            st.session_state.filtro_competicao_time = None
            dados_filtrados_por_competicao = dados_filtrados_por_equipe.copy() # Continua com a filtragem apenas por equipe
        else:
            dados_filtrados_por_competicao = dados_filtrados_por_equipe[dados_filtrados_por_equipe['competicao'] == st.session_state.filtro_competicao_time]


    # 3. Filtro por Partida
    with col2:
        # Adiciona placeholder para partida
        options_partidas = ["Selecione uma partida"] + dados_filtrados_por_competicao["partida"].unique().tolist()
        options_partidas[1:].reverse() # Inverte apenas as opções de partida, mantendo o placeholder no início
        
        partida_index = 0
        if st.session_state.filtro_partida_time and st.session_state.filtro_partida_time in options_partidas:
            partida_index = options_partidas.index(st.session_state.filtro_partida_time)

        filtro_partida_selecionado = st.selectbox(
            "Selecione uma partida",
            options=options_partidas,
            index=partida_index,
            key="partida_select"
        )

        if filtro_partida_selecionado != "Selecione uma partida" and filtro_partida_selecionado != st.session_state.filtro_partida_time:
            st.session_state.filtro_partida_time = filtro_partida_selecionado
            st.rerun() # Força o recarregamento

        # Se o usuário selecionou o placeholder para partida, ou se ainda não selecionou nenhuma partida válida
        if filtro_partida_selecionado == "Selecione uma partida":
            st.session_state.filtro_partida_time = None
            df_para_analisar = dados_filtrados_por_competicao.copy()
            df_para_media = dados_filtrados_por_competicao.copy()
        else:
            # Se uma partida específica foi selecionada, analise apenas essa partida
            df_para_analisar = dados_filtrados_por_competicao[
                dados_filtrados_por_competicao['partida'] == st.session_state.filtro_partida_time
            ]
            # A média deve ser calculada a partir de todas as outras partidas (excluindo a atual)
            df_para_media = dados_filtrados_por_competicao[
                dados_filtrados_por_competicao['partida'] != st.session_state.filtro_partida_time
            ]
            # Se não houver outras partidas para a média, use a própria partida para evitar erros
            if df_para_media.empty:
                df_para_media = df_para_analisar.copy()


    # --- Geração dos Gráficos e Exibição das Abas ---
    # Apenas exibe os gráficos se houver dados para analisar após todos os filtros
    if not df_para_analisar.empty:
        figures_dict = pegar_figuras_e_estatisticas(df_para_analisar, df_para_media)

        tab_names = ["Primeiro Tempo", "Segundo Tempo", "Total"]
        tabs = st.tabs(tab_names)

        for i, tab in enumerate(tabs):
            with tab:
                tab_name = tab_names[i]
                # Verifica se há dados para exibir na aba antes de chamar a função
                if tab_name == "Total" or (figures_dict[tab_name][0] and figures_dict[tab_name][0].data):
                    exibir_conteudo_tab(tab_name, figures_dict[tab_name], df_para_analisar,logo_id)
                else:
                    st.info(f"Não há dados para exibir em '{tab_name}' para a seleção atual.")
    else:
        st.info("Não há dados para a seleção atual. Por favor, ajuste os filtros.")


# --- Fechamento da Conexão com o Banco de Dados ---
# Garante que a conexão com o banco de dados seja fechada ao desligar o aplicativo
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)
