import streamlit as st
from db_manager import DBManager,get_db_manager
import atexit
from utils import extrair_dados_caracteristicas_gols,extrair_dataframe_analise_gols,plotar_caracteristicas_gols,plotar_caracteristicas_gols_invertido,plotar_caracteristicas_gols_1,plotar_caracteristicas_gols_2,extrair_dados_caracteristicas_gols_1, plotar_caracteristicas_gols_2_invertido
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime




db_manager = get_db_manager()
df_gols_total = extrair_dataframe_analise_gols(db_manager)
opcoes_equipes = df_gols_total['Equipe Analisada'].unique().tolist()
opcoes_equipes_restante = []
col1, col2 = st.columns([1, 1])
today = datetime.datetime.now()
next_year = today.year + 1
jan_1 = datetime.date(today.year, 1, 1)
dec_31 = datetime.date(today.year, 12, 31)

with col1:
    filtro_equipe_1 = st.selectbox("Selecione uma equipe",options=opcoes_equipes,index=None)
if filtro_equipe_1:
    opcoes_equipes_restante = [equipe for equipe in opcoes_equipes if equipe != filtro_equipe_1]
    
    
with col2:
    filtro_equipe_2 = st.selectbox("Selecione outra equipe",options=opcoes_equipes_restante,index=None)
    
   
if filtro_equipe_2:
    
    data = st.date_input(
        "Selecio um período",
        value=(jan_1, dec_31),
        min_value=jan_1,
        max_value=dec_31,
        format="MM.DD.YYYY",
        
    )
    
    if isinstance(data, tuple) and len(data) == 2:
        data_inicio, data_fim = data
        
        
        df_gols = df_gols_total[(df_gols_total['Data'] >= data_inicio) & (df_gols_total['Data'] <= data_fim)]
   
    #Figs por tempo
        fig = plotar_caracteristicas_gols_2(df_gols,filtro_equipe_1,filtro_equipe_2)
        fig1 = plotar_caracteristicas_gols_2_invertido(df_gols,filtro_equipe_1,filtro_equipe_2)

        #Figs totais
        fig_total = plotar_caracteristicas_gols(df_gols,filtro_equipe_1,filtro_equipe_2)
        fig_total1 = plotar_caracteristicas_gols_invertido(df_gols,filtro_equipe_1,filtro_equipe_2)
        
        total_tab, por_quarto_tab = st.tabs(['Total','Por Quarto'])
        
        with por_quarto_tab:
        
            with st.container(border=True,height=650):
                st.plotly_chart(fig,config={'displayModeBar': False})
            
            with st.container(border=True,height=650):
                st.plotly_chart(fig1,config={'displayModeBar': False})
        
        with total_tab:
        
            with st.container(border=True,height=650):
                st.plotly_chart(fig_total,config={'displayModeBar': False})
            
            with st.container(border=True,height=650):
                st.plotly_chart(fig_total1,config={'displayModeBar': False})             































if hasattr(st, "on_event") and callable(getattr(st, "on_event")):
    st.on_event("shutdown", db_manager.fechar_conexao)
else:
    atexit.register(db_manager.fechar_conexao) 