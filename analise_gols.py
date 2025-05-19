import streamlit as st
import os
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
from db_manager import DBManager,get_db_manager
import atexit
from utils import exibir_seta,extrair_dataframe_analise_gols
from utils import listar_opces_jogadores

# @st.dialog("Deletar",width='large')
# def deletar():
#     df_gols = extraisr_dataframe_analise_gols(db_manager)
#     df_gols = df_gols.iloc[:,:-3]
    
#     event = st.dataframe(
#             df_gols,
#             use_container_width=True,
#             hide_index=True,
#             on_select="rerun",
#             selection_mode="single-row",
# )   
    
#     selected_rows = event.selection.rows
#     if selected_rows:
#         filtered_df = df_gols.iloc[selected_rows]
#         st.dataframe(filtered_df,key='dialogdataframe')
    


db_manager = get_db_manager()

# Lista de jogos
lista_jogos = db_manager.listar_jogos()
tipo_gol = ["Marcado", "Sofrido"]
# Inicializar o valor padrão para o tempo no estado, se ainda não existir
if "selected_tempo" not in st.session_state:
    st.session_state["selected_tempo"] = "1ºQ"

# Exibir aviso se não houver jogos
if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    # Criar as opções de jogos
    opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
    jogo_selecionado = st.selectbox("Selecinoe um jogo para adicionar gols", options=opcoes_jogos.keys(), index=None)
    
    if jogo_selecionado:
        jogo_id = opcoes_jogos[jogo_selecionado]
        equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, _, _, _, _ = db_manager.listar_detalhes_jogo(jogo_id)
        opcoes_equipes = {equipe_mandante_nome: equipe_mandante_id, equipe_visitante_nome: equipe_visitante_id}
        equipe_selecionada = st.selectbox("Selecione uma equipe para analisar", options=opcoes_equipes.keys(), index=None)
        
        if equipe_selecionada:
            equipe_analisada_id = opcoes_equipes[equipe_selecionada] 
            lista_jogadores = db_manager.listar_jogadores_por_equipe(equipe_analisada_id)
            letf_div, central_div, right_div = st.columns([1,3,1])
            
            with central_div:        
            # Seleção do tempo
                tempo = st.pills(
                    "Tempo", 
                    ['1ºQ','2ºQ','3ºQ','4ºQ', '1ºP', '2ºP'], 
                    key="selected_tempo",
                    default=st.session_state["selected_tempo"]  # Usar o valor atual do session_state como default
                )
                
                # Condição para verificar a mudança de tempo e manter o último valor selecionado
                if tempo != st.session_state["selected_tempo"]:
                    st.session_state["selected_tempo"] = tempo  # Atualiza o valor no session_state

                # Container para os elementos abaixo do botão de tempo
                with st.container():
                    opcoes_jogadores_dict, opcoes_jogadores_list = listar_opces_jogadores(lista_jogadores)
                    col1, col2 = st.columns(2)

                    # Coluna 1: Exibir a imagem e capturar as coordenadas
                    with col2:
                        coordinates = streamlit_image_coordinates("futsal_court_dotted.png", key="local", 
                                                                width=280,height=470
                                                                )

                    # Coluna 2: Formulário
                    with col1:
                        with st.form("forms_analise_gols", clear_on_submit=True,):  # Limpar formulário ao submeter
                            st.write("Adicionar gol")

                            # Campos do formulário com valor padrão vazio
                            tipo = st.pills(
                                "Tipo", 
                                options=tipo_gol,
                                
                            )
                            caracteristica_gol = st.pills(
                                "Característica", 
                                ["4x3",'3x4', "Ataque Posicional PA", "Ataque Posicional PB","Goleiro Linha","Defesa Goleiro Linha","Goleiro no Jogo", "Escanteio", "Falta","Lateral","Pênalti","Tiro de 10", "Gol Contra","Transição Alta","Transição Baixa"],
                               
                            )
                            if len(opcoes_jogadores_list) == 0:
                                st.warning("Sem jogadores cadastrados")
                                
                            
                            jogador_gol = st.selectbox("Selecione o autor do gol", options=opcoes_jogadores_list, index=None)
                            
                            jogador_assistencia = st.selectbox("Selecione o autor da assistentência", options=opcoes_jogadores_list, index=None)
                            
                            jogadores_em_quadra = st.pills("Selecione os jogadores em quadra", options=opcoes_jogadores_list, selection_mode="multi")
                            
                    
                            
                            coord_text_analise_gols = st.text_input(
                                "Coordenadas selecionadas (x, y):",
                                value=f"{coordinates['x']}, {coordinates['y']}" if coordinates else "",key="coord_analise_gols"
                            )

                            # Botão de envio
                            enviar_form = st.form_submit_button("Enviar")

                            if enviar_form:
                                if not tipo or not caracteristica_gol or not coord_text_analise_gols or not tempo:  # Verifica se os campos obrigatórios estão preenchidos
                                    st.error("Por favor, preencha os campos obrigatórios.")
                                
                                else:
                                    try:
                                        # Obter coordenadas
                                        x = coordinates['x']
                                        y = coordinates['y']

                                        # Converter nomes para IDs
                                        autor_gol_id = opcoes_jogadores_dict.get(jogador_gol)[0] if jogador_gol else None
                                        assistente_id = opcoes_jogadores_dict.get(jogador_assistencia)[0] if jogador_assistencia else None
                                        jogadores_em_quadra_ids = [opcoes_jogadores_dict[j][0] for j in jogadores_em_quadra if j in opcoes_jogadores_dict]

                                        # Adicionar gol principal
                                        db_manager.adicionar_gol(
                                            jogo_id=jogo_id,
                                            equipe_analisada_id=equipe_analisada_id,
                                            tipo_gol=tipo,
                                            tempo=tempo,
                                            caracteristica=caracteristica_gol,
                                            x_loc=x,
                                            y_loc=y,
                                            jogadores_em_quadra=jogadores_em_quadra_ids,
                                            autor_gol_id=autor_gol_id,
                                            assistente_id=assistente_id
                                        )

                                        # Determinar equipe adversária
                                        if equipe_analisada_id == equipe_mandante_id:
                                            equipe_oponente_id = equipe_visitante_id
                                        else:
                                            equipe_oponente_id = equipe_mandante_id

                                        # Inverter tipo de gol
                                        tipo_oposto = "Sofrido" if tipo == "Marcado" else "Marcado"

                                        # Adicionar registro oposto
                                        db_manager.adicionar_gol(
                                            jogo_id=jogo_id,
                                            equipe_analisada_id=equipe_oponente_id,
                                            tipo_gol=tipo_oposto,
                                            tempo=tempo,
                                            caracteristica=caracteristica_gol,
                                            x_loc=x,
                                            y_loc=y,
                                            jogadores_em_quadra=None,
                                            autor_gol_id=None,
                                            assistente_id=None
                                        )

                                        st.success("Gol adicionado com sucesso!")
                                        
                                    except Exception as e:
                                        st.error(f"Erro ao salvar dados: {str(e)}")
                                        db_manager.rollback()
                                                        
                                        
                with right_div:
                    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
                    exibir_seta("↑")
                    
    
    
    # if st.button("A"):
    #     deletar()
    
#     df_gols = extraisr_dataframe_analise_gols(db_manager)
#     df_gols = df_gols.iloc[:,:-3]
    
#     event = st.dataframe(
#             df_gols,
#             use_container_width=True,
#             hide_index=True,
#             on_select="rerun",
#             selection_mode="multi-row",
# )   
    
#     selected_rows = event.selection.rows
#     filtered_df = df_gols.iloc[selected_rows]
    
#     for rows in selected_rows:
#         st.write(rows)
    
#     st.dataframe(filtered_df)
    # event=st.data_editor(df_gols, 
    #              column_config={
    #                     "editar": st.column_config.CheckboxColumn(
    #                         "Editar",
    #                         help="Selecione quais gols editar",
    #                         default=False)
    #              },
    #              hide_index=True)
    
    # selected_rows = event.selection.rows
    # filtered_df = df_gols.iloc[selected_rows]
    # st.data_editor(filtered_df, 
    #              column_config={
    #                     "editar": st.column_config.CheckboxColumn(
    #                         "Editar",
    #                         help="Selecione quais gols editar",
    #                         default=False)
    #              },
    #              hide_index=True)           
                
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao) 
