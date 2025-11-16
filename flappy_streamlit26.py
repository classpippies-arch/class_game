# flappy_streamlit.py
import streamlit as st
import os, base64, glob

# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="Flappy (Streamlit only)", layout="wide", page_icon="🐦")
st.title("Flappy Bird — Streamlit (Auto assets)")
st.write("This app auto-loads assets from ./assets/images and ./assets/sounds (or repo root). No required uploads.")

# ------------------ HELPERS: asset discovery & data-URLs ------------------
ASSETS_IMG_DIR = os.path.join(".", "assets", "images")
ASSETS_SND_DIR = os.path.join(".", "assets", "sounds")

# expected names
EXPECTED_BG = "background_image.png"
EXPECTED_PLAYER = "player_character.png"
EXPECTED_PIPE = "obstacle_enemy.png"

def path_exists(p):
    return p and os.path.exists(p)

def find_image(filename):
    # preferred inside assets/images
    candidate = os.path.join(ASSETS_IMG_DIR, filename)
    if os.path.exists(candidate):
        return candidate
    # fallback to repo root
    if os.path.exists(filename):
        return filename
    return None

def collect_mp3s():
    files = []
    if os.path.isdir(ASSETS_SND_DIR):
        files = sorted(glob.glob(os.path.join(ASSETS_SND_DIR, "*.mp3")))
    if not files:
        files = sorted(glob.glob("*.mp3"))
    return files

def to_data_url(path):
    """Read file and return data:<mime>;base64,.... or None"""
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
    else:
        mime = "application/octet-stream"
    return "data:{};base64,{}".format(mime, base64.b64encode(raw).decode())

# ------------------ Resolve assets ------------------
bg_path = find_image(EXPECTED_BG)
player_path = find_image(EXPECTED_PLAYER)
pipe_path = find_image(EXPECTED_PIPE)
sound_list = collect_mp3s()

# heuristics for menu/ingame/gameover picks
menu_path = ingame_path = gameover_path = None
if sound_list:
    lower = [os.path.basename(p).lower() for p in sound_list]
    # pick by keyword
    for i, n in enumerate(lower):
        if "menu" in n or "home" in n:
            menu_path = sound_list[i]; break
    for i, n in enumerate(lower):
        if "ingame" in n or "game" in n and "over" not in n:
            ingame_path = sound_list[i]; break
    for i, n in enumerate(lower):
        if "over" in n or "gameover" in n or "ending" in n or "end" in n:
            gameover_path = sound_list[i]; break
    # fallbacks
    if not menu_path and len(sound_list) >= 1: menu_path = sound_list[0]
    if not ingame_path and len(sound_list) >= 2: ingame_path = sound_list[1]
    if not gameover_path and len(sound_list) >= 3: gameover_path = sound_list[2]

BG_URL = to_data_url(bg_path) or ""
PLAYER_URL = to_data_url(player_path) or ""
PIPE_URL = to_data_url(pipe_path) or ""
MENU_MUSIC_URL = to_data_url(menu_path) if menu_path else None
INGAME_MUSIC_URL = to_data_url(ingame_path) if ingame_path else None
GAMEOVER_MUSIC_URL = to_data_url(gameover_path) if gameover_path else None

# warnings / info to user (clear)
missing = []
if not BG_URL: missing.append("background image")
if not PLAYER_URL: missing.append("player image")
if not PIPE_URL: missing.append("obstacle image")
if missing:
    st.warning("Missing assets: {}. The game will use safe visual fallbacks (shapes).".format(", ".join(missing)))
if not sound_list:
    st.info("No .mp3 found in ./assets/sounds or repo root. Music will be off unless you upload or add mp3s to repo.")
else:
    st.success("Found {} sound file(s). Selected menu/ingame/gameover tracks automatically.".format(len(sound_list)))

# Optional: sidebar override (still optional)
with st.sidebar:
    st.header("Optional overrides")
    override_bg = st.file_uploader("Background (optional)", type=["png","jpg","jpeg"], key="ovbg")
    override_player = st.file_uploader("Player (optional)", type=["png","jpg","jpeg"], key="ovplayer")
    override_pipe = st.file_uploader("Pipe (optional)", type=["png","jpg","jpeg"], key="ovpipe")
    override_menu = st.file_uploader("Menu music (optional)", type=["mp3","wav","ogg"], key="ovmenu")
    override_ingame = st.file_uploader("Ingame music (optional)", type=["mp3","wav","ogg"], key="ovingame")
    st.markdown("---")
    st.caption("Uploads override repo assets for this session only (not required).")

def uploaded_to_dataurl(uploaded, current):
    if uploaded is None:
        return current
    raw = uploaded.read()
    name = uploaded.name.lower()
    if name.endswith(".mp3"): mime = "audio/mpeg"
    elif name.endswith(".ogg"): mime = "audio/ogg"
    elif name.endswith(".wav"): mime = "audio/wav"
    elif name.endswith(".jpg") or name.endswith(".jpeg"): mime = "image/jpeg"
    else: mime = "image/png"
    return "data:{};base64,{}".format(mime, base64.b64encode(raw).decode())

if override_bg: BG_URL = uploaded_to_dataurl(override_bg, BG_URL)
if override_player: PLAYER_URL = uploaded_to_dataurl(override_player, PLAYER_URL)
if override_pipe: PIPE_URL = uploaded_to_dataurl(override_pipe, PIPE_URL)
if override_menu: MENU_MUSIC_URL = uploaded_to_dataurl(override_menu, MENU_MUSIC_URL)
if override_ingame: INGAME_MUSIC_URL = uploaded_to_dataurl(override_ingame, INGAME_MUSIC_URL)

# ------------------ JS/HTML template (no f-string; safe placeholders) ------------------
GAME_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
body{margin:0;background:#0b0b0b;color:#fff;font-family:sans-serif}
#wrap{width:95%;max-width:1000px;margin:10px auto;position:relative}
canvas{width:100%;height:70vh;background:#000;border-radius:10px;display:block}
#startBtn{position:absolute;top:12px;right:12px;z-index:999;background:#ff4757;color:#fff;border:none;padding:10px 14px;border-radius:10px;font-weight:700}
#musicToggle{position:absolute;top:12px;left:12px;z-index:999;background:#333;color:#fff;border:none;padding:8px 10px;border-radius:8px}
#scoreText{position:absolute;top:14px;left:50%;transform:translateX(-50%);z-index:999;font-size:28px;font-weight:700}
.menuCard{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}
.menuInner{background:rgba(0,0,0,0.6);padding:20px;border-radius:12px;pointer-events:all;text-align:center}
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
const PLAYER_URL = "__PLAYER_URL__";
const PIPE_URL = "__PIPE_URL__";
const BG_URL = "__BG_URL__";
const MENU_MUSIC_URL = __MENU_MUSIC_URL__;
const INGAME_MUSIC_URL = __INGAME_MUSIC_URL__;
const GAMEOVER_MUSIC_URL = __GAMEOVER_MUSIC_URL__;

let menuAudio = null;
let ingameAudio = null;
let gameoverAudio = null;
let musicEnabled = true;

if (MENU_MUSIC_URL) { menuAudio = new Audio(MENU_MUSIC_URL); menuAudio.loop = true; menuAudio.volume = 0.5; }
if (INGAME_MUSIC_URL) { ingameAudio = new Audio(INGAME_MUSIC_URL); ingameAudio.loop = true; ingameAudio.volume = 0.5; }
if (GAMEOVER_MUSIC_URL) { gameoverAudio = new Audio(GAMEOVER_MUSIC_URL); gameoverAudio.volume = 0.6; }

try {
  const m = localStorage.getItem('flappy_music_enabled');
  if (m !== null) musicEnabled = m === '1';
  document.getElementById('musicToggle').innerText = musicEnabled ? 'Music ON' : 'Music OFF';
} catch(e) { console.warn(e); }

document.getElementById('musicToggle').addEventListener('click', () => {
  musicEnabled = !musicEnabled;
  document.getElementById('musicToggle').innerText = musicEnabled ? 'Music ON' : 'Music OFF';
  try { localStorage.setItem('flappy_music_enabled', musicEnabled ? '1' : '0'); } catch(e) {}
  if (!musicEnabled) { if (menuAudio) menuAudio.pause(); if (ingameAudio) ingameAudio.pause(); if (gameoverAudio) gameoverAudio.pause(); }
  else { if (!gameRunning && menuAudio) menuAudio.play().catch(()=>{}); if (gameRunning && ingameAudio) ingameAudio.play().catch(()=>{}); }
});

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function resize(){ canvas.width = Math.min(window.innerWidth*0.95,1000); canvas.height = Math.min(window.innerHeight*0.72,700); }
resize(); window.addEventListener('resize', resize);

let images = { bg:null, player:null, pipe:null };
function loadImage(url){ return new Promise((res,rej)=>{ let i=new Image(); i.onload = ()=>res(i); i.onerror = rej; i.src = url; }); }

async function loadAssets() {
  try { images.bg = BG_URL ? await loadImage(BG_URL) : null; } catch(e){ console.warn('bg load failed',e); images.bg=null; }
  try { images.player = PLAYER_URL ? await loadImage(PLAYER_URL) : null; } catch(e){ console.warn('player load failed',e); images.player=null; }
  try { images.pipe = PIPE_URL ? await loadImage(PIPE_URL) : null; } catch(e){ console.warn('pipe load failed',e); images.pipe=null; }
}

let gameRunning=false, gameOver=false, score=0;
let player={x:100,y:200,vy:0,size:48}, gravity=0.6, jump=-11, pipes=[], pipeGap=160, pipeTimer=0, last=performance.now();

function reset(){ score=0; player.y = canvas.height/2; player.vy = 0; pipes = []; gameOver=false; document.getElementById('score').innerText = 0; }
function spawnPipe(){ const margin = Math.floor(canvas.height*0.12); const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap)+margin+pipeGap/2); pipes.push({x:canvas.width+100,center,scored:false}); }

function update(dt){
  if(!gameRunning||gameOver) return;
  pipeTimer += dt;
  if(pipeTimer>1400){ pipeTimer = 0; spawnPipe(); }
  for(let p of pipes) p.x -= 2.5 * (dt/16);
  if(pipes.length && pipes[0].x + 120 < 0) pipes.shift();
  player.vy += gravity * (dt/16);
  player.y += player.vy * (dt/16);

  for(let p of pipes){
    const w = Math.floor(canvas.width * 0.09);
    const topH = p.center - (pipeGap/2);
    const bottomY = p.center + (pipeGap/2);
    if(!p.scored && p.x + w < player.x){ p.scored = true; score++; document.getElementById('score').innerText = score; }
    // AABB collision
    const rect = {x:player.x,y:player.y,w:player.size,h:player.size};
    const topRect = {x:p.x,y:0,w:w,h:topH};
    const botRect = {x:p.x,y:bottomY,w:w,h:canvas.height-bottomY};
    if(checkRectCollision(rect, topRect) || checkRectCollision(rect, botRect)){ gameOver = true; }
  }
  if(player.y + player.size > canvas.height) gameOver = true;
}

function checkRectCollision(r1,r2){
  return r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y;
}

function render(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  if(images.bg) ctx.drawImage(images.bg,0,0,canvas.width,canvas.height);
  else { ctx.fillStyle='#000'; ctx.fillRect(0,0,canvas.width,canvas.height); }
  for(let p of pipes){
    const w = Math.floor(canvas.width * 0.09);
    const topH = p.center - (pipeGap/2);
    if(images.pipe){
      ctx.drawImage(images.pipe,p.x,0,w,topH);
      ctx.drawImage(images.pipe,p.x,p.center+(pipeGap/2),w,canvas.height-(p.center+(pipeGap/2)));
    } else {
      ctx.fillStyle = '#217a4a'; ctx.fillRect(p.x,0,w,topH); ctx.fillRect(p.x,p.center+(pipeGap/2),w,canvas.height-(p.center+(pipeGap/2)));
    }
  }
  if(images.player) ctx.drawImage(images.player,player.x,player.y,player.size,player.size);
  else { ctx.fillStyle='#f1c40f'; ctx.fillRect(player.x,player.y,player.size,player.size); }
  if(gameOver){
    ctx.fillStyle='rgba(0,0,0,0.5)'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#fff'; ctx.font='36px sans-serif'; ctx.textAlign='center';
    ctx.fillText('GAME OVER - Score: ' + score, canvas.width/2, canvas.height/2);
  }
}

function flap(){ if(!gameRunning||gameOver) return; player.vy = jump; }
window.addEventListener('keydown',(e)=>{ if(e.code==='Space') flap(); });
canvas.addEventListener('mousedown',()=>{ flap(); });
canvas.addEventListener('touchstart',(e)=>{ e.preventDefault(); flap(); },{passive:false});

let lastTS = performance.now();
function loop(ts){
  const dt = ts - lastTS; lastTS = ts;
  update(dt); render();
  if(!gameOver) requestAnimationFrame(loop);
  else { if(ingameAudio) ingameAudio.pause(); try{ const prev = parseInt(localStorage.getItem('flappy_best')||'0'); if(score>prev) localStorage.setItem('flappy_best', String(score)); }catch(e){} }
}

document.getElementById('menuPlayBtn').addEventListener('click', ()=>{ if(menuAudio && musicEnabled) menuAudio.play().catch(()=>{}); });
document.getElementById('startBtn').addEventListener('click', ()=>{ if(!gameRunning){ gameRunning = true; if(menuAudio) menuAudio.pause(); if(ingameAudio && musicEnabled) ingameAudio.play().catch(()=>{}); reset(); last = performance.now(); requestAnimationFrame(loop); } else { reset(); gameOver=false; if(ingameAudio && musicEnabled){ ingameAudio.currentTime = 0; ingameAudio.play().catch(()=>{}); } last = performance.now(); requestAnimationFrame(loop); } });

loadAssets().then(()=>{ try{ const b = parseInt(localStorage.getItem('flappy_best')||'0'); if(b>0) document.getElementById('bestText').innerText = 'Best: ' + b; }catch(e){} render(); }).catch(e=>{ console.warn(e); render(); });

</script>
</body>
</html>
"""

# ------------------ Replace placeholders with safe JS literals ------------------
def js_str_or_null(s):
    if s is None:
        return "null"
    return '"' + s.replace('"', '\\"') + '"'

html = GAME_TEMPLATE.replace("__PLAYER_URL__", PLAYER_URL)
html = html.replace("__PIPE_URL__", PIPE_URL)
html = html.replace("__BG_URL__", BG_URL)
html = html.replace("__MENU_MUSIC_URL__", js_str_or_null(MENU_MUSIC_URL))
html = html.replace("__INGAME_MUSIC_URL__", js_str_or_null(INGAME_MUSIC_URL))
html = html.replace("__GAMEOVER_MUSIC_URL__", js_str_or_null(GAMEOVER_MUSIC_URL))

# ------------------ Render component ------------------
st.components.v1.html(html, height=820, scrolling=False)

st.markdown("---")
st.markdown("**Notes:**")
st.markdown("- Place images in `assets/images/` or root with the expected names. - Place .mp3 in `assets/sounds/` or root. - Use the sidebar only to override if needed.")
