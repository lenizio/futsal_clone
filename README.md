# 🏆 Análise de Futsal

Este repositório contém uma aplicação **Streamlit** para **análise de desempenho de futsal**, permitindo o gerenciamento de equipes, jogadores, jogos e a visualização de dados em tempo real. O aplicativo se conecta a um banco de dados **PostgreSQL** para armazenar e recuperar todas as informações.

🔗 **Acesse a aplicação online**: [https://scoutfutsal.streamlit.app/](https://scoutfutsal.streamlit.app/)

---

## ⚙️ Funcionalidades

A aplicação está dividida em várias seções para cobrir todo o fluxo de trabalho de análise:

- **Times (`equipes.py`)**  
  Gerenciamento completo de equipes e jogadores. Permite adicionar, editar e excluir equipes e seus respectivos atletas.

- **Jogos (`jogos.py`)**  
  Registro de partidas. Você pode cadastrar jogos, detalhando equipes mandante e visitante, competição, fase e rodada. Também permite baixar as jogadas de um jogo específico em formato CSV.

- **Jogadas (`jogadas.py`)**  
  Ferramenta interativa para registrar jogadas durante uma partida. Usando um mapa de quadra clicável, é possível marcar a localização de eventos como finalizações, desarmes, perdas de posse, entre outros, para jogadores específicos e em tempos específicos do jogo.

- **Análise em Tempo Real (`analise_tempo_real.py`)**  
  Painel de análise que fornece estatísticas gerais de um time, gráficos de barras comparativos por tempo de jogo e heatmaps de localização das jogadas na quadra.

- **Análise de Atleta (`analise_atleta.py`)**  
  Focado no desempenho individual, este módulo exibe estatísticas detalhadas de um jogador, comparando suas ações com a média da equipe e mostrando a localização de suas jogadas.

---

## 🗂️ Estrutura do Projeto
```
├── app.py                  # Arquivo principal do Streamlit
├── db_manager.py           # Conexão e funções para o banco de dados PostgreSQL
├── utils.py                # Funções auxiliares (pandas, plotly, matplotlib, etc.)
├── equipes.py              # Página de gerenciamento de times e jogadores
├── jogos.py                # Página de gerenciamento de jogos
├── jogadas.py              # Página para registrar jogadas
├── analise_tempo_real.py   # Visualização da análise de times
├── analise_atleta.py       # Visualização da análise de atletas individuais
├── futsal_court.jpg        # Imagem da quadra usada na interface
├── requirements.txt        # Lista de dependências
```

## 🧰 Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [PostgreSQL](https://www.postgresql.org/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)
- [Matplotlib](https://matplotlib.org/)




📄 Licença
Este projeto está licenciado sob a MIT License.

👤 Autor
Lenizio Oliveira
