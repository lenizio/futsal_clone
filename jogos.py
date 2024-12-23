import streamlit as st
import pandas as pd
from datetime import datetime
from db_manager import DBManager

db_manager = DBManager()

clubes = db_manager.listar_equipes()  # Função para listar clubes únicos

if len(clubes) <= 1:
    st.warning("Adicione mais equipes.")
    
@st.dialog("Adicionar Jogos")
def adicionar_jogos_dialog():
    lista_equipes = db_manager.listar_equipes()
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
            competicao = st.selectbox("Competição",('Liga','Metropolitano','Mineiro'),index=None)
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
        
lista_jogos = db_manager.listar_jogos()

if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    df = pd.DataFrame(lista_jogos, columns=["id",'equipe_mandante_id',"Equipe Mandante","equipe_visitante_id" ,"Equipe Visitante","date" ,"Competição","Fase", "Rodada"])
    df = df.drop(columns=["id","date",'equipe_mandante_id',"equipe_visitante_id"])
    st.dataframe(df, hide_index=True)
    
if st.button("Adicionar Jogos", key="adicionar_jogos"):
    adicionar_jogos_dialog()
    
