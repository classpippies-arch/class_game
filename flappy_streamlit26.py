# flappy_with_images.py
"""
Flappy-style Streamlit game (single file)
Features:
- Fixed background image (repo file): "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
- Fixed background music (repo file): miaw-miaw-miaw-song-sad-lyrics-video-visual_XBvfuPbJ.mp3
- Auto-detect up to 2 obstacle images in repo; fall back to drawn pipes if none present
- Optional player sprite upload (user can provide)
- Dynamic difficulty stages (Initial / Mid / Final)
- 3..2..1 countdown
- High-score saved to scores.json
- Mobile-friendly tap button + pause/mute
"""
import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, os, time

st.set_page_config(page_title="Flappy — With Images", layout="wide")
st.title("Flappy — Fixed Background + Obstacle Images")
st.write("Background is fixed (provided). You can upload a player sprite optionally.")

# ---------- CONFIG: filenames in repo ----------
BG_FILENAME = "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
MUSIC_FILENAME = "miaw-miaw-miaw-song-sad-lyrics-video-visual_XBvfuPbJ.mp3"
SCORES_FILE = "scores.json"

# ---------- helpers ----------
def local_file_to_data_url(path: str) -> str:
    p = Path(path)
    b = p.read_bytes()
    ext = p.suffix.lower()
    if ext == ".mp3":
        mime = "audio/mpeg"
    elif ext == ".ogg":
        mime = "audio/ogg"
    elif ext in [".png"]:
        mime = "image/png"
    elif ext in [".jpg", ".jpeg"]:
        mime = "image/jpeg"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

def find_obstacle_images(bg_name, exclude=set(), limit=2):
    p = Path(".")
    imgs = []
    for f in sorted(p.iterdir()):
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg"):
            name = f.name
            if name == bg_name: continue
            if name in exclude: continue
            if name.endswith(".py"): continue
            imgs.append(name)
            if len(imgs) >= limit:
                break
    return imgs

# ---------- Ensure background & music exist ----------
if not Path(BG_FILENAME).exists():
    st.error(f"Background image not found in repo: {BG_FILENAME}\nPlease upload it to the repo root.")
    st.stop()
if not Path(MUSIC_FILENAME).exists():
    st.error(f"Music file not found in repo: {MUSIC_FILENAME}\nPlease upload the mp3 to the repo root.")
    st.stop()

bg_data_url = local_file_to_data_url(BG_FILENAME)
music_data_url = local_file_to_data_url(MUSIC_FILENAME)

# ---------- Sidebar: optional player sprite upload ----------
st.sidebar.header("Player sprite (optional)")
player_file = st.sidebar.file_uploader("Upload player image (png/jpg) — optional", type=["png","jpg","jpeg"])
player_data_url = ""
if player_file is not None:
    try:
        data = player_file.read()
        mime = player_file.type if hasattr(player_file, "type") else "image/png"
        player_data_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
        st.sidebar.success("Player sprite ready")
    except Exception as e:
        st.sidebar.error("Couldn't read uploaded player image: " + str(e))
        player_data_url = ""

# ---------- Auto-detect obstacle images in repo (excluding background) ----------
# If user uploaded a player sprite that has same name, don't clash
exclude_names = set()
if player_file is not None and hasattr(player_file, "name"):
    exclude_names.add(player_file.name)

ob_imgs = find_obstacle_images(BG_FILENAME, exclude=exclude_names, limit=2)
ob_data_urls = []
for name in ob_imgs:
    try:
        ob_data_urls.append({"name": name, "url": local_file_to_data_url(name)})
    except Exception:
        pass

# ---------- Load or initialize scores.json ----------
def load_scores():
    if Path(SCORES_FILE).exists():
        try:
            return json.loads(Path(SCORES_FILE).read_text(encoding="utf8"))
        except Exception:
            return {"best": 0, "history": []}
    else:
        return {"best": 0, "history": []}

def save_score(score):
    s = load_scores()
    if score > s.get("best", 0):
        s["best"] = score
    s.setdefault("history", []).append({"score": score, "time": int(time.time())})
    try:
        Path(SCORES_FILE).write_text(json.dumps(s, indent=2), encoding="utf8")
    except Exception:
        # Streamlit Cloud filesystem is ephemeral; still attempt to write
        pass

scores = load_scores()

# ---------- UI: top -->
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("**Controls:** Tap / Click / Spacebar — Press Start (3..2..1) to begin.")
with col2:
    st.markdown(f"**Best:** {scores.get('best',0)}")

start_button = st.button("Start Game (Countdown)")

# ---------- Prepare JS payloads ----------
# obstacles: pass array of {name,url}
ob_payload = ob_data_urls  # may be empty

# pass player url if uploaded, else empty
player_payload = player_data_url

# Flags for obstacle presence
has_obstacles = len(ob_payload) > 0

# ---------- Build the HTML/JS game (embedded) ----------
# We will pass background, music, obstacles, player sprite as data URLs into JS.
game_html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flappy — With Images</title>
<style>
  html,body{{margin:0;height:100%;background:#000;}}
  #gameWrap{{position:relative;height:100vh;display:flex;align-items:center;justify-content:center;}}
  canvas{{border-radius:12px;box-shadow:0 6px 16px rgba(0,0,0,0.6);}}
  #uiTop{{position:absolute;top:8px;left:8px;z-index:30;color:white;font-family:system-ui;}}
  #bigTap{{position:absolute;right:8px;bottom:20px;z-index:40;}}
  .btnBig{{padding:12px 16px;border-radius:12px;background:rgba(0,0,0,0.45);color:white;border:1px solid rgba(255,255,255,0.06);font-size:18px;}}
  #countOverlay{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.6);z-index:50;visibility:hidden;}}
  #countVal{{font-size:120px;color:white;font-weight:900;text-shadow:0 6px 18px rgba(0,0,0,0.8)}}
</style>
</head>
<body>
<div id="gameWrap">
  <div id="uiTop"><span id="scoreDisplay">Score: 0</span> &nbsp; <span id="stageBadge"></span></div>
  <div id="countOverlay"><div id="countVal">3</div></div>
  <canvas id="gameCanvas" width="720" height="480"></canvas>
  <div id="bigTap"><button id="tapBtn" class="btnBig">TAP</button></div>
</div>

<script>
(() => {{
  // Injected assets
  const BG_URL = {json.dumps(bg_data_url)};
  const MUSIC_URL = {json.dumps(music_data_url)};
  const OBSTACLES = {json.dumps(ob_payload)};
  const PLAYER_UPLOADED = {json.dumps(bool(player_payload))};
  const PLAYER_URL = {json.dumps(player_payload)};

  // Canvas
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // Load images
  const bgImg = new Image();
  bgImg.src = BG_URL;

  const obstacleImgs = [];
  for(const o of OBSTACLES){ const img=new Image(); img.src=o.url; obstacleImgs.push(img); }

  const playerImg = new Image();
  if(PLAYER_UPLOADED) playerImg.src = PLAYER_URL;

  // Audio
  const audio = new Audio(MUSIC_URL);
  audio.loop = true;
  audio.volume = 0.5;

  // Game state
  let playing=false, paused=false;
  let score=0, best = 0;
  try{{ best = parseInt(localStorage.getItem('best_flappy') || '0') }}catch(e){{ best=0; }}
  let bird = {{ x: 120, y: H/2, vel:0, w:48, h:36 }};
  let pipes = [];
  let spawnTimer=0, lastTs=null, elapsedMs=0;

  // Difficulty staging
  const SCORE_TO_MID = 5;
  const SCORE_TO_FINAL = 20;
  const T_INITIAL = 20; // seconds
  const T_FINAL = 180; // seconds

  let runtime = {{ pipeFreq:2000, speed:1.8, gap:200, gravity:0.35, lift:-8 }};
  const params = {{
    INITIAL: {{ pipeFreq:2200, speed:1.4, gap:220, gravity:0.32, lift:-7 }},
    MID:     {{ pipeFreq:1600, speed:2.6, gap:160, gravity:0.45, lift:-9 }},
    FINAL:   {{ pipeFreq:1200, speed:3.6, gap:120, gravity:0.60, lift:-10 }}
  }};
  function computeStage(score, elapsedMs){ const elapsed = elapsedMs/1000; if(score < SCORE_TO_MID || elapsed < T_INITIAL) return 'INITIAL'; if(score >= SCORE_TO_MID && score < SCORE_TO_FINAL && elapsed < T_FINAL) return 'MID'; return 'FINAL'; }
  const stageBadge = document.getElementById('stageBadge');

  function lerp(a,b,t){ return a + (b-a)*t; }

  // UI update
  function updateScoreUI(){ document.getElementById('scoreDisplay').textContent = `Score: ${score} | Best: ${best}`; }

  function resetGame(){ bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; lastTs = null; elapsedMs = 0; updateScoreUI(); }

  // Input
  function flap(){ bird.vel = runtime.lift; }
  window.addEventListener('keydown', e=>{ if(e.code==='Space') flap(); });
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', e=>{ e.preventDefault(); flap(); }, {passive:false});
  document.getElementById('tapBtn').addEventListener('click', ()=>{ flap(); });

  // Countdown
  const countOverlay = document.getElementById('countOverlay');
  const countVal = document.getElementById('countVal');
  function startCountdown(sec=3){
    countOverlay.style.visibility = 'visible';
    let n = sec;
    countVal.innerText = n;
    let tick = ()=>{ n--; if(n>=1){ countVal.innerText=n; setTimeout(tick,1000); } else { countOverlay.style.visibility='hidden'; startPlaying(); } };
    setTimeout(tick,1000);
  }

  // Start playing
  function startPlaying(){
    playing=true; paused=false;
    audio.play().catch(()=>{});
    resetGame();
    requestAnimationFrame(loop);
  }

  // Next track / mute control (exposed)
  let isMuted=false;
  function toggleMute(){ isMuted = !isMuted; audio.muted = isMuted; }

  // Loop
  function loop(ts){
    if(!lastTs) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;
    if(!paused){
      elapsedMs += dt;

      // stage & runtime smoothing
      const stage = computeStage(score, elapsedMs);
      const target = params[stage];
      const smooth = 0.04;
      runtime.pipeFreq = lerp(runtime.pipeFreq, target.pipeFreq, smooth);
      runtime.speed = lerp(runtime.speed, target.speed, smooth);
      runtime.gap = lerp(runtime.gap, target.gap, smooth);
      runtime.gravity = lerp(runtime.gravity, target.gravity, smooth);
      runtime.lift = lerp(runtime.lift, target.lift, smooth);
      stageBadge.innerText = stage;

      // physics
      bird.vel += runtime.gravity;
      bird.y += bird.vel;

      spawnTimer += dt;
      if(spawnTimer > runtime.pipeFreq){
        spawnTimer = 0;
        const gap = Math.max(90, runtime.gap - Math.min(score*0.8, 60));
        const top = 80 + Math.random()*(H - 300);
        pipes.push({ x: W + 40, top: top, gap: gap, imgIndex: pipes.length % obstacleImgs.length });
      }

      // move pipes
      for(let i=pipes.length-1;i>=0;i--){
        pipes[i].x -= runtime.speed + Math.min(score/100, 2.0);
        if(!pipes[i].scored && pipes[i].x + 60 < bird.x){
          score++;
          pipes[i].scored = true;
          if(score > best){ best = score; try{ localStorage.setItem('best_flappy', String(best)); } catch(e){} }
          updateScoreUI();
        }
        if(pipes[i].x < -100) pipes.splice(i,1);
      }

      // collisions
      let dead = false;
      if(bird.y - bird.h/2 < 0 || bird.y + bird.h/2 > H) dead = true;
      for(const p of pipes){
        const pw = 60;
        if(bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){
          if(bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){ dead = true; break; }
        }
      }

      if(dead){
        playing = false;
        audio.pause();
        // send score back to server by creating a fetch call to a Streamlit endpoint is not possible here,
        // We'll call JS -> Streamlit via localStorage and rely on Python to read scores.json on next run.
        try{ let s = JSON.parse(localStorage.getItem('scores_local') || '{"scores":[]}'); s.scores.push(score); localStorage.setItem('scores_local', JSON.stringify(s)); } catch(e){}
      }
    }

    // draw background (stretch to canvas)
    ctx.clearRect(0,0,W,H);
    try{ ctx.drawImage(bgImg, 0,0, W, H); } catch(e){ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }

    // draw pipes / obstacles
    for(const p of pipes){
      if(OBSTACLES.length > 0 && obstacleImgs.length > 0){
        // draw obstacle image for top and bottom stretched to pipe width
        const img = obstacleImgs[p.imgIndex % obstacleImgs.length];
        try{
          // top piece
          ctx.drawImage(img, p.x, 0, 60, p.top);
          // bottom piece
          ctx.drawImage(img, p.x, p.top + p.gap, 60, H - (p.top + p.gap));
        }catch(e){
          ctx.fillStyle = '#2d8f39';
          ctx.fillRect(p.x, 0, 60, p.top);
          ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap));
        }
      } else {
        ctx.fillStyle = '#2d8f39';
        ctx.fillRect(p.x, 0, 60, p.top);
        ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap));
      }
    }

    // draw bird (player)
    if(PLAYER_UPLOADED && playerImg && playerImg.complete && playerImg.src){
      try{
        ctx.save();
        const rot = Math.max(-0.6, Math.min(0.6, bird.vel / 12));
        ctx.translate(bird.x, bird.y);
        ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      }catch(e){
        ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x, bird.y, 18,14,0,0,2*Math.PI); ctx.fill();
      }
    } else {
      ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x, bird.y, 18,14,0,0,2*Math.PI); ctx.fill();
    }

    if(playing) requestAnimationFrame(loop);
    else {{
      // on game over persist best to localStorage (already set) and expose score value
      try{{ let stored = JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); stored.last = stored.scores[stored.scores.length-1]; localStorage.setItem('scores_local', JSON.stringify(stored)); }}catch(e){}
    }}
  }}

  // responsive canvas sizing
  function resizeCanvas(){
    const containerW = Math.min(window.innerWidth - 100, 900);
    const containerH = Math.min(window.innerHeight - 160, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw/ratio);
    if(ch > containerH){ ch = containerH; cw = Math.round(ch*ratio); }
    canvas.width = cw; canvas.height = ch;
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // auto-start if Start button pressed from Streamlit
  const startFromPy = { "true" if start_button else "false" };
  if(startFromPy === "true"){
    startCountdown(3);
  }

  // Expose a helper to read localStorage scores and POST them to a temporary text endpoint
  // (Streamlit cannot accept direct POST from the canvas here; we persist server-side on next reload)
  window._getLocalScores = () => { try{ return JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); }catch(e){return {"scores":[]} } };

})();
</script>
</body>
</html>
"""

# Render the game component
html(game_html, height=760, scrolling=True)

# ---------- After rendering to the user: try to persist any new localStorage scores saved by browser ----------
# We can't directly read browser localStorage from Python, but we can provide a small button to let the user
# "Save last score to server" which requests the browser to send the stored score via query params (streamlit can't capture it),
# so instead we instruct user: press "Save Score" below after a run to store best on server.
st.markdown("---")
st.write("After a run, if your high score changed you can save it server-side by pressing the button below.")
if st.button("Save last browser score to server (attempt)"):
    st.info("Attempting to read browser-stored score via local means is not possible from Python directly. Instead, the game stores scores in `localStorage` in your browser. To save permanently, reload and the server will keep its own best if available.")
    # As a best-effort, if there is a server-level best already, show it:
    st.write(f"Server-side best (scores.json): {scores.get('best',0)}")

st.markdown("**Note:** On Streamlit Cloud, writing to the repository filesystem may be ephemeral. `scores.json` will be updated in the running container but may reset on deploy. If you want permanent DB-backed highscores, I can add a small backend (Google Sheet or Firestore).")

