import streamlit as st
import streamlit.components.v1 as components
from db_manager import get_db_manager
from utils import listar_jogadas_com_tempo,formatar_hhmmss
import re
import atexit   

if "tempo_inicio_partida" not in st.session_state:
    st.session_state["tempo_inicio_partida"] = None

db_manager = get_db_manager()
lista_jogos = db_manager.listar_jogos()

opcoes_jogos = {f"{j[2]} x {j[4]} - {j[6]} - {j[7]} - {j[8]}": j[0] for j in lista_jogos}
jogo_selecionado = st.selectbox("Selecione um jogo", options=opcoes_jogos.keys(), index=None)

if jogo_selecionado:
    jogo_id = opcoes_jogos[jogo_selecionado]
    link_youtube = st.text_input("Insira o link da transmissão (YouTube):")

    if link_youtube:
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", link_youtube)
        if match:
            video_id = match.group(1)
            lista_jogadas_df = listar_jogadas_com_tempo(db_manager, jogo_id)
            lista_jogadas_df =  lista_jogadas_df.reset_index()

            if not lista_jogadas_df.empty:

                # Opções de filtros
                tipos_jogadas = lista_jogadas_df["jogada"].unique()
                jogadores = lista_jogadas_df["jogador_nome"].unique()

                # Linhas da tabela
                linhas_html = ""
                for idx, row in lista_jogadas_df.iterrows():
                    tempo_formatado = formatar_hhmmss(row['tempo_relativo_jogada'])
                    linhas_html += f"""
                    <tr data-tempo="{row['tempo_relativo_jogada']}" data-tempo-original="{row['tempo_relativo_jogada']}" style="background-color:{'#ffffff' if idx%2==0 else '#e6e6e6'};">
                        <td>{idx}</td>
                        <td>{row['jogada']}</td>
                        <td>{row['jogador_nome']}</td>
                        <td>{row['quadrante']}</td>
                        <td>{tempo_formatado}</td>
                        <td><button onclick="seekToTime({row['tempo_relativo_jogada']})">Ir</button></td>
                    </tr>
                    """

                                # HTML completo
                html_code = f"""
                            <style>
                            body {{
                                font-family: Arial, sans-serif;
                                color: #333;
                            }}
                            table {{
                                width: 100%;
                                border-collapse: collapse;
                                font-size: 14px;
                                font-family: Arial, sans-serif;
                                color: #222;
                                border-radius: 20px;
                            }}
                            th {{
                                background-color: #ddd;
                                font-weight: bold;
                                color: black;
                                font-size: 15px;
                                text-align: left;
                                padding: 5px;
                            }}
                            td {{
                                padding: 5px;
                                color: #444;
                            }}
                            select {{
                                font-size: 14px;
                                color: white;
                                background-color: black;
                                padding: 5px;
                                font-family: Arial, sans-serif;
                                border-radius: 6px;
                            }}
                            label {{
                                font-weight: bold;
                                font-size: 15px;
                                color: white;
                            }}
                            p {{
                                font-size: 16px;
                                color: #d9534f;
                                font-weight: bold;
                                font-family: Arial, sans-serif;
                            }}
                            button {{
                                font-size: 14px;
                                padding: 5px 10px;
                                cursor: pointer;
                                border-radius: 6px;
                            }}
                            </style>

                            <div style="display:flex; gap:20px; align-items:flex-start;">
                                <div style="flex:1; min-width:400px; text-align:center;">
                                    <div id="player"></div>
                                    <p style="font-weight:bold; color:white; margin-top:10px;">
                                        Arraste o player até a conclusão da primeira jogada e clique em sincronizar.
                                    </p>
                                    <div style="margin-top:10px; display:flex; gap:10px; justify-content:center;">
                                        <button onclick="somarTempo()">Sincronizar</button>
                                        <button onclick="resetarTempos()">Resetar</button>
                                    </div>
                                </div>

                                <div style="flex:1; display:flex; flex-direction:column; max-width:600px;">
                                    <div style="display:flex; gap:10px; margin-bottom:5px;">
                                        <div>
                                            <label for="filtroJogada">Filtrar por jogada:</label>
                                            <select id="filtroJogada" onchange="filtrarTabela()" style="padding:5px;">
                                                <option value="">Todas</option>
                                                {''.join([f'<option value="{j}">{j}</option>' for j in tipos_jogadas])}
                                            </select>
                                        </div>
                                        <div>
                                            <label for="filtroJogador">Filtrar por jogador:</label>
                                            <select id="filtroJogador" onchange="filtrarTabela()" style="padding:5px;">
                                                <option value="">Todos</option>
                                                {''.join([f'<option value="{j}">{j}</option>' for j in jogadores])}
                                            </select>
                                        </div>
                                    </div>

                                    <div style="max-height:400px; overflow-y:auto; border:1px solid #ccc; background-color:#fff;">
                                        <table id="tabelaJogadas" style="width:100%; border-collapse: collapse; font-size:14px;">
                                            <tr style='background-color:#ddd; position:sticky; top:0;'>
                                                <th>Ordem</th>
                                                <th>Jogada</th>
                                                <th>Jogador</th>
                                                <th>Quadrante</th>
                                                <th>Tempo</th>
                                                <th>Ação</th>
                                            </tr>
                                            {linhas_html}
                                        </table>
                                    </div>
                                </div>
                            </div>

                            <script>
                            function formatarTempo(segundos) {{
                                var hrs = Math.floor(segundos / 3600);
                                var min = Math.floor((segundos % 3600) / 60);
                                var seg = Math.floor(segundos % 60);
                                return (hrs > 0 ? String(hrs).padStart(2,'0') + ':' : '') +
                                    String(min).padStart(2,'0') + ':' +
                                    String(seg).padStart(2,'0');
                            }}

                            var tag = document.createElement('script');
                            tag.src = "https://www.youtube.com/iframe_api";
                            var firstScriptTag = document.getElementsByTagName('script')[0];
                            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

                            var player;
                            function onYouTubeIframeAPIReady() {{
                                player = new YT.Player('player', {{
                                    height: '360',
                                    width: '100%',
                                    videoId: '{video_id}',
                                    playerVars: {{ 'autoplay': 0, 'controls': 1, 'rel': 0, 'enablejsapi': 1 }},
                                    events: {{ 'onReady': onPlayerReady }}
                                }});
                            }}

                            function onPlayerReady(event) {{
                                setInterval(function() {{
                                    if(player) {{}}
                                }}, 500);
                            }}

                            function seekToTime(seconds) {{
                                if(player) {{
                                    player.seekTo(seconds, true);
                                }}
                            }}

                            // Sincronizar descontando 10 segundos
                            function somarTempo() {{
                                var tempoAtual = player.getCurrentTime() - 10;
                                if (tempoAtual < 0) tempoAtual = 0;

                                var linhas = document.querySelectorAll("#tabelaJogadas tr[data-tempo]");
                                linhas.forEach(function(linha) {{
                                    var tempoOriginal = parseFloat(linha.getAttribute("data-tempo-original"));
                                    var tempoNovo = tempoOriginal + tempoAtual;
                                    linha.setAttribute("data-tempo", tempoNovo);
                                    // Atualiza coluna de tempo e botão
                                    linha.cells[4].innerText = formatarTempo(tempoNovo);
                                    linha.cells[5].children[0].setAttribute("onclick", "seekToTime(" + tempoNovo + ")");
                                }});
                            }}

                            // Resetar para valores originais
                            function resetarTempos() {{
                                var linhas = document.querySelectorAll("#tabelaJogadas tr[data-tempo]");
                                linhas.forEach(function(linha) {{
                                    var tempoOriginal = parseFloat(linha.getAttribute("data-tempo-original"));
                                    linha.setAttribute("data-tempo", tempoOriginal);
                                    linha.cells[4].innerText = formatarTempo(tempoOriginal);
                                    linha.cells[5].children[0].setAttribute("onclick", "seekToTime(" + tempoOriginal + ")");
                                }});
                            }}

                            // Filtrar tabela
                            function filtrarTabela() {{
                                var filtroJogada = document.getElementById('filtroJogada').value.toLowerCase();
                                var filtroJogador = document.getElementById('filtroJogador').value.toLowerCase();
                                var linhas = document.querySelectorAll("#tabelaJogadas tr[data-tempo]");
                                linhas.forEach(function(linha) {{
                                    var jogada = linha.cells[1].innerText.toLowerCase();
                                    var jogador = linha.cells[2].innerText.toLowerCase();
                                    linha.style.display = ((filtroJogada && jogada !== filtroJogada) || (filtroJogador && jogador !== filtroJogador)) ? 'none' : '';
                                }});
                            }}
                            </script>
                            """


                components.html(html_code, height=600)

            else:
                st.warning("Jogo sem jogadas adicionadas")
        else:
            st.error("Link inválido.")
    else:
        st.info("Insira o link da transmissão para exibir o vídeo e os dados.")

atexit.register(db_manager.fechar_conexao)
