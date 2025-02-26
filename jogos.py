import streamlit as st
import pandas as pd
from datetime import datetime
from db_manager import DBManager,get_db_manager
from utils import convert_df_to_csv, calcular_quadrante
import atexit


db_manager = get_db_manager()

lista_equipes = db_manager.listar_equipes()
lista_jogos = db_manager.listar_jogos()

if len(lista_equipes) <= 1:
    st.warning("Adicione mais equipes.")
    
@st.dialog("Adicionar Jogos")
def adicionar_jogos_dialog(lista_equipes):
    dict_equipes = {equipe[1] + " " + equipe[2]: equipe[0] for equipe in lista_equipes}
    
    # Seleciona a equipe mandante
    equipe_mandante = st.selectbox("Equipe Mandante", options=dict_equipes.keys(), index=None)
    
    if equipe_mandante:
        # Cria o dicionário de equipes restantes excluindo a mandante
        equipes_restantes = {equipe: dict_equipes[equipe] for equipe in dict_equipes if equipe != equipe_mandante}
        
        # Seleciona a equipe visitante
        equipe_visitante = st.selectbox("Equipe Visitante", options=equipes_restantes.keys(), index=None)
        
        if equipe_mandante and equipe_visitante:  # Verifica se ambas as equipes foram selecionadas
            data = st.date_input("Data do Jogo", value=datetime.today())
            competicao = st.selectbox("Competição",('Liga','Metropolitano','Mineiro',"Amistoso"),index=None)
            fase = st.selectbox("Fase", ('Classificação','Final'), index = None)
            opcoes_rodada=[]
            if fase == "Classificação":
                # Gera rodadas numeradas de 1 a 23
                opcoes_rodada = [f"{i}ª Rodada" for i in range(1, 24)]
            elif fase == "Final":
                # Opções específicas para a fase final
                opcoes_rodada = ["Oitavas","Quartas","Semifinal", "Final"]

                # Selectbox para escolher a rodada
            rodada = st.selectbox("Rodada", opcoes_rodada, index = None)
            
            # Obtém os IDs das equipes selecionadas
            id_equipe_mandante = dict_equipes[equipe_mandante]
            id_equipe_visitante = equipes_restantes[equipe_visitante]
            
            # Processa os dados ao clicar no botão de submissão
            if st.button("Adicionar Jogo", key="adicionar_jogo_dialog"):
                if not equipe_mandante or not equipe_visitante or not data or not fase or not rodada or not competicao:
                    st.error("Preencha todos os campos")
                else:
                    try:
                        # Chama a função para adicionar o jogo no banco de dados
                        id_jogo = db_manager.adicionar_jogo(
                            equipe_mandante_id=id_equipe_mandante,
                            equipe_mandante_nome=equipe_mandante,
                            equipe_visitante_id=id_equipe_visitante,
                            equipe_visitante_nome=equipe_visitante,
                            data=data,
                            fase=fase,
                            rodada=rodada,
                            competicao=competicao
                        )
                        st.success(f"Jogo adicionado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao adicionar jogo: {e}")
@st.dialog("Deletar Jogos")
def deletar_jogos_dialog(lista_jogos):
    opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
    jogo_selecionado = st.selectbox("Selecinoe um jogo para excluir", options=opcoes_jogos.keys(), index=None)
    
    if jogo_selecionado:
        jogo_id = opcoes_jogos[jogo_selecionado]
        if st.button("Exluir Jogo", key="excluir_jogo_dialog"):
            try:
                db_manager.deletar_jogo(jogo_id)
                st.success(f"Jogo deletado com sucesso!")
                st.rerun()
            except Exception as e:
                        st.error(f"Erro ao deletar jogo: {e}")

@st.dialog("Baixar Jogadas")
def baixar_jogadas_dialog(lista_jogos):

        opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
        jogo_selecionado = st.selectbox("Selecinoe um jogo para baixar jogadas", options=opcoes_jogos.keys(), index=None)
        
        if jogo_selecionado:
            jogo_id = opcoes_jogos[jogo_selecionado]
            lista_jogadas = db_manager.listar_jogadas_por_partida(jogo_id)
            lista_jogadas_df = pd.DataFrame(lista_jogadas, columns=["equipe_mandante_nome","equipe_visitante_nome","fase","rodada","competicao","jogador_nome","jogada","tempo","x_loc","y_loc"])
            if not lista_jogadas_df.empty:
                lista_jogadas_df['quadrante'] = lista_jogadas_df.apply(lambda row: calcular_quadrante(row['x_loc'], row['y_loc']), axis=1)
                lista_jogadas_df.drop(["x_loc","y_loc"],axis=1, inplace=True)
                csv_data = convert_df_to_csv(lista_jogadas_df)

                # Botão para download do CSV
                if st.download_button(
                    label="Baixar CSV",
                    data=csv_data,
                    file_name= jogo_selecionado + ".csv",
                    mime="text/csv"
                ):
                    st.rerun()
            else:
                st.warning("Jogo sem jogadas adicionadas")
            
        
    
column1, column2, column3 = st.columns([1,1,3])           

with column1:
    if st.button("Adicionar Jogos", key="adicionar_jogos"):
        adicionar_jogos_dialog(lista_equipes)
with column2:
    if st.button("Excluir Jogos", key="excluir_jogos"):
        deletar_jogos_dialog(lista_jogos)
with column3:
    if st.button("Baixar Jogadas", key="baixar_jogadas"):
        baixar_jogadas_dialog(lista_jogos)        

if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    df = pd.DataFrame(lista_jogos, columns=["id",'equipe_mandante_id',"Equipe Mandante","equipe_visitante_id" ,"Equipe Visitante","date" ,"Competição","Fase", "Rodada"])
    df = df.drop(columns=["id","date",'equipe_mandante_id',"equipe_visitante_id"])
    st.dataframe(df, hide_index=True)

    
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao) 