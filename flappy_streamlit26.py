import streamlit as st
import base64
import os

st.set_page_config(page_title="Flappy Bird Game", layout="wide")
st.title("Flappy Bird – Streamlit Edition")
st.write("Tap/Click/Space to jump. Menu music and in-game music handled separately. Mobile + PC friendly.")

# ----- Configure these filenames to match your repo exactly -----
# If filenames differ, change them here (case-sensitive)
MENU_MUSIC_FILE = "Home Screen Music (Only on Menu Screen).mp3"  # <--- exact file in your repo
INGAME_MUSIC_FILE = "ingame_music_1.mp3"  # or ingame_music_2.mp3, etc.

PLAYER_FILE = "player_character.png"
PIPE_FILE = "obstacle_enemy.png"
BG_FILE = "background_image.png"

# ----- helper to turn repo file into data URL (or None if missing) -----
def file_to_data_url_if_exists(filepath):
    if not os.path.exists(filepath):
        return None
    b = open(filepath, "rb").read()
    # detect type
    ext = filepath.lower().split(".")[-1]
    if ext in ("png", "jpg", "jpeg", "svg"):
        mime = "image/png" if ext == "png" or ext == "svg" else "image/jpeg"
    elif ext in ("mp3",):
        mime = "audio/mpeg"
    elif ext in ("ogg",):
        mime = "audio/ogg"
    elif ext in ("wav",):
        mime = "audio/wav"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode()

# build urls (None if file not present)
PLAYER_URL = file_to_data_url_if_exists(PLAYER_FILE) or ""
PIPE_URL = file_to_data_url_if_exists(PIPE_FILE) or ""
BG_URL = file_to_data_url_if_exists(BG_FILE) or ""
MENU_MUSIC_URL = file_to_data_url_if_exists(MENU_MUSIC_FILE)
INGAME_MUSIC_URL = file_to_data_url_if_exists(INGAME_MUSIC_FILE)

# ----- If music missing, JS will hide music controls gracefully -----

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
  #menuCard {{ background: rgba(0,0,0,0.6); padding:24px 28px; border-radius:12px; text-align:center; pointer-events:all; }}
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
      <h2>Welcome — Flappy Streamlit</h2>
      <p>Menu music will play here. Press PLAY to start the game.</p>
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

// Audio elements
let menuAudio = null;
let ingameAudio = null;
let musicEnabled = true;

// create audio if present
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

// menu overlay controls
const menuOverlay = document.getElementById('menuOverlay');
const menuPlayBtn = document.getElementById('menuPlayBtn');
const startBtn = document.getElementById('startBtn');
const musicToggle = document.getElementById('musicToggle');
const scoreSpan = document.getElementById('score');

// toggle music on/off
musicToggle.addEventListener('click', () => {{
  musicEnabled = !musicEnabled;
  musicToggle.innerText = musicEnabled ? 'Music ON' : 'Music OFF';
  if (!musicEnabled) {{
    if (menuAudio) menuAudio.pause();
    if (ingameAudio) ingameAudio.pause();
  }} else {{
    // resume appropriate track depending on state
    if (!gameRunning && menuAudio) menuAudio.play().catch(()=>{{}});
    if (gameRunning && ingameAudio) ingameAudio.play().catch(()=>{{}});
  }}
}});

// Play only after user gesture — browsers block autoplay otherwise
menuPlayBtn.addEventListener('click', () => {{
  // start playing menu music (if available)
  if (menuAudio && musicEnabled) {{
    menuAudio.currentTime = 0;
    menuAudio.play().catch(()=>{{}});
  }}
  // remove overlay pointer-events to allow start press etc.
  // We keep overlay visible until START is pressed to show menu
}});

// Game canvas + engine (simplified)
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

function resize(){ canvas.width = Math.min(window.innerWidth*0.95, 1000); canvas.height = Math.min(window.innerHeight*0.72, 700); }
resize(); window.addEventListener('resize', resize);

// assets
let images = {{ bg: null, player: null, pipe: null }};
function loadImage(url){ return new Promise((res,reject)=>{{ let i=new Image(); i.onload = ()=>res(i); i.onerror = reject; i.src = url; }});}

let gameRunning = false;
let gameOver = false;
let score = 0;
let player = {{ x: 100, y: 200, vy:0, size:48 }};
let gravity = 0.6;
let jump = -11;
let pipes = [];
let pipeGap = Math.floor(canvas.height * 0.28);
let pipeTimer = 0;

// load images (if URLs empty, create simple placeholders)
async function loadAssets(){{
  try {{
    images.bg = BG_URL ? await loadImage(BG_URL) : null;
    images.player = PLAYER_URL ? await loadImage(PLAYER_URL) : null;
    images.pipe = PIPE_URL ? await loadImage(PIPE_URL) : null;
  }} catch(e) {{
    console.warn('asset load failed', e);
  }}
}}

function reset(){{
  score = 0; player.y = canvas.height/2; player.vy = 0; pipes = []; gameOver = false;
  document.getElementById('score').innerText = score;
}}

function spawnPipe(){{
  const margin = Math.floor(canvas.height*0.12);
  const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap) + margin + pipeGap/2);
  pipes.push({{ x: canvas.width + 100, center, scored:false }});
}}

function update(dt){{
  if (!gameRunning || gameOver) return;
  pipeTimer += dt;
  if (pipeTimer > 1400) {{ pipeTimer = 0; spawnPipe(); }}
  // move pipes
  for (let p of pipes) p.x -= 3 * (dt/16);
  if (pipes.length && pipes[0].x + 120 < 0) pipes.shift();
  player.vy += gravity * (dt/16);
  player.y += player.vy * (dt/16);
  // collisions & scoring
  for (let p of pipes) {{
    const w = Math.floor(canvas.width * 0.09);
    const topH = p.center - (pipeGap/2);
    const bottomY = p.center + (pipeGap/2);
    if (!p.scored && p.x + w < player.x) {{ p.scored = true; score++; document.getElementById('score').innerText = score; }}
    // simple AABB circle approx
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

function render(){{
  // background
  if (images.bg) ctx.drawImage(images.bg, 0, 0, canvas.width, canvas.height);
  else {{ ctx.fillStyle = '#000'; ctx.fillRect(0,0,canvas.width,canvas.height); }}
  // pipes
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
  // player
  if (images.player) ctx.drawImage(images.player, player.x, player.y, player.size, player.size);
  else {{
    ctx.fillStyle = '#f1c40f'; ctx.fillRect(player.x, player.y, player.size, player.size);
  }}
  // score is shown by outer HTML element; no need to draw here
}}

let last = performance.now();
function loop(t){{
  const dt = t - last;
  last = t;
  update(dt);
  render();
  if (!gameOver) requestAnimationFrame(loop);
  else {{
    // stop in-game music & show gameover on canvas
    if (ingameAudio) ingameAudio.pause();
    ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff'; ctx.font = '36px sans-serif'; ctx.textAlign='center';
    ctx.fillText('GAME OVER - Score: ' + score, canvas.width/2, canvas.height/2);
  }}
}}

// controls
function flap(){ if (!gameRunning || gameOver) return; player.vy = jump; }
window.addEventListener('keydown', (e) => {{ if (e.code === 'Space') flap(); }});
canvas.addEventListener('mousedown', (e) => {{ if (!gameRunning) return; flap(); }});
canvas.addEventListener('touchstart', (e) => {{ e.preventDefault(); if (!gameRunning) return; flap(); }}, {{passive:false}});

// start button behavior:
// - if currently in menu state: pressing START will begin game,
//   stop menu audio, start ingame audio (if present)
startBtn.addEventListener('click', async () => {{
  // ensure user gesture allows audio
  if (!gameRunning) {{
    gameRunning = true;
    // stop menu music, start ingame music
    if (menuAudio) {{ menuAudio.pause(); menuAudio.currentTime = 0; }}
    if (ingameAudio && musicEnabled) {{
      try {{ await ingameAudio.play(); }} catch(e){{ console.warn('ingame play blocked', e); }}
    }}
    // hide menu overlay
    menuOverlay.style.display = 'none';
    reset();
    last = performance.now();
    requestAnimationFrame(loop);
  }} else {{
    // restart while running/after gameover
    reset();
    gameOver = false;
    if (ingameAudio && musicEnabled) {{ ingameAudio.currentTime = 0; ingameAudio.play().catch(()=>{{}}); }}
    last = performance.now();
    requestAnimationFrame(loop);
  }}
}});

// when user clicks PLAY on menu card, start menu music (gesture)
menuPlayBtn.addEventListener('click', () => {{
  if (menuAudio && musicEnabled) {{
    menuAudio.currentTime = 0;
    menuAudio.play().catch(()=>{{}});
  }}
}});

// ensure pause/cleanup if user navigates away
window.addEventListener('pagehide', () => {{
  if (menuAudio) menuAudio.pause();
  if (ingameAudio) ingameAudio.pause();
}});

// initial load: load images then render an intro screen
loadAssets().then(() => {{
  render();
  // show overlay; menuAudio will start only after user clicks Play (menuPlayBtn)
}}).catch(e => {{ console.warn('assets load err', e); render(); }});

</script>
</body>
</html>
"""

st.components.v1.html(game_html, height=760, scrolling=False)

st.markdown("""
**Notes (simple):**
- On the menu, press **PLAY** to allow the menu music to play (browser requires a gesture).
- Then press **START** to begin playing the game — menu music will stop and in-game music starts.
- If music filenames in repo are different, update `MENU_MUSIC_FILE` and `INGAME_MUSIC_FILE` variables at top of this script.
""")

