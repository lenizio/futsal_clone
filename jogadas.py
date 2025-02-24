import streamlit as st
import os
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_gsheets import GSheetsConnection
from db_manager import DBManager,get_db_manager
import atexit

from utils import listar_opces_jogadores
db_manager = get_db_manager()

# Lista de jogos
lista_jogos = db_manager.listar_jogos()

# Inicializar o valor padrão para o tempo no estado, se ainda não existir
if "selected_tempo" not in st.session_state:
    st.session_state["selected_tempo"] = "1ºT"

# Exibir aviso se não houver jogos
if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    # Criar as opções de jogos
    opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
    jogo_selecionado = st.selectbox("Selecinoe um jogo para adicionar jogadas", options=opcoes_jogos.keys(), index=None)
    
    if jogo_selecionado:
        jogo_id = opcoes_jogos[jogo_selecionado]
        equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, _, _, _, _ = db_manager.listar_detalhes_jogo(jogo_id)
        opcoes_equipes = {equipe_mandante_nome: equipe_mandante_id, equipe_visitante_nome: equipe_visitante_id}
        equipe_selecionada = st.selectbox("Selecione uma equipe para analisar", options=opcoes_equipes.keys(), index=None)
        
        if equipe_selecionada:
            equipe_id = opcoes_equipes[equipe_selecionada] 
            lista_jogadores = db_manager.listar_jogadores_por_equipe(equipe_id)
            if not lista_jogadores:
                st.warning("Equipe sem jogadores cadastrados. Cadastre para poder analisar")
            else:
                
                letf_div, central_div, right_div = st.columns([1,3,1])
                
                with central_div:        
                # Seleção do tempo
                    tempo = st.pills(
                        "Tempo", 
                        ['1ºT', '2ºT', '1ºP', '2ºP'], 
                        key="selected_tempo",
                        default=st.session_state["selected_tempo"]  # Usar o valor atual do session_state como default
                    )
                    
                    # Condição para verificar a mudança de tempo e manter o último valor selecionado
                    if tempo != st.session_state["selected_tempo"]:
                        st.session_state["selected_tempo"] = tempo  # Atualiza o valor no session_state

                    # Container para os elementos abaixo do botão de tempo
                    with st.container():
                        opcoes_jogadores_dict, opcoes_jogadores_list = listar_opces_jogadores(lista_jogadores)
                        col2, col1 = st.columns(2)

                        # Coluna 1: Exibir a imagem e capturar as coordenadas
                        with col1:
                            coordinates = streamlit_image_coordinates("futasl_court.jpg", key="local", 
                                                                    width=280,height=470
                                                                    )

                        # Coluna 2: Formulário
                        with col2:
                            with st.form("my_form", clear_on_submit=True):  # Limpar formulário ao submeter
                                st.write("Adicionar evento")

                                # Campos do formulário com valor padrão vazio
                                jogadas = st.pills(
                                    "Jogada", 
                                    ['FIN.C', 'FIN.E', 'FIN.T', 'GOL', 'ASSIST.', 'DES.C/P.','C.A.P.', 'DES.S/P.', 'PER.P.', 'C.A.C.'],
                                    selection_mode="multi"
                                )
                                jogador = st.pills("Selecione o jogador", options=opcoes_jogadores_list)
                                
                                coord_text = st.text_input(
                                    "Coordenadas selecionadas (x, y):",
                                    value=f"{coordinates['x']}, {coordinates['y']}" if coordinates else "",
                                )

                                # Botão de envio
                                submitted = st.form_submit_button("Enviar")

                                if submitted:
                                    if not jogadas or not jogador or not coord_text or not tempo:  # Verifica se os campos obrigatórios estão preenchidos
                                        st.error("Por favor, preencha todos os campos.")
                                    else:
                                        try:
                                            x = float(coordinates["x"])
                                            y = float(coordinates["y"])
                                            # Recupera os detalhes do jogador
                                            jogador_id, jogador_nome = opcoes_jogadores_dict[jogador]

                                            # Se 'GOL' estiver nas jogadas, garantir que 'FIN.C' também seja adicionado
                                            jogadas_modificadas = jogadas.copy()

                                            # Adicionar 'FIN.C' apenas se 'GOL' estiver presente e 'FIN.C' não estiver
                                            if 'GOL' in jogadas_modificadas and 'FIN.C' not in jogadas_modificadas:
                                                jogadas_modificadas.append('FIN.C')
                                            
                                            for jogada in jogadas_modificadas:
                                            
                                                # Insere cada jogada no banco de dados
                                                db_manager.adicionar_jogada(
                                                    jogador_id=jogador_id,
                                                    jogador_nome=jogador_nome,
                                                    jogo_id=jogo_id,
                                                    jogada=jogada,
                                                    tempo=tempo,
                                                    x_loc=x,
                                                    y_loc=y
                                                )
                                            st.success(f"Jogada adicionada com sucesso!")    
                                        except Exception as e:
                                            st.error(f"Erro ao adicionar jogadas: {e}")

if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao) 