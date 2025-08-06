import streamlit as st
import pandas as pd
import time
from db_manager import DBManager,get_db_manager
import atexit
from psycopg2.errors import UniqueViolation

db_manager = get_db_manager()
db_manager.rollback()


@st.dialog("Adicionar Jogador")
def adicionar_jogador_dialog(equipe_id, equipe_nome):
    nome = st.text_input("Nome") 
    posicao = st.selectbox("Selecione a posição", ('Goleiro', "Ala D","Ala E", "Fixo", 'Pivô'),index = None)
    numero_camisa = st.number_input("Número da camisa", value=None, min_value=0,format="%d")
    image_id= st.text_input("Adicione o id da foto do jogador", value=None)
    
    # Validação e submissão do formulário
    if st.button("Cadastrar", key=f"adicionar_jogador_dialog"):  # Adicionando um key único
        if not nome or not posicao or not numero_camisa:
            st.error("Por favor, preencha todos os campos.")
        else:
            
            try:
                resultado = db_manager.adicionar_jogador(nome, equipe_id, equipe_nome, posicao, numero_camisa,image_id)
                st.success(f"Jogador cadastrado com sucesso!")
                time.sleep(1)  
                st.rerun()                
            
            except Exception as e:
                st.error(f"Aconteceu o segunite erro ao cadastrar o jogador: {e}")
                db_manager.rollback()
                
@st.dialog("Editar Jogador")
def editar_jogador_dialog(equipe_id):
    lista_jogadores = db_manager.listar_jogadores_por_equipe(equipe_id)
    dict_jogadores = {jogador[1]:[jogador[0],jogador[2],jogador[3],jogador[4]]for jogador in lista_jogadores}
    jogador = st.selectbox('Selecione o jogador', options=dict_jogadores.keys(), index=None)
    
    if jogador:
        jogador_id = dict_jogadores[jogador][0]
        nome = st.text_input("Nome",value=jogador) 
        posicoes_list = ['Goleiro', "Ala D","Ala E", "Fixo", 'Pivô']
        posicao = st.selectbox("Selecione a posição", options=posicoes_list,index = posicoes_list.index(dict_jogadores[jogador][1]))
        numero_camisa = st.number_input("Número da camisa", value=dict_jogadores[jogador][2])
        image_id= st.text_input("Adicione o id da foto do jogador",value=dict_jogadores[jogador][3])
        
        if st.button("Editar", key=f"editar_jogador_dialog"):  # Adicionando um key único
            if not nome or not posicao or not numero_camisa:
                st.error("Por favor, preencha todos os campos.")
            else:
                resultado = db_manager.editar_jogador(equipe_id,jogador_id,nome,numero_camisa,posicao,image_id)   
                if isinstance(resultado, str):  # Se for uma string, é uma mensagem de erro
                    st.error(resultado)
                    db_manager.rollback()# Exibe a mensagem de erro no Streamlit
                else:
                    st.success(f"Jogador editado com sucesso!")
                    time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                    st.rerun()

    
   
    
    
    
                

@st.dialog("Excluir Jogador")
def excluir_jogador_dialog(equipe_id):
    
    lista_jogadores = db_manager.listar_jogadores_por_equipe(equipe_id)
    dict_jogadores = {jogador[1]:jogador[0] for jogador in lista_jogadores}
    jogador = st.selectbox('Selecione o jogador', options=dict_jogadores.keys(), index=None)
    if jogador:
        jogador_id =dict_jogadores[jogador]
        st.warning("Isso excluirá permanentemente todos os dados associados a ese jogador. Você tem certeza?", icon="⚠️")
        if st.button("Excluir", key=f"excluir_jogador_dialog"):
        
            if db_manager.deletar_jogador(jogador_id):
                st.success(f"Jogador deletado com sucesso!")
                time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                st.rerun()    
            else:
                st.error('Erro na hora de excluir jogador. Tente novamente')
                db_manager.rollback()         
                time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                st.rerun()     




# Obter a lista de clubes
clubes = db_manager.listar_equipes()  # Função para listar clubes únicos

if not clubes:
    st.warning("Sem equipes registradas.")
else:
    # Criar uma lista de nomes de clubes
    for clube in clubes:
        with st.expander(f"{clube[1]} {clube[2]}"):  # Exibe o nome e a categoria do clube
            # Listar jogadores por equipe
            jogadores = db_manager.listar_jogadores_por_equipe(clube[0])
            
            if not jogadores:  # Se não houver jogadores, exibe uma mensagem
                st.write("Nenhum jogador cadastrado")
            else:
                df = pd.DataFrame(jogadores, columns=["id", "Nome", "Posição",'Número',"image_id"])
                df = df.drop(columns=["id","image_id"])
                st.dataframe(df, hide_index=True)

            botao_adicionar_jogador, botao_excluir_jogador, botao_editar_jogador = st.columns([1,1,3])

            with botao_adicionar_jogador:
                if st.button("Adicionar Jogador", key=f"adicionar_jogador_{clube[0]}"):
                    adicionar_jogador_dialog(clube[0], clube[1])
        
            with botao_excluir_jogador:
                if st.button("Excluir Jogador", key=f"excluir_jogador_{clube[0]}"):
                    excluir_jogador_dialog(clube[0])
            with botao_editar_jogador:
                if st.button("Editar Jogador", key=f"editar_jogador_{clube[0]}"):
                    editar_jogador_dialog(clube[0])

# Adicionar equipe
@st.dialog("Adicionar equipe")
def adicionar_equipe_dialog():
    equipe = st.text_input("Nome da Equipe") 
    categoria = st.selectbox("Selecione a categoria", ('Principal', 'Sub-20'))
    logo_id= st.text_input("Adicione o id da equipe", value=None)
    
    # Validação e submissão do formulário
    if st.button("Cadastrar", key="adicionar_equipe_dialog"):  # Adicionando uma chave única para o botão de cadastrar equipe
        if not equipe or not categoria:  # Verifica se os campos obrigatórios estão preenchidos
            st.error("Por favor, preencha todos os campos.")
        else:
            id = db_manager.adicionar_equipe(equipe, categoria,logo_id)
            if id is not None:
                st.success("Equipe cadastrada com sucesso!")
                st.rerun()
            else:
                st.error(f"O equipe '{equipe}' na categoria '{categoria}' já está cadastrado.")
                db_manager.rollback()
@st.dialog("Excluir equipe")
def excluir_equipe_dialog():
    
    lista_equipes = db_manager.listar_equipes()
    dict_equipes = {equipe[1]+ " " + equipe[2]:equipe[0] for equipe in lista_equipes}
    equipe = st.selectbox('Selecione o equipe', options=dict_equipes.keys(), index=None)
    
    if equipe:
        equipe_id =dict_equipes[equipe]
        st.warning("Isso excluirá permanentemente todos os dados associados a esse time. Você tem certeza?", icon="⚠️")
        if st.button("Excluir", key=f"excluir_equipe_dialog"):
            if db_manager.deletar_equipe(equipe_id):
                st.success(f"Equipe deletada com sucesso!")
                time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                st.rerun()    
            else:
                st.error('Erro na hora de excluir time. Tente novamente')
                db_manager.rollback()         
                time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                st.rerun()     
                    
@st.dialog("Editar equipe")
def editar_equipe_dialog():
    opcoes_categoria = ['Principal', 'Sub-20']
    lista_equipes = db_manager.listar_equipes()
    dict_equipes = {equipe[1]+ " " + equipe[2]:equipe[0] for equipe in lista_equipes}
    equipe = st.selectbox('Selecione o equipe', options=dict_equipes.keys(), index=None)
    
    if equipe:
        equipe_id =dict_equipes[equipe]
        dados_equipe = db_manager.listar_dados_equipe(equipe_id)
        if dados_equipe:
            nome_equipe, categoria_equipe,logo_id = dados_equipe
            equipe = st.text_input("Nome da Equipe", value=nome_equipe) 
            categoria = st.selectbox("Selecione a categoria", options=opcoes_categoria, index=opcoes_categoria.index(categoria_equipe))
            logo_equipe= st.text_input("Adicione o id da equipe", value=logo_id)
        
        
        if st.button("Editar", key=f"editar_equipe_dialog"):
            if not equipe or not categoria:
                st.error("Por favor, preencha todos os campos.")
            else:    
                try:
                    db_manager.atualizar_equipe(equipe_id,equipe,categoria,logo_equipe)
                    st.success(f"Equipe atualizada com sucesso!")
                    time.sleep(1)  # Pausa de 2 segundos para mostrar a mensagem antes de atualizar a página
                    st.rerun()    
                except Exception as e:
                    st.error(f"Erro ao atualizar equipe: {e}")
                    db_manager.rollback()         
                    


botao_adicionar_equipe,botao_editar_equipe, botao_excluir_equipe = st.columns(3)
with botao_adicionar_equipe:
    if st.button("Adicionar equipe", key="adicionar_equipe"):
        adicionar_equipe_dialog()
with botao_editar_equipe:
    if st.button("Editar equipe", key="editar_equipe"):
        editar_equipe_dialog()
with botao_excluir_equipe:
    if st.button("Excluir equipe", key="exluir_equipe"):
        excluir_equipe_dialog()
        
        
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)         