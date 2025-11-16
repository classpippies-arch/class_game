# flappy_streamlit26.py
import streamlit as st
import base64
import os

st.set_page_config(page_title="Easy Flappy Bird", layout="wide")
st.title("🎮 Easy Flappy Bird - Customize Your Game!")
st.write("Aap apni pasand ka background, character, obstacles aur music set kar sakte hain!")

# --------- Left side: Easy Uploaders ---------
with st.sidebar:
    st.header("🎨 Game Customization")
    
    st.subheader("🖼️ Images")
    up_bg = st.file_uploader("Background Image", type=["png","jpg","jpeg"], key="bg")
    up_player = st.file_uploader("Player Character", type=["png","jpg","jpeg"], key="player")
    up_pipe = st.file_uploader("Obstacles", type=["png","jpg","jpeg"], key="pipe")
    
    st.markdown("---")
    st.subheader("🎵 Music")
    up_menu_music = st.file_uploader("Menu Music", type=["mp3","ogg","wav"], key="menu_music")
    up_ingame_music = st.file_uploader("Game Music", type=["mp3","ogg","wav"], key="ingame_music")
    
    st.markdown("---")
    st.subheader("⚙️ Game Settings")
    game_speed = st.slider("Game Speed", 1, 10, 3)
    gravity_strength = st.slider("Gravity", 0.1, 1.0, 0.5)
    jump_power = st.slider("Jump Power", 5, 20, 12)
    
    st.markdown("---")
    st.success("✅ Upload karne ke baad game automatically update ho jayega!")

# --------- Helper: convert uploaded file or repo file to data URL ---------
def fileobj_to_data_url(fileobj, default_path=None):
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

# repo fallback names
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

# --------- Generate embedded HTML + JS ---------
game_html = f"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ 
    margin:0; 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color:#fff; 
    font-family:'Arial', sans-serif; 
  }}
  #canvasWrap {{ 
    width:95%; 
    max-width:900px; 
    margin: 10px auto; 
    position:relative; 
    background: rgba(255,255,255,0.1);
    border-radius:15px;
    padding:10px;
    backdrop-filter: blur(10px);
  }}
  canvas {{ 
    width:100%; 
    height:65vh; 
    background:#000; 
    border-radius:10px; 
    display:block; 
    border: 3px solid #fff;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  }}
  #startBtn {{ 
    position:absolute; 
    top:15px; 
    right:15px; 
    z-index:999; 
    background:#ff6b6b; 
    color:#fff; 
    border:none; 
    padding:12px 20px; 
    border-radius:10px; 
    font-weight:700;
    font-size:16px;
    cursor:pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(255,107,107,0.4);
  }}
  #startBtn:hover {{ background:#ff5252; transform: scale(1.05); }}
  
  #musicToggle {{ 
    position:absolute; 
    top:15px; 
    left:15px; 
    z-index:999; 
    background:#4ecdc4; 
    color:#fff; 
    border:none; 
    padding:10px 15px; 
    border-radius:8px; 
    cursor:pointer;
    font-weight:600;
    transition: all 0.3s ease;
  }}
  #musicToggle:hover {{ background:#45b7af; }}
  
  #menuOverlay {{ 
    position:absolute; 
    inset:0; 
    display:flex; 
    align-items:center; 
    justify-content:center; 
    z-index:500; 
    pointer-events:none; 
    background: rgba(0,0,0,0.7);
    border-radius:10px;
  }}
  #menuCard {{ 
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding:25px 30px; 
    border-radius:15px; 
    text-align:center; 
    pointer-events:all;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    border: 2px solid rgba(255,255,255,0.2);
  }}
  #menuCard h3 {{ 
    margin:0 0 15px 0; 
    font-size:24px; 
    color:#fff;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  }}
  #menuCard p {{ 
    margin:0 0 20px 0; 
    font-size:14px; 
    opacity:0.9;
    line-height:1.5;
  }}
  #menuCard button {{ 
    margin-top:5px; 
    padding:12px 25px; 
    font-weight:700; 
    border-radius:10px; 
    border:none; 
    background:#ffd93d; 
    color:#333;
    font-size:16px;
    cursor:pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(255,217,61,0.4);
  }}
  #menuCard button:hover {{ 
    background:#ffcd00; 
    transform: scale(1.05);
  }}
  #scoreText {{ 
    position:absolute; 
    top:15px; 
    left:50%; 
    transform:translateX(-50%); 
    z-index:999; 
    font-size:32px; 
    font-weight:900;
    color:#ffd93d;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
  }}
  #controlsInfo {{
    position:absolute;
    bottom:15px;
    left:50%;
    transform:translateX(-50%);
    z-index:999;
    background:rgba(0,0,0,0.7);
    padding:8px 15px;
    border-radius:20px;
    font-size:14px;
    color:#ffd93d;
  }}
  .easy-mode {{ 
    position:absolute;
    top:70px;
    left:15px;
    z-index:999;
    background:rgba(46, 204, 113, 0.9);
    color:white;
    padding:5px 10px;
    border-radius:15px;
    font-size:12px;
    font-weight:bold;
  }}
</style>
</head>
<body>
<div id="canvasWrap">
  <div class="easy-mode">✨ EASY MODE ✨</div>
  <div id="scoreText">Score: <span id="score">0</span></div>
  <button id="musicToggle">🔊 Music ON</button>
  <button id="startBtn">🎮 START GAME</button>
  <div id="controlsInfo">🔼 SPACE / CLICK / TOUCH to JUMP</div>

  <div id="menuOverlay">
    <div id="menuCard">
      <h3>🚀 Welcome to Easy Flappy Bird!</h3>
      <p>Upload your favorite images and music from the sidebar!<br>
      Game automatically becomes easier with your settings!</p>
      <button id="menuPlayBtn">🎵 PLAY MUSIC</button>
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

// Game settings from Streamlit
const GAME_SPEED = {game_speed};
const GRAVITY = {gravity_strength};
const JUMP_POWER = -{jump_power};

let menuAudio = null;
let ingameAudio = null;
let musicEnabled = true;

if (MENU_MUSIC_URL) {{
  menuAudio = new Audio(MENU_MUSIC_URL);
  menuAudio.loop = true;
  menuAudio.volume = 0.4;
}}
if (INGAME_MUSIC_URL) {{
  ingameAudio = new Audio(INGAME_MUSIC_URL);
  ingameAudio.loop = true;
  ingameAudio.volume = 0.4;
}}

const menuOverlay = document.getElementById('menuOverlay');
const menuPlayBtn = document.getElementById('menuPlayBtn');
const startBtn = document.getElementById('startBtn');
const musicToggle = document.getElementById('musicToggle');
const scoreSpan = document.getElementById('score');

// Auto music on page load
try {{
  const m = localStorage.getItem('flappy_music_enabled');
  if (m !== null) musicEnabled = m === '1';
  musicToggle.innerText = musicEnabled ? '🔊 Music ON' : '🔇 Music OFF';
  
  // Auto start music
  if (musicEnabled && menuAudio) {{
    setTimeout(() => {{
      menuAudio.play().catch(e => console.log('Auto-play prevented'));
    }}, 1000);
  }}
}} catch(e){{ console.warn('storage err', e); }}

musicToggle.addEventListener('click', () => {{
  musicEnabled = !musicEnabled;
  musicToggle.innerText = musicEnabled ? '🔊 Music ON' : '🔇 Music OFF';
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

function resize(){{ 
  canvas.width = Math.min(window.innerWidth*0.95, 900); 
  canvas.height = Math.min(window.innerHeight*0.65, 600); 
}}
resize(); 
window.addEventListener('resize', resize);

let images = {{ bg: null, player: null, pipe: null }};
function loadImage(url){{ return new Promise((res,rej) => {{ let i=new Image(); i.onload = ()=>res(i); i.onerror = rej; i.src = url; }}); }}

let gameRunning = false;
let gameOver = false;
let score = 0;
let player = {{ x: 100, y: 200, vy:0, size:50 }};
let pipes = [];
let pipeGap = 180; // Wider gap for easier gameplay
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
  const margin = Math.floor(canvas.height*0.15); // More margin
  const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap) + margin + pipeGap/2);
  pipes.push({{ x: canvas.width + 100, center, scored:false }});
}}

function update(dt) {{
  if (!gameRunning || gameOver) return;
  pipeTimer += dt;
  if (pipeTimer > 1800) {{ pipeTimer = 0; spawnPipe(); }} // Slower pipe spawn
  for (let p of pipes) p.x -= (GAME_SPEED * 0.8) * (dt/16); // Adjustable speed
  if (pipes.length && pipes[0].x + 120 < 0) pipes.shift();
  player.vy += GRAVITY * (dt/16);
  player.y += player.vy * (dt/16);
  for (let p of pipes) {{
    const w = Math.floor(canvas.width * 0.08); // Narrower pipes
    const topH = p.center - (pipeGap/2);
    const bottomY = p.center + (pipeGap/2);
    if (!p.scored && p.x + w < player.x) {{ p.scored = true; score++; scoreSpan.innerText = score; }}
    // Easier collision detection
    const playerRect = {{ x: player.x, y: player.y, width: player.size, height: player.size }};
    const topPipe = {{ x: p.x, y: 0, width: w, height: topH }};
    const bottomPipe = {{ x: p.x, y: bottomY, width: w, height: canvas.height - bottomY }};
    
    if (checkCollision(playerRect, topPipe) || checkCollision(playerRect, bottomPipe)) {{
      gameOver = true;
    }}
  }}
  // Ground collision with buffer
  if (player.y + player.size > canvas.height - 10) gameOver = true;
  // Ceiling collision removed for easier gameplay
  if (player.y < 0) player.y = 0;
}}

function checkCollision(rect1, rect2) {{
  return rect1.x < rect2.x + rect2.width &&
         rect1.x + rect1.width > rect2.x &&
         rect1.y < rect2.y + rect2.height &&
         rect1.y + rect1.height > rect2.y;
}}

function render() {{
  if (images.bg) {{
    ctx.drawImage(images.bg, 0, 0, canvas.width, canvas.height);
  }} else {{
    // Default gradient background
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#1e3c72');
    gradient.addColorStop(1, '#2a5298');
    ctx.fillStyle = gradient;
    ctx.fillRect(0,0,canvas.width,canvas.height);
  }}
  
  for (let p of pipes) {{
    const w = Math.floor(canvas.width * 0.08);
    const topH = p.center - (pipeGap/2);
    if (images.pipe) {{
      ctx.drawImage(images.pipe, p.x, 0, w, topH);
      ctx.drawImage(images.pipe, p.x, p.center + (pipeGap/2), w, canvas.height - (p.center + (pipeGap/2)));
    }} else {{
      // Default pipe with gradient
      const pipeGradient = ctx.createLinearGradient(p.x, 0, p.x + w, 0);
      pipeGradient.addColorStop(0, '#2ecc71');
      pipeGradient.addColorStop(1, '#27ae60');
      ctx.fillStyle = pipeGradient;
      ctx.fillRect(p.x, 0, w, topH);
      ctx.fillRect(p.x, p.center + (pipeGap/2), w, canvas.height - (p.center + (pipeGap/2)));
    }}
  }}
  
  if (images.player) {{
    ctx.drawImage(images.player, player.x, player.y, player.size, player.size);
  }} else {{
    // Default player with glow effect
    ctx.shadowColor = '#f1c40f';
    ctx.shadowBlur = 15;
    ctx.fillStyle = '#f1c40f';
    ctx.fillRect(player.x, player.y, player.size, player.size);
    ctx.shadowBlur = 0;
  }}
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
    
    // Game over screen with restart option
    ctx.fillStyle = 'rgba(0,0,0,0.8)'; 
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#ff6b6b'; 
    ctx.font = 'bold 36px Arial'; 
    ctx.textAlign='center';
    ctx.fillText('GAME OVER', canvas.width/2, canvas.height/2 - 40);
    ctx.fillStyle = '#ffd93d'; 
    ctx.font = '28px Arial';
    ctx.fillText('Score: ' + score, canvas.width/2, canvas.height/2);
    ctx.fillStyle = '#4ecdc4'; 
    ctx.font = '20px Arial';
    ctx.fillText('Click START to play again', canvas.width/2, canvas.height/2 + 50);
  }}
}}

function flap() {{ 
  if (!gameRunning || gameOver) return; 
  player.vy = JUMP_POWER; 
}}

// Multiple control options
window.addEventListener('keydown', (e) => {{ 
  if (e.code === 'Space' || e.key === 'ArrowUp' || e.key === 'w') flap(); 
}});
canvas.addEventListener('mousedown', flap);
canvas.addEventListener('touchstart', (e) => {{ e.preventDefault(); flap(); }}, {{passive:false}});

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

// Show best score
try {{
  const best = parseInt(localStorage.getItem('flappy_best') || '0');
  if (!isNaN(best) && best > 0) {{
    const card = document.querySelector('#menuCard');
    const el = document.createElement('div');
    el.style.marginTop = '15px';
    el.style.fontSize = '16px';
    el.style.color = '#ffd93d';
    el.style.fontWeight = 'bold';
    el.innerText = '🏆 Best Score: ' + best;
    card.appendChild(el);
  }}
}} catch(e){{ console.warn('storage err', e); }}

loadAssets().then(() => {{ render(); }}).catch(e => {{ console.warn('assets load', e); render(); }});

</script>
</body>
</html>
"""

# Render game
st.components.v1.html(game_html, height=700, scrolling=False)

# Instructions
st.markdown("""
## 🎯 Easy Game Features:

### ✨ **Auto Easy Mode:**
- **Wider gaps** between obstacles
- **Slower game speed** by default  
- **Multiple controls**: Space, Arrow Up, Click, or Touch
- **No ceiling death** - bounce safely at top

### 🎨 **Customization:**
1. **Upload images** from sidebar - game automatically updates!
2. **Choose your music** - menu and game music
3. **Adjust settings**: Game speed, gravity, jump power

### 🎮 **How to Play:**
- Press **START GAME** to begin
- Use **SPACE, CLICK, or TOUCH** to make bird jump
- Avoid obstacles and score points!
- Music plays automatically

### 💡 **Pro Tip:** 
Set **low gravity** and **high jump power** for super easy gameplay!
""")

# Add some fun emojis
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🎵 Your Music**")
with col2:
    st.markdown("**🖼️ Your Images**")  
with col3:
    st.markdown("**⚡ Your Settings**")
