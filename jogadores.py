import streamlit as st
import streamlit.components.v1 as components

# HTML para exibir o player do YouTube e capturar o tempo
video_html = """
<div id="player"></div>
<form onsubmit="return sendTime()">
  <button type="submit">Enviar Formulário</button>
</form>
<script>
  // Carrega a API do YouTube
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/iframe_api";
  var firstScriptTag = document.getElementsByTagName('script')[0];
  firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

  var player;
  function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
      height: '390',
      width: '640',
      videoId: 'YOUTUBE_VIDEO_ID',
      playerVars: {
        'origin': window.location.origin
      },
      events: {
        'onReady': onPlayerReady
      }
    });
  }

  function onPlayerReady(event) {
    console.log("Player está pronto");
  }

  function sendTime() {
    const currentTime = player.getCurrentTime();
    const iframe = document.createElement('iframe');
    iframe.style.display = "none";
    iframe.src = `/capture?time=${currentTime}`;
    document.body.appendChild(iframe);
    return true; // Permite o envio do formulário
  }
</script>
"""

# Substitua 'YOUTUBE_VIDEO_ID' pelo ID do vídeo do YouTube
video_html = video_html.replace("I9mkyG9UyOM", "dQw4w9WgXcQ")  # Exemplo de ID de vídeo

st.markdown("### Vídeo do YouTube com Formulário")
components.html(video_html, height=400)

# Captura os dados enviados pela URL
if "capture" in st.query_params():
    video_time = st.query_params()["capture"][0]
    st.write(f"Tempo do vídeo: {video_time} segundos")
