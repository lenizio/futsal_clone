import streamlit as st
from db_manager import DBManager
from utils import listar_opces_jogadores, pegar_dados_pizza_plot, pizza_plot
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, Circle
import plotly.tools as tls
import plotly.graph_objects as go


db_manager = DBManager()

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

image_path = 'futasl_court.jpg'  # Substitua pelo caminho correto ou URL da sua imagem

# Crie uma figura Plotly com a imagem
fig = go.Figure(go.Image(
    source=image_path
))

# Ajuste os eixos se necessário (por exemplo, para manter a proporção da imagem)


# Exibir a imagem no Streamlit
st.plotly_chart(fig)


def draw_court(ax=None, color='gray', lw=2):
    # Se um objeto ax não for fornecido, cria-se um novo
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # Área de gol na parte inferior da quadra
    gol_area_line_bottom = Rectangle((-31, 121), 61, 0, linewidth=lw, color=color)
    gol_area_right_arc_bottom = Arc((30, 0), 240, 240, theta1=0, theta2=90, linewidth=lw, color=color)
    gol_area_left_arc_bottom = Arc((-30, 0), 240, 240, theta1=90, theta2=180, linewidth=lw, color=color)

    # Área de gol na parte superior da quadra (espelhada verticalmente)
    gol_area_line_top = Rectangle((-16, 680), 60, 0, linewidth=lw, color=color)
    gol_area_right_arc_top = Arc((16, 800), 240, 240, theta1=270, theta2=360, linewidth=lw, color=color)
    gol_area_left_arc_top = Arc((-16, 800), 240, 240, theta1=180, theta2=270, linewidth=lw, color=color)

    center_line = Rectangle((-200, 400), 400, 0, linewidth=lw, color=color)
    center_circle = Circle((0, 400), 60, linewidth=lw, color=color, fill=False)

    outer_lines = Rectangle((-200, 0), 400, 800, linewidth=lw, color=color, fill=False)

    # Lista de todos os elementos da quadra, incluindo as áreas de gol
    court_elements = [
        gol_area_right_arc_bottom, gol_area_left_arc_bottom,
        gol_area_line_bottom,
        gol_area_right_arc_top, gol_area_left_arc_top, gol_area_line_top,
        center_line, center_circle, outer_lines
    ]

    # Adiciona todos os elementos ao gráfico
    for element in court_elements:
        ax.add_patch(element)

    ax.set_aspect('equal')
    return ax

fig, ax = plt.subplots(figsize=(12, 11))
draw_court(ax, color="white")
ax.set_xlim(-300, 300)
ax.set_ylim(-100, 1000)
ax.axis('off')
plotly_fig = tls.mpl_to_plotly(fig)
st.plotly_chart(plotly_fig)
