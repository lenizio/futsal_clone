import streamlit as st
from db_manager import DBManager
import atexit


db_manager = DBManager()
db_manager.criar_tabelas()

equipes_page = st.Page("equipes.py", title="Times")
analise_tempo_real_page = st.Page("analise_tempo_real.py", title="Análise Tempo Real")
jogos_page = st.Page("jogos.py", title="Jogos")
jogadas_page = st.Page("jogadas.py", title="Jogadas")
analise_atleta_page = st.Page("analise_atleta.py", title="Análise Atleta")
pg = st.navigation([equipes_page,jogos_page,jogadas_page,analise_tempo_real_page, analise_atleta_page])
st.set_page_config(page_title="Análise Futsal", layout="wide")
pg.run()

if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)