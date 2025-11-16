import streamlit as st
from streamlit.components.v1 import html
import base64
from pathlib import Path
import json

st.set_page_config(page_title="Flappy Game", layout="wide")
st.title("Flappy Game — Fixed Background Music (No Upload Needed)")
st.write("Press Start → 3..2..1 countdown → game + fixed background music will start.")

# -----------------------------
# Correct path to your music file in GitHub repo
# -----------------------------
MUSIC_PATH = "miaw-miaw-miaw-song-sad-lyrics-video-visual_XBvfuPbJ.mp3"

if not Path(MUSIC_PATH).exists():
    st.error(f"Music file not found: {MUSIC_PATH}")
    st.stop()

def file_to_data_url(path):
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:audio/mpeg;base64,{b64}"

music_url = file_to_data_url(MUSIC_PATH)

# No custom sprites
player_url = ""
obstacle_url = ""
bg_url = ""

# Start button
start_game = st.button("Start / Restart Game")

game_html_template = """
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html,body { margin:0; height:100%; background:#111; }
  #gameArea { display:flex; justify-content:center; align-items:center; height:100vh; }
  canvas { background:#70c5ce; border-radius:12px; }
  #countdownOverlay {
    position:absolute; inset:0; display:flex; justify-content:center; align-items:center;
    background:rgba(0,0,0,0.6); visibility:hidden;
  }
  #countTxt { font-size:120px; color:white; font-weight:900; }
  #scoreDisplay {
    position:absolute; top:10px; left:10px; padding:8px 12px;
    background:rgba(0,0,0,0.3); color:white; font-size:22px; border-radius:8px;
  }
</style>
</head>
<body>

<div id="scoreDisplay">Score: 0</div>
<div id="countdownOverlay"><div id="countTxt">3</div></div>
<div id="gameArea"><canvas id="gameCanvas" width="720" height="480"></canvas></div>

<script>
(() => {

  const MUSIC_URL = __MUSIC_URL__;
  const START_FROM_PY = __START_FROM_PY__;

  let canvas = document.getElementById("gameCanvas");
  let ctx = canvas.getContext("2d");
  let W = canvas.width, H = canvas.height;

  let bgm = new Audio(MUSIC_URL);
  bgm.loop = true;
  bgm.volume = 0.6;

  let bird = { x:100, y:H/2, vel:0, w:40, h:30 };
  let gravity = 0.45;
  let lift = -9;
  let pipes = [];
  let spawnTimer = 0;
  let score = 0;
  let best = localStorage.getItem("best_flappy") || 0;
  let playing = false;
  let last = null;

  function resetGame(){
    bird.y = H/2;
    bird.vel = 0;
    pipes = [];
    spawnTimer = 0;
    score = 0;
    last = null;
    updateScore();
  }

  function updateScore(){
    document.getElementById("scoreDisplay").innerText =
      "Score: " + score + " | Best: " + best;
  }

  function flap(){
    bird.vel = lift;
  }

  // Input
  window.addEventListener("keydown", e => { if(e.code==="Space") flap(); });
  canvas.addEventListener("mousedown", flap);
  canvas.addEventListener("touchstart", e => { e.preventDefault(); flap(); }, {passive:false});

  // Countdown
  function startCountdown(){
    const overlay = document.getElementById("countdownOverlay");
    const txt = document.getElementById("countTxt");
    overlay.style.visibility = "visible";

    let n = 3;
    txt.innerText = n;

    let go = () => {
      n--;
      if(n >= 1){
        txt.innerText = n;
        setTimeout(go,1000);
      } else {
        overlay.style.visibility = "hidden";
        startGame();
      }
    };
    setTimeout(go,1000);
  }

  function startGame(){
    playing = true;
    resetGame();
    bgm.play().catch(()=>{});
    requestAnimationFrame(loop);
  }

  function loop(t){
    if(!last) last = t;
    let dt = t - last;
    last = t;

    // physics
    bird.vel += gravity;
    bird.y += bird.vel;

    // pipes
    spawnTimer += dt;
    if(spawnTimer > 1600){
      spawnTimer = 0;
      let gap = 160;
      let topH = 60 + Math.random() * (H - 260);
      pipes.push({ x:W+40, top:topH, gap:gap });
    }

    for(let i = pipes.length-1; i>=0; i--){
      let p = pipes[i];
      p.x -= 2.8;

      if(!p.scored && p.x + 60 < bird.x){
        score++;
        p.scored = true;
        if(score > best){ best = score; localStorage.setItem("best_flappy", best); }
        updateScore();
      }
      if(p.x < -100) pipes.splice(i,1);
    }

    // Collisions
    let dead = false;
    if(bird.y > H || bird.y < 0) dead = true;

    for(let p of pipes){
      let pipeW = 60;
      if(bird.x + 20 > p.x && bird.x - 20 < p.x + pipeW){
        if(bird.y - 15 < p.top || bird.y + 15 > p.top + p.gap){
          dead = true;
        }
      }
    }

    // Draw
    ctx.clearRect(0,0,W,H);

    // pipes
    ctx.fillStyle = "green";
    for(let p of pipes){
      ctx.fillRect(p.x, 0, 60, p.top);
      ctx.fillRect(p.x, p.top+p.gap, 60, H - (p.top+p.gap));
    }

    // bird
    ctx.fillStyle = "yellow";
    ctx.beginPath();
    ctx.ellipse(bird.x, bird.y, 20, 15, 0, 0, 2*Math.PI);
    ctx.fill();

    if(dead){
      playing = false;
      bgm.pause();
    }

    if(playing) requestAnimationFrame(loop);
  }

  // auto-start if Streamlit button pressed
  if(START_FROM_PY){
    startCountdown();
  }

})();
</script>

</body>
</html>
"""

# Inject values
game_html = (
    game_html_template
    .replace("__MUSIC_URL__", json.dumps(music_url))
    .replace("__START_FROM_PY__", "true" if start_game else "false")
)

html(game_html, height=700, scrolling=False)
