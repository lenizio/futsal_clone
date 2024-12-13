import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_gsheets import GSheetsConnection
from db_manager import DBManager




# Criar duas colunas
col1, col2 = st.columns(2)

# Coluna 1: Exibir a imagem e capturar as coordenadas
with col1:
    st.write("Clique na imagem para capturar as coordenadas (x, y):")
    coordinates = streamlit_image_coordinates(
        "/home/lenizio/minas_projects/futsal_analysis/images/futasl_court.jpg",
        key="local",
    )

# Coluna 2: Formulário
with col2:
    with st.form("my_form", clear_on_submit=True):  # Limpar formulário ao submeter
        st.write("Adicionar evento")

        # Campos do formulário com valor padrão vazio
        jogada = st.radio(
            "Jogada", 
            ['FIN.C', 'FIN.E', 'FIN.T', 'ASSIST.', 'GOL', 'DES.C/P.', 'DES.S/P.', 'PER.P', 'C.A'], 
            horizontal=True
        )
        jogador = st.radio(
            "Selecione um Jogador", 
            ['1','2','3','4','5','6','7','8','9'],
            horizontal=True
        )

        # Campo para coordenadas
        coord_text = st.text_input(
            "Coordenadas selecionadas (x, y):",
            value=f"{coordinates['x']}, {coordinates['y']}" if coordinates else "",
        )

        # Botão de envio
        submitted = st.form_submit_button("Enviar")

        if submitted:
            if not jogada or not jogador:  # Verifica se os campos obrigatórios estão preenchidos
                st.error("Por favor, preencha todos os campos.")
            else:
                st.success(f"Coordenadas enviadas: {coord_text}")
                st.write(f"Jogada: {jogada}, Jogador: {jogador}")
                
        
