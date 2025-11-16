# flappy_streamlit26.py
import streamlit as st
import base64
import os

st.set_page_config(page_title="Flappy Bird (Upload Assets)", layout="wide")
st.title("Flappy Bird — Upload your images & music")
st.write("Upload background/player/obstacle images and menu/in-game music using the UI below. Then use PLAY (menu) and START (game).")

# --------- Left side: Uploaders ---------
with st.sidebar:
    st.header("Upload your assets (optional)")
    up_bg = st.file_uploader("Background image (png/jpg)", type=["png","jpg","jpeg"], key="bg")
    up_player = st.file_uploader("Player image (png/jpg)", type=["png","jpg","jpeg"], key="player")
    up_pipe = st.file_uploader("Obstacle image (png/jpg)", type=["png","jpg","jpeg"], key="pipe")
    st.markdown("---")
    up_menu_music = st.file_uploader("Menu music (mp3/ogg/wav)", type=["mp3","ogg","wav"], key="menu_music")
    up_ingame_music = st.file_uploader("In-game music (mp3/ogg/wav)", type=["mp3","ogg","wav"], key="ingame_music")
    st.markdown("---")
    st.info("If you don't upload, app will try to use files present in repo root (player_character.png, obstacle_enemy.png, background_image.png, etc.)")

# --------- Helper: convert uploaded file or repo file to data URL ---------
def fileobj_to_data_url(fileobj, default_path=None):
    # if user uploaded fileobj, use it
    if fileobj is not None:
        raw = fileobj.read()
        name = fileobj.name.lower()
        mime = "image/png"
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            mime = "image/jpeg"
        elif name.endswith(".mp3"):
            mime = "audio/mpeg"
        elif name.endswith(".ogg"):
            mime = "audio/ogg"
        elif name.endswith(".wav"):
            mime = "audio/wav"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    # else try repo file fallback
    if default_path and os.path.exists(default_path):
        with open(default_path, "rb") as f:
            raw = f.read()
        ext = default_path.lower().split(".")[-1]
        mime = "image/png"
        if ext in ("jpg", "jpeg"):
            mime = "image/jpeg"
        elif ext == "mp3":
            mime = "audio/mpeg"
        elif ext == "ogg":
            mime = "audio/ogg"
        elif ext == "wav":
            mime = "audio/wav"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    return None

# repo fallback names (change if your repo uses different names)
REPO_BG = "background_image.png"
REPO_PLAYER = "player_character.png"
REPO_PIPE = "obstacle_enemy.png"
REPO_MENU_MUSIC = "Home Screen Music (Only on Menu Screen).mp3"
REPO_INGAME_MUSIC = "ingame_music_1.mp3"

BG_URL = fileobj_to_data_url(up_bg, REPO_BG) or ""
PLAYER_URL = fileobj_to_data_url(up_player, REPO_PLAYER) or ""
PIPE_URL = fileobj_to_data_url(up_pipe, REPO_PIPE) or ""
MENU_MUSIC_URL = fileobj_to_data_url(up_menu_music, REPO_MENU_MUSIC)
INGAME_MUSIC_URL = fileobj_to_data_url(up_ingame_music, REPO_INGAME_MUSIC)

# --------- Generate embedded HTML + JS (escaped braces) ---------
game_html = f"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ margin:0; background:#0b0b0b; color:#fff; font-family:sans-serif; }}
  #canvasWrap {{ width:95%; max-width:1000px; margin: 10px auto; position:relative; }}
  canvas {{ width:100%; height:70vh; background:#000; border-radius:10px; display:block; }}
  #startBtn {{ position:absolute; top:12px; right:12px; z-index:999; background:#ff4757; color:#fff; border:none; padding:10px 14px; border-radius:10px; font-weight:700; }}
  #musicToggle {{ position:absolute; top:12px; left:12px; z-index:999; background:#333; color:#fff; border:none; padding:8px 10px; border-radius:8px; }}
  #menuOverlay {{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:500; pointer-events:none; }}
  #menuCard {{ background: rgba(0,0,0,0.6); padding:20px 22px; border-radius:12px; text-align:center; pointer-events:all; }}
  #menuCard button {{ margin-top:12px; padding:10px 16px; font-weight:700; border-radius:8px; border:none; background:#20bf6b; color:#fff; }}
  #scoreText {{ position:absolute; top:14px; left:50%; transform:translateX(-50%); z-index:999; font-size:28px; font-weight:700; }}
</style>
</head>
<body>
<div id="canvasWrap">
  <div id="scoreText">Score: <span id="score">0</span></div>
  <button id="musicToggle">Music ON</button>
  <button id="startBtn">START</button>

  <div id="menuOverlay">
    <div id="menuCard">
      <h3>Welcome — Use PLAY to allow menu music</h3>
      <p>Upload your own background/player/obstacle and menu/in-game music from the sidebar.</p>
      <button id="menuPlayBtn">PLAY</button>
    </div>
  </div>

  <canvas id="c"></canvas>
</div>

<script>
const PLAYER_URL = "{PLAYER_URL}";
const PIPE_URL = "{PIPE_URL}";
const BG_URL = "{BG_URL}";
const MENU_MUSIC_URL = {('"' + MENU_MUSIC_URL + '"') if MENU_MUSIC_URL else 'null'};
const INGAME_MUSIC_URL = {('"' + INGAME_MUSIC_URL + '"') if INGAME_MUSIC_URL else 'null'};

let menuAudio = null;
let ingameAudio = null;
let musicEnabled = true;

if (MENU_MUSIC_URL) {{
  menuAudio = new Audio(MENU_MUSIC_URL);
  menuAudio.loop = true;
  menuAudio.volume = 0.5;
}}
if (INGAME_MUSIC_URL) {{
  ingameAudio = new Audio(INGAME_MUSIC_URL);
  ingameAudio.loop = true;
  ingameAudio.volume = 0.5;
}}

const menuOverlay = document.getElementById('menuOverlay');
const menuPlayBtn = document.getElementById('menuPlayBtn');
const startBtn = document.getElementById('startBtn');
const musicToggle = document.getElementById('musicToggle');
const scoreSpan = document.getElementById('score');

try {{
  const m = localStorage.getItem('flappy_music_enabled');
  if (m !== null) musicEnabled = m === '1';
  musicToggle.innerText = musicEnabled ? 'Music ON' : 'Music OFF';
}} catch(e){{ console.warn('storage err', e); }}

musicToggle.addEventListener('click', () => {{
  musicEnabled = !musicEnabled;
  musicToggle.innerText = musicEnabled ? 'Music ON' : 'Music OFF';
  try {{ localStorage.setItem('flappy_music_enabled', musicEnabled ? '1' : '0'); }} catch(e){{}}
  if (!musicEnabled) {{
    if (menuAudio) menuAudio.pause();
    if (ingameAudio) ingameAudio.pause();
  }} else {{
    if (!gameRunning && menuAudio) menuAudio.play().catch(()=>{{}});
    if (gameRunning && ingameAudio) ingameAudio.play().catch(()=>{{}});
  }}
}});

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

function resize(){{ canvas.width = Math.min(window.innerWidth*0.95, 1000); canvas.height = Math.min(window.innerHeight*0.72, 700); }}
resize(); window.addEventListener('resize', resize);

let images = {{ bg: null, player: null, pipe: null }};
function loadImage(url){{ return new Promise((res,rej) => {{ let i=new Image(); i.onload = ()=>res(i); i.onerror = rej; i.src = url; }}); }}

let gameRunning = false;
let gameOver = false;
let score = 0;
let player = {{ x: 100, y: 200, vy:0, size:48 }};
let gravity = 0.6;
let jump = -11;
let pipes = [];
let pipeGap = 160;
let pipeTimer = 0;
let last = performance.now();

async function loadAssets() {{
  try {{
    images.bg = BG_URL ? await loadImage(BG_URL) : null;
    images.player = PLAYER_URL ? await loadImage(PLAYER_URL) : null;
    images.pipe = PIPE_URL ? await loadImage(PIPE_URL) : null;
  }} catch(e) {{ console.warn('asset load failed', e); }}
}}

function reset() {{
  score = 0;
  player.y = canvas.height/2;
  player.vy = 0;
  pipes = [];
  gameOver = false;
  scoreSpan.innerText = score;
}}

function spawnPipe() {{
  const margin = Math.floor(canvas.height*0.12);
  const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap) + margin + pipeGap/2);
  pipes.push({{ x: canvas.width + 100, center, scored:false }});
}}

function update(dt) {{
  if (!gameRunning || gameOver) return;
  pipeTimer += dt;
  if (pipeTimer > 1400) {{ pipeTimer = 0; spawnPipe(); }}
  for (let p of pipes) p.x -= 3 * (dt/16);
  if (pipes.length && pipes[0].x + 120 < 0) pipes.shift();
  player.vy += gravity * (dt/16);
  player.y += player.vy * (dt/16);
  for (let p of pipes) {{
    const w = Math.floor(canvas.width * 0.09);
    const topH = p.center - (pipeGap/2);
    const bottomY = p.center + (pipeGap/2);
    if (!p.scored && p.x + w < player.x) {{ p.scored = true; score++; scoreSpan.innerText = score; }}
    const r = Math.max(player.size, player.size) * 0.45;
    const closestX = Math.max(p.x, Math.min(player.x, p.x + w));
    const closestYTop = Math.max(0, Math.min(player.y, topH));
    const dx = player.x - closestX;
    const dyTop = player.y - closestYTop;
    if (dx*dx + dyTop*dyTop <= r*r) gameOver = true;
    const closestYBottom = Math.max(bottomY, Math.min(player.y, canvas.height));
    const dyB = player.y - closestYBottom;
    if (dx*dx + dyB*dyB <= r*r) gameOver = true;
  }}
  if (player.y + player.size > canvas.height) gameOver = true;
}}

function render() {{
  if (images.bg) ctx.drawImage(images.bg, 0, 0, canvas.width, canvas.height);
  else {{ ctx.fillStyle = '#000'; ctx.fillRect(0,0,canvas.width,canvas.height); }}
  for (let p of pipes) {{
    const w = Math.floor(canvas.width * 0.09);
    const topH = p.center - (pipeGap/2);
    if (images.pipe) {{
      ctx.drawImage(images.pipe, p.x, 0, w, topH);
      ctx.drawImage(images.pipe, p.x, p.center + (pipeGap/2), w, canvas.height - (p.center + (pipeGap/2)));
    }} else {{
      ctx.fillStyle = '#2ecc71';
      ctx.fillRect(p.x, 0, w, topH);
      ctx.fillRect(p.x, p.center + (pipeGap/2), w, canvas.height - (p.center + (pipeGap/2)));
    }}
  }}
  if (images.player) ctx.drawImage(images.player, player.x, player.y, player.size, player.size);
  else {{ ctx.fillStyle = '#f1c40f'; ctx.fillRect(player.x, player.y, player.size, player.size); }}
}}

function loop(t) {{
  const dt = t - last;
  last = t;
  update(dt);
  render();
  if (!gameOver) requestAnimationFrame(loop);
  else {{
    if (ingameAudio) ingameAudio.pause();
    try {{
      const prev = parseInt(localStorage.getItem('flappy_best') || '0');
      if (score > prev) localStorage.setItem('flappy_best', String(score));
    }} catch(e){{ console.warn('storage err', e); }}
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff'; ctx.font = '36px sans-serif'; ctx.textAlign='center';
    ctx.fillText('GAME OVER - Score: ' + score, canvas.width/2, canvas.height/2);
  }}
}}

function flap() {{ if (!gameRunning || gameOver) return; player.vy = jump; }}
window.addEventListener('keydown', (e) => {{ if (e.code === 'Space') flap(); }});
canvas.addEventListener('mousedown', (e) => {{ if (!gameRunning) return; flap(); }});
canvas.addEventListener('touchstart', (e) => {{ e.preventDefault(); if (!gameRunning) return; flap(); }}, {{passive:false}});

startBtn.addEventListener('click', async () => {{
  if (!gameRunning) {{
    gameRunning = true;
    if (menuAudio) {{ menuAudio.pause(); menuAudio.currentTime = 0; }}
    if (ingameAudio && musicEnabled) {{
      try {{ await ingameAudio.play(); }} catch(e){{ console.warn('ingame play blocked', e); }}
    }}
    menuOverlay.style.display = 'none';
    reset();
    last = performance.now();
    requestAnimationFrame(loop);
  }} else {{
    reset();
    gameOver = false;
    if (ingameAudio && musicEnabled) {{ ingameAudio.currentTime = 0; ingameAudio.play().catch(()=>{{}}); }}
    last = performance.now();
    requestAnimationFrame(loop);
  }}
}});

menuPlayBtn.addEventListener('click', () => {{
  if (menuAudio && musicEnabled) {{
    menuAudio.currentTime = 0;
    menuAudio.play().catch(()=>{{}});
  }}
}});

window.addEventListener('pagehide', () => {{
  if (menuAudio) menuAudio.pause();
  if (ingameAudio) ingameAudio.pause();
}});

try {{
  const best = parseInt(localStorage.getItem('flappy_best') || '0');
  if (!isNaN(best) && best > 0) {{
    const card = document.querySelector('#menuCard');
    const el = document.createElement('div');
    el.style.marginTop = '8px';
    el.style.fontSize = '14px';
    el.style.opacity = '0.9';
    el.innerText = 'Best: ' + best;
    card.appendChild(el);
  }}
}} catch(e){{ console.warn('storage err', e); }}

loadAssets().then(() => {{ render(); }}).catch(e => {{ console.warn('assets load', e); render(); }});

</script>
</body>
</html>
"""

# Render game
st.components.v1.html(game_html, height=760, scrolling=False)

st.markdown("""
**Instructions (simple):**
1. Use the **sidebar** to upload your background/player/obstacle images and menu/in-game music.  
2. On the page: first press **PLAY** (menu) to allow menu music (browser requires a gesture).  
3. Then press **START** to play — menu music will stop and in-game music will start.  
4. If you don't upload files, the app will try to use repo files with default names (change filenames at top of this script if your repo uses different names).
""")
