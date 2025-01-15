import streamlit as st
from db_manager import DBManager,get_db_manager
from utils import listar_opces_jogadores, pegar_dados_pizza_plot, pizza_plot
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, Circle
import plotly.tools as tls
import plotly.graph_objects as go
import atexit



db_manager = get_db_manager()

# Exemplo de lista de jogos
lista_jogos = db_manager.listar_jogos()

if not lista_jogos:
    st.warning("Sem jogos registrados")  
else:
    opcoes_jogos = {f"{jogo[2]} x {jogo[4]} - {jogo[6]} - {jogo[7]} - {jogo[8]}" : jogo[0] for jogo in lista_jogos}
    jogo_selecionado = st.selectbox("Selecione um jogo para analisar",options=opcoes_jogos.keys(),index=None)
    
    if jogo_selecionado:
        jogo_id = opcoes_jogos[jogo_selecionado]
        lista_jogadas = db_manager.listar_jogadas_por_jogo(jogo_id)
        
        dados_grafico_pizza = pegar_dados_pizza_plot(lista_jogadas)
        figs = pizza_plot(dados_grafico_pizza)
        cols = st.columns(2)  

        for i, fig in enumerate(figs):
            col = cols[i % 2]  
            col.plotly_chart(fig)


if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao) 