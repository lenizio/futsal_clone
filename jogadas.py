import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_gsheets import GSheetsConnection
from db_manager import DBManager
db_manager = DBManager()

lista_jogos = db_manager.listar_jogos()

if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
    jogo_selecionado = st.selectbox("Selecione um jogo para adicionanar jogadas",options=opcoes_jogos.keys(),index=None)
    
    if jogo_selecionado:
        jogo_id = opcoes_jogos[jogo_selecionado]
        equipe_mandante_id, equipe_mandante_nome,equipe_visitante_id ,equipe_visitante_nome,_,_,_,_  = db_manager.listar_detalhes_jogo(jogo_id)
        opcoes_equipes={equipe_mandante_nome: equipe_mandante_id,equipe_visitante_nome:equipe_visitante_id}
        equipe_selecionada = st.selectbox("Selecione uma equile para analisar",options=opcoes_equipes.keys(),index=None)
        
        if equipe_selecionada:
            
        # Criar duas colunas
            equipe_id = opcoes_equipes[equipe_selecionada] 
            lista_jogadores = db_manager.listar_jogadores_por_equipe(equipe_id)
            if not lista_jogadores:
                    st.warning("Equipe sem jogadores cadastrados. Cadastre para poder analisar")
            else:        
                    # opcoes_jogadores_dict = {}
                    # opcoes_jogadores_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Goleiro"})
                    # opcoes_jogadores_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Fixo"})
                    # opcoes_jogadores_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala D"})
                    # opcoes_jogadores_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala E"})
                    # opcoes_jogadores_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Pivô"})
                    # opcoes_jogadores_list = list(opcoes_jogadores_dict.keys())
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
                    
                    col2, col1 = st.columns(2)

                    # Coluna 1: Exibir a imagem e capturar as coordenadas
                    with col1:
                        coordinates = streamlit_image_coordinates(
                            "futsal_analysis/images/futasl_court.jpg",
                            key="local",
                        )

                    # Coluna 2: Formulário
                    with col2:
                        
                        with st.form("my_form", clear_on_submit=True):  # Limpar formulário ao submeter
                            st.write("Adicionar evento")

                            # Campos do formulário com valor padrão vazio
                            jogadas = st.pills(
                                "Jogada", 
                                ['FIN.C', 'FIN.E', 'FIN.T', 'ASSIST.', 'GOL', 'DES.C/P.', 'DES.S/P.', 'PER.P', 'C.A'],
                                selection_mode="multi"
                                

                            )
                            # Seleção de goleiro
                            jogador = st.pills("Selecio o jogador", options=opcoes_jogadores_list)
                            coord_text = st.text_input(
                                "Coordenadas selecionadas (x, y):",
                                value=f"{coordinates['x']}, {coordinates['y']}" if coordinates else "",
                            )

                            # Botão de envio
                            submitted = st.form_submit_button("Enviar")

                            if submitted:
                                if not jogadas or not jogador or not coord_text:  # Verifica se os campos obrigatórios estão preenchidos
                                    st.error("Por favor, preencha todos os campos.")
                                else:
                                    try:
                                        for jogada in jogadas:
                                            # Extrai as coordenadas (x, y)
                                            x = float(coordinates["x"])
                                            y = float(coordinates["y"]) 
                                            # Recupera os detalhes do jogador
                                            jogador_id, jogador_nome = opcoes_jogadores_dict[jogador]

                                            # Insere cada jogada no banco de dados
                                            db_manager.adicionar_jogada(
                                                jogador_id=jogador_id,
                                                jogador_nome=jogador_nome,
                                                jogo_id=jogo_id,
                                                jogada=jogada,
                                                x_loc=x,
                                                y_loc=y
                                            )
                                        
                                        st.success(f"As seguintes jogadas foram registradas: {', '.join(jogadas)}")
                                    except Exception as e:
                                        st.error(f"Erro ao adicionar jogadas: {e}")
                                
