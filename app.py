import streamlit as st
from db_manager import DBManager


db_manager = DBManager()
db_manager.criar_tabelas()

equipes_page = st.Page("equipes.py", title="Times")
jogadores_page = st.Page("jogadores.py", title="Jogadores")
jogos_page = st.Page("jogos.py", title="Jogos")
jogadas_page = st.Page("jogadas.py", title="Jogadas")

pg = st.navigation([equipes_page,jogadores_page,jogos_page,jogadas_page])
st.set_page_config(page_title="Análise Futsal")
pg.run()