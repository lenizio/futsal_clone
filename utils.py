import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

def listar_opces_jogadores(lista_jogadores):
    opcoes_jogadores_dict={}
    opcoes_goleiro_dict = {jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Goleiro"}
    opcoes_jogadores_dict.update(opcoes_goleiro_dict)
    opcoes_goleiro_list = list(opcoes_goleiro_dict.keys())                    
    opcoes_jogadores_linha_dict = {}
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Fixo"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala D"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Ala E"})
    opcoes_jogadores_linha_dict.update({jogador[3]: [jogador[0], jogador[1]] for jogador in lista_jogadores if jogador[2] == "Pivô"})
    opcoes_jogadores_linha_list = list(opcoes_jogadores_linha_dict.keys())
    opcoes_jogadores_linha_list.sort()
    opcoes_jogadores_list=opcoes_goleiro_list+opcoes_jogadores_linha_list
    opcoes_jogadores_dict.update(opcoes_jogadores_linha_dict)
    
    return opcoes_jogadores_dict, opcoes_jogadores_list

def pegar_dados_pizza_plot(lista_jogadas):
    df = pd.DataFrame(lista_jogadas,columns=["id","jogador_id","jogador_nome","jogo_id","jogada","x_loc","y_loc"])
    tipos_finalizacoes = ["FIN.C", "FIN.E", "FIN.T"]    
    quantidade_finalizacoes = df.jogada[df["jogada"].isin( tipos_finalizacoes)].value_counts().reindex( tipos_finalizacoes, fill_value=0)
    quantidade_finalizacoes = quantidade_finalizacoes.to_numpy()
    
    tipos_desarmes = ['DES.C/P.', 'DES.S/P.']
    quantidade_desarmes = df.jogada[df["jogada"].isin(tipos_desarmes)].value_counts().reindex(tipos_desarmes,fill_value=0)
    quantidade_desarmes = quantidade_desarmes.to_numpy()
    
    percas_de_posse = ['PER.P', 'C.A']
    quantidade_percas_posse = df.jogada[df["jogada"].isin(percas_de_posse)].value_counts().reindex(percas_de_posse,fill_value=0)
    quantidade_percas_posse = quantidade_percas_posse.to_numpy()

    dados_grafico_pizza = [
        {
            "data": quantidade_finalizacoes,
            "labels": tipos_finalizacoes,
            "title": "Distribuição de Finalizações"
        },
        {
            "data": [quantidade_finalizacoes[0], sum(quantidade_finalizacoes)],  # Finalização certa / errada
            "labels": ["Certas", "Erradas"],
            "title": "Eficiência de Finalizações"
        },
        {
            "data": quantidade_desarmes,
            "labels": tipos_desarmes ,
            "title": "Distribuição de Desarmes"
        },
        {
            "data": quantidade_percas_posse,
            "labels":  percas_de_posse,
            "title": "Distribuição de Perdas de Posse"
        }
    ]
    
    return dados_grafico_pizza

def pizza_plot(dados_grafico_pizza):
    # Criar uma lista de figuras do Plotly
    figs = []

    # Iterar sobre os dados e gerar gráficos de pizza
    for dado in dados_grafico_pizza:
        data = dado["data"]
        labels = dado["labels"]
        title = dado["title"]

        # Criar gráfico de pizza
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=data,
            textinfo="percent+value",  # Exibir porcentagem e valor absoluto
            pull=[0.1] * len(labels),  # Se quiser destacar um pedaço, use esse parâmetro
            marker=dict(line=dict(color="white", width=1)),  # Bordas brancas
        )])
        
        fig.update_layout(
            title=title,
            showlegend=True
        )
        
        # Adicionar a figura gerada à lista de figuras
        figs.append(fig)
    
    return figs