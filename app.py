import streamlit as st
from db_manager import DBManager, get_db_manager
import atexit

# Configuração da página: deve ser o primeiro comando Streamlit
st.set_page_config(page_title="Análise Futsal", layout="wide")

# Inicialização do banco de dados
db_manager = get_db_manager()
db_manager.criar_tabelas()
# Definição das páginas
equipes_page = st.Page("equipes.py", title="Times")
analise_tempo_real_page = st.Page("analise_tempo_real.py", title="Análise Tempo Real")
jogos_page = st.Page("jogos.py", title="Jogos")
jogadas_page = st.Page("jogadas.py", title="Jogadas")
analise_atleta_page = st.Page("analise_atleta.py", title="Análise Atleta")
analise_gols_page = st.Page("analise_gols.py",title= "Análise Gols")
analise_gols_vizu_page = st.Page("analise_gols_vizu.py",title= "Análise Gols Visualização")


pg = st.navigation([equipes_page, jogos_page, jogadas_page, analise_tempo_real_page, analise_atleta_page,analise_gols_page,analise_gols_vizu_page ])
pg.run()

# Fechar conexão com o banco de dados ao encerrar o app
if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao)
