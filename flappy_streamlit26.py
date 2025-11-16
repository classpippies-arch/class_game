# flappy_streamlit26.py
import streamlit as st
import base64
import os
import glob

st.set_page_config(page_title="Premium Flappy Bird", layout="wide", page_icon="🐦")
st.markdown("""
<style>
/* minimal styling kept from previous premium look */
.main-header{font-size:2.4rem;font-weight:800;text-align:center}
.sidebar .sidebar-content {background: linear-gradient(180deg,#f8f9fa,#e9ecef);}
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="main-header">🎮 Premium Flappy Bird — Auto Asset Loader</div>', unsafe_allow_html=True)
st.write("The app will automatically load assets from `./assets/images/` and `./assets/sounds/` (repo). If not found, it will attempt repo-root fallbacks.")

# -------------------------
# CONFIG: asset directories & expected names
# -------------------------
ASSETS_IMG_DIR = os.path.join(".", "assets", "images")
ASSETS_SND_DIR = os.path.join(".", "assets", "sounds")

# expected image filenames (preferred)
EXPECTED_BG = "background_image.png"
EXPECTED_PLAYER = "player_character.png"
EXPECTED_PIPE = "obstacle_enemy.png"

# fallback filenames in repo root (common in your repo)
FALLBACK_BG = "background_image.png"
FALLBACK_PLAYER = "player_character.png"
FALLBACK_PIPE = "obstacle_enemy.png"

# utility: convert file path to data URL (or None)
def path_to_data_url(path):
    try:
        if not path or not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            raw = f.read()
        ext = path.lower().split(".")[-1]
        if ext in ("png", "svg"):
            mime = "image/png"
        elif ext in ("jpg", "jpeg"):
            mime = "image/jpeg"
        elif ext == "mp3":
            mime = "audio/mpeg"
        elif ext == "ogg":
            mime = "audio/ogg"
        elif ext == "wav":
            mime = "audio/wav"
        else:
            mime = "application/octet-stream"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    except Exception as e:
        st.warning(f"Failed to load asset `{path}`: {e}")
        return None

# helper: find file in assets dir with given name, or fallback to repo root
def find_asset_image(preferred_dir, filename, fallback):
    # check preferred dir
    if preferred_dir and os.path.isdir(preferred_dir):
        candidate = os.path.join(preferred_dir, filename)
        if os.path.exists(candidate):
            return candidate
    # check repo root fallback
    if os.path.exists(fallback):
        return fallback
    return None

# helper: collect mp3 files from assets dir (sorted)
def collect_sounds(preferred_dir):
    files = []
    if preferred_dir and os.path.isdir(preferred_dir):
        files = sorted(glob.glob(os.path.join(preferred_dir, "*.mp3")))
    # if none and repo root has mp3s, use them
    if not files:
        files = sorted(glob.glob("*.mp3"))
    return files

# --------------------------------------
# Resolve assets (auto)
# --------------------------------------
bg_path = find_asset_image(ASSETS_IMG_DIR, EXPECTED_BG, FALLBACK_BG)
player_path = find_asset_image(ASSETS_IMG_DIR, EXPECTED_PLAYER, FALLBACK_PLAYER)
pipe_path = find_asset_image(ASSETS_IMG_DIR, EXPECTED_PIPE, FALLBACK_PIPE)

sound_files = collect_sounds(ASSETS_SND_DIR)

# Choose menu / ingame / gameover music heuristically
menu_music_path = None
ingame_music_path = None
gameover_music_path = None
if sound_files:
    # try to pick names containing 'menu' 'ingame' 'gameover' else first ones
    lower_files = [os.path.basename(p).lower() for p in sound_files]
    for idx, name in enumerate(lower_files):
        if "menu" in name or "home" in name:
            menu_music_path = sound_files[idx]
            break
    for idx, name in enumerate(lower_files):
        if "game" in name and "over" not in name and "ingame" in name:
            ingame_music_path = sound_files[idx]
            break
    for idx, name in enumerate(lower_files):
        if "gameover" in name or "game-over" in name or "end" in name or "ending" in name:
            gameover_music_path = sound_files[idx]
            break
    # fallback assignments
    if not menu_music_path and len(sound_files) >= 1:
        menu_music_path = sound_files[0]
    if not ingame_music_path and len(sound_files) >= 2:
        ingame_music_path = sound_files[1]
    if not gameover_music_path and len(sound_files) >= 3:
        gameover_music_path = sound_files[2]

# Convert to data-urls
BG_URL = path_to_data_url(bg_path) or ""
PLAYER_URL = path_to_data_url(player_path) or ""
PIPE_URL = path_to_data_url(pipe_path) or ""
MENU_MUSIC_URL = path_to_data_url(menu_music_path) if menu_music_path else None
INGAME_MUSIC_URL = path_to_data_url(ingame_music_path) if ingame_music_path else None
GAMEOVER_MUSIC_URL = path_to_data_url(gameover_music_path) if gameover_music_path else None

# Show friendly messages for missing assets
missing = []
if not (BG_URL and PLAYER_URL and PIPE_URL):
    if not BG_URL:
        missing.append("background image")
    if not PLAYER_URL:
        missing.append("player image")
    if not PIPE_URL:
        missing.append("obstacle image")
    st.warning("Missing assets detected: " + ", ".join(missing) + ". The game will use fallback visuals (solid shapes).")
if not sound_files:
    st.info("No .mp3 files found in ./assets/sounds/ or repo root. No automatic music will play (use toggle to test).")
else:
    st.success(f"Found {len(sound_files)} sound file(s). Menu/In-game/Gameover music selected automatically.")

# Optional: let user override by upload (still optional; not required)
with st.sidebar:
    st.markdown("### Optional: override detected assets")
    up_bg = st.file_uploader("Background (optional)", type=["png","jpg","jpeg"], key="override_bg")
    up_player = st.file_uploader("Player (optional)", type=["png","jpg","jpeg"], key="override_player")
    up_pipe = st.file_uploader("Obstacle (optional)", type=["png","jpg","jpeg"], key="override_pipe")
    up_menu = st.file_uploader("Menu music (optional)", type=["mp3","ogg","wav"], key="override_menu")
    up_ingame = st.file_uploader("Ingame music (optional)", type=["mp3","ogg","wav"], key="override_ingame")
    up_gameover = st.file_uploader("Gameover music (optional)", type=["mp3","ogg","wav"], key="override_gameover")

# If overrides provided, use them (these are optional)
def uploaded_to_dataurl(uploaded, current):
    if uploaded is not None:
        raw = uploaded.read()
        name = uploaded.name.lower()
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
    return current

BG_URL = uploaded_to_dataurl(up_bg, BG_URL) or ""
PLAYER_URL = uploaded_to_dataurl(up_player, PLAYER_URL) or ""
PIPE_URL = uploaded_to_dataurl(up_pipe, PIPE_URL) or ""
MENU_MUSIC_URL = uploaded_to_dataurl(up_menu, MENU_MUSIC_URL) if (up_menu or MENU_MUSIC_URL) else None
INGAME_MUSIC_URL = uploaded_to_dataurl(up_ingame, INGAME_MUSIC_URL) if (up_ingame or INGAME_MUSIC_URL) else None
GAMEOVER_MUSIC_URL = uploaded_to_dataurl(up_gameover, GAMEOVER_MUSIC_URL) if (up_gameover or GAMEOVER_MUSIC_URL) else None

# -------------------------
# Build & render embedded HTML/JS (escape JS braces by doubling)
# -------------------------
# Basic game configuration values (tweakable)
GAME_SPEED = 3
GRAVITY = 0.6
JUMP_POWER = -11
PIPE_GAP = 160

game_html = f"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
body{{margin:0;background:#0b0b0b;color:#fff;font-family:sans-serif}}
#wrap{{width:95%;max-width:1000px;margin:10px auto;position:relative}}
canvas{{width:100%;height:70vh;background:#000;border-radius:10px;display:block}}
#startBtn{{position:absolute;top:12px;right:12px;z-index:999;background:#ff4757;color:#fff;border:none;padding:10px 14px;border-radius:10px;font-weight:700}}
#musicToggle{{position:absolute;top:12px;left:12px;z-index:999;background:#333;color:#fff;border:none;padding:8px 10px;border-radius:8px}}
#scoreText{{position:absolute;top:14px;left:50%;transform:translateX(-50%);z-index:999;font-size:28px;font-weight:700}}
.menuCard{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}}
.menuInner{{background:rgba(0,0,0,0.6);padding:20px;border-radius:12px;pointer-events:all;text-align:center}}
</style>
</head>
<body>
<div id="wrap">
  <div id="scoreText">Score: <span id="score">0</span></div>
  <button id="musicToggle">Music ON</button>
  <button id="startBtn">START</button>

  <div class="menuCard">
    <div class="menuInner">
      <h3>Welcome — Press PLAY to allow audio, then START</h3>
      <button id="menuPlayBtn">PLAY</button>
      <div id="bestText" style="margin-top:8px;color:#ddd;font-size:14px"></div>
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
const GAMEOVER_MUSIC_URL = {('"' + GAMEOVER_MUSIC_URL + '"') if GAMEOVER_MUSIC_URL else 'null'};

let menuAudio = null;
let ingameAudio = null;
let gameoverAudio = null;
let musicEnabled = true;

if (MENU_MUSIC_URL) {{
  menuAudio = new Audio(MENU_MUSIC_URL); menuAudio.loop = true; menuAudio.volume = 0.5;
}}
if (INGAME_MUSIC_URL) {{
  ingameAudio = new Audio(INGAME_MUSIC_URL); ingameAudio.loop = true; ingameAudio.volume = 0.5;
}}
if (GAMEOVER_MUSIC_URL) {{
  gameoverAudio = new Audio(GAMEOVER_MUSIC_URL); gameoverAudio.volume = 0.6;
}}

try {{
  const m = localStorage.getItem('flappy_music_enabled');
  if (m !== null) musicEnabled = m === '1';
  document.getElementById('musicToggle').innerText = musicEnabled ? 'Music ON' : 'Music OFF';
}} catch(e){{console.warn(e)}}

document.getElementById('musicToggle').addEventListener('click', () => {{
  musicEnabled = !musicEnabled;
  document.getElementById('musicToggle').innerText = musicEnabled ? 'Music ON' : 'Music OFF';
  try {{ localStorage.setItem('flappy_music_enabled', musicEnabled ? '1' : '0'); }} catch(e){{}}
  if (!musicEnabled) {{ if (menuAudio) menuAudio.pause(); if (ingameAudio) ingameAudio.pause(); if (gameoverAudio) gameoverAudio.pause(); }}
  else {{ if (!gameRunning && menuAudio) menuAudio.play().catch(()=>{{}}); if (gameRunning && ingameAudio) ingameAudio.play().catch(()=>{{}}); }}
}});

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function resize(){{ canvas.width = Math.min(window.innerWidth*0.95,1000); canvas.height = Math.min(window.innerHeight*0.72,700); }}
resize(); window.addEventListener('resize', resize);

let images = {{ bg:null, player:null, pipe:null }};
function loadImage(url){{ return new Promise((res,rej) => {{ let i=new Image(); i.onload = ()=>res(i); i.onerror = rej; i.src = url; }})); }}

async function loadAssets() {{
  try {{
    images.bg = BG_URL ? await loadImage(BG_URL) : null;
  }} catch(e){{ console.warn('bg load failed', e); images.bg = null; }}
  try {{
    images.player = PLAYER_URL ? await loadImage(PLAYER_URL) : null;
  }} catch(e){{ console.warn('player load failed', e); images.player = null; }}
  try {{
    images.pipe = PIPE_URL ? await loadImage(PIPE_URL) : null;
  }} catch(e){{ console.warn('pipe load failed', e); images.pipe = null; }}
}}

let gameRunning=false, gameOver=false, score=0;
let player={{x:100,y:200,vy:0,size:48}}, gravity={GRAVITY}, jump={JUMP_POWER}, pipes=[], pipeGap={PIPE_GAP}, pipeTimer=0, last=performance.now();

function reset(){{ score=0; player.y = canvas.height/2; player.vy = 0; pipes=[]; gameOver=false; document.getElementById('score').innerText = 0; }}
function spawnPipe(){{ const margin = Math.floor(canvas.height*0.12); const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap)+margin+pipeGap/2); pipes.push({{x:canvas.width+100,center,scored:false}}); }}

function update(dt){{ if(!gameRunning||gameOver) return; pipeTimer += dt; if(pipeTimer>1400){pipeTimer=0;spawnPipe();} for(let p of pipes) p.x -= {GAME_SPEED}*(dt/1000)*60*0.05; if(pipes.length&&pipes[0].x+120<0) pipes.shift(); player.vy += gravity*(dt/16); player.y += player.vy*(dt/16); for(let p of pipes){{ const w = Math.floor(canvas.width*0.09); const topH = p.center - (pipeGap/2); const bottomY = p.center + (pipeGap/2); if(!p.scored && p.x + w < player.x){ p.scored = true; score++; document.getElementById('score').innerText = score; } // collision (AABB)
 const rect = {{x:player.x,y:player.y,w:player.size,h:player.size}};
 const topRect = {{x:p.x,y:0,w:w,h:topH}};
 const botRect = {{x:p.x,y:bottomY,w:w,h:canvas.height-bottomY}};
 if(checkRectCollision(rect, topRect) || checkRectCollision(rect, botRect)){{ gameOver = true; }}
}} if(player.y + player.size > canvas.height) gameOver = true; }}

function checkRectCollision(r1,r2){{ return r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y; }}

function render(){{ ctx.clearRect(0,0,canvas.width,canvas.height); if(images.bg) ctx.drawImage(images.bg,0,0,canvas.width,canvas.height); else {{ ctx.fillStyle='#000'; ctx.fillRect(0,0,canvas.width,canvas.height); }} for(let p of pipes){{ const w = Math.floor(canvas.width*0.09); const topH = p.center - (pipeGap/2); if(images.pipe){{ ctx.drawImage(images.pipe,p.x,0,w,topH); ctx.drawImage(images.pipe,p.x,p.center+(pipeGap/2),w,canvas.height-(p.center+(pipeGap/2))); }} else {{ ctx.fillStyle='#217a4a'; ctx.fillRect(p.x,0,w,topH); ctx.fillRect(p.x,p.center+(pipeGap/2),w,canvas.height-(p.center+(pipeGap/2))); }} }} if(images.player) ctx.drawImage(images.player,player.x,player.y,player.size,player.size); else {{ ctx.fillStyle='#f1c40f'; ctx.fillRect(player.x,player.y,player.size,player.size); }} if(gameOver){{ ctx.fillStyle='rgba(0,0,0,0.5)'; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.fillStyle='#fff'; ctx.font='36px sans-serif'; ctx.textAlign='center'; ctx.fillText('GAME OVER - Score: ' + score, canvas.width/2, canvas.height/2); }} }}

function flap(){{ if(!gameRunning||gameOver) return; player.vy = jump; }}
window.addEventListener('keydown',(e)=>{{ if(e.code === 'Space') flap(); }});
canvas.addEventListener('mousedown',()=>{{ flap(); }});
canvas.addEventListener('touchstart',(e)=>{{ e.preventDefault(); flap(); }},{passive:false});

function loop(t){{ const dt = t - last; last = t; update(dt); render(); if(!gameOver) requestAnimationFrame(loop); else {{ if(ingameAudio) ingameAudio.pause(); try{{ const prev = parseInt(localStorage.getItem('flappy_best')||'0'); if(score>prev) localStorage.setItem('flappy_best',String(score)); }}catch(e){{}} }} }}

document.getElementById('menuPlayBtn').addEventListener('click', ()=>{{ if(menuAudio && musicEnabled) menuAudio.play().catch(()=>{{}}); }});
document.getElementById('startBtn').addEventListener('click', ()=>{{ if(!gameRunning){{ gameRunning = true; if(menuAudio) menuAudio.pause(); if(ingameAudio && musicEnabled) ingameAudio.play().catch(()=>{{}}); reset(); last = performance.now(); requestAnimationFrame(loop); }} else {{ reset(); gameOver = false; if(ingameAudio && musicEnabled){ ingameAudio.currentTime = 0; ingameAudio.play().catch(()=>{{}}); } last = performance.now(); requestAnimationFrame(loop); }} }});

loadAssets().then(()=>{{ // show best score
 try{{ const b = parseInt(localStorage.getItem('flappy_best')||'0'); if(b>0) document.getElementById('bestText').innerText = 'Best: ' + b; }}catch(e){{}}
 render();
}}).catch(e=>{{ console.warn(e); render(); }});

</script>
</body>
</html>
"""

# Render
st.components.v1.html(game_html, height=800, scrolling=False)

# final instructions
st.markdown("---")
st.markdown("**How it loads assets now:**")
st.markdown("""
- Auto searches `./assets/images/` for `background_image.png`, `player_character.png`, `obstacle_enemy.png` (preferred).
- If not found it will try repo root filenames.
- Auto collects `.mp3` files from `./assets/sounds/` (or repo root) and selects menu/in-game/gameover tracks heuristically.
- You can optionally override assets from the sidebar (but it's not required).
- If required images are missing, the game uses clean shape fallbacks and shows a warning message (no crash).
""")
