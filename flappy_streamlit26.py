# flappy_final.py
"""
Flappy Game - single-file Streamlit app
Features:
- Fixed background image (repo file) - user cannot change
- Player sprite upload (optional)
- Obstacle images auto-detected from repo, plus optional upload
- Select background music from mp3 files found in repo root
- 3..2..1 countdown
- Dynamic difficulty: Initial -> Mid -> Final (smooth transitions)
- High-score saved to scores.json (server-side)
- Mobile-friendly TAP button + keyboard support
"""

import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, time, os

st.set_page_config(page_title="Flappy Final", layout="wide")
st.title("Flappy — Final (Images, Difficulty, Music selector)")
st.write("Background fixed. Upload player sprite (optional). Choose music from repo. Tap to play.")

# --------- CONFIG ----------
# Background file name you uploaded to repo root (change only if you used different name)
BG_NAME = "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
SCORES_FILE = "scores.json"

# --------- Helpers ----------
def file_to_data_url(path: Path):
    b = path.read_bytes()
    ext = path.suffix.lower()
    if ext == ".mp3": mime = "audio/mpeg"
    elif ext == ".ogg": mime = "audio/ogg"
    elif ext == ".png": mime = "image/png"
    elif ext in (".jpg", ".jpeg"): mime = "image/jpeg"
    else: mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

def list_repo_images(exclude_names=None, limit=5):
    if exclude_names is None: exclude_names=set()
    img_exts = {".png", ".jpg", ".jpeg"}
    root = Path(".")
    found=[]
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix.lower() in img_exts:
            if f.name in exclude_names: continue
            found.append(f.name)
            if len(found)>=limit: break
    return found

def list_repo_mp3s():
    root = Path(".")
    mp3s=[]
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix.lower() in (".mp3", ".ogg"):
            mp3s.append(f.name)
    return mp3s

def load_scores():
    p = Path(SCORES_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf8"))
        except Exception:
            return {"best":0, "history":[]}
    return {"best":0, "history":[]}

def save_score_to_file(score):
    s = load_scores()
    if score > s.get("best",0):
        s["best"] = score
    s.setdefault("history", []).append({"score": score, "time": int(time.time())})
    try:
        Path(SCORES_FILE).write_text(json.dumps(s, indent=2), encoding="utf8")
    except Exception:
        # may fail on immutable FS in some hosts; still attempt
        pass

# --------- Ensure background exists ----------
if not Path(BG_NAME).exists():
    st.error(f"Background image not found: {BG_NAME}. Upload it to repo root or update BG_NAME.")
    st.stop()

# --------- Sidebar: player sprite upload, optional obstacle upload, music select ----------
st.sidebar.header("Customize (optional)")
player_file = st.sidebar.file_uploader("Upload player sprite (png/jpg) — optional", type=["png","jpg","jpeg"])
obstacle_file = st.sidebar.file_uploader("Upload obstacle image (png/jpg) — optional - will be used for pipes", type=["png","jpg","jpeg"])
# list mp3s in repo root
mp3s = list_repo_mp3s()
if not mp3s:
    st.sidebar.warning("No mp3 files in repo root. Add mp3 to repo and reload.")
selected_music = None
if mp3s:
    selected = st.sidebar.selectbox("Select background music (from repo)", mp3s, index=0)
    selected_music = selected

# start button
start_button = st.button("Start / Restart (Countdown)")

# --------- Build assets (data URLs) ----------
bg_url = file_to_data_url(Path(BG_NAME))
music_url = file_to_data_url(Path(selected_music)) if selected_music else ""
player_data_url = ""
if player_file is not None:
    # convert uploaded to data URL
    data = player_file.read()
    mime = player_file.type if hasattr(player_file, "type") else "image/png"
    player_data_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

obstacle_repo = list_repo_images(exclude_names={BG_NAME, Path(__file__).name}, limit=5)
# remove script name if present; keep up to 2 obstacles
obstacle_urls = []
# if user uploaded obstacle_file, prioritize it
if obstacle_file is not None:
    data = obstacle_file.read()
    mime = obstacle_file.type if hasattr(obstacle_file, "type") else "image/png"
    obstacle_urls.append({"name": obstacle_file.name, "url": f"data:{mime};base64," + base64.b64encode(data).decode("ascii")})
# then include up to 2 repo images (excluding bg)
for name in obstacle_repo:
    if len(obstacle_urls) >= 2: break
    if name == player_file.name if player_file is not None else False: continue
    obstacle_urls.append({"name": name, "url": file_to_data_url(Path(name))})

# scores
scores = load_scores()

# --------- Build HTML/JS (injected using json dumps to avoid f-string/braces issues) ----------
# We will inject JSON strings for bg, music, obstacles, player; JS code uses them directly.
html_template = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flappy Final</title>
<style>
  html,body { margin:0; height:100%; font-family: system-ui, -apple-system, 'Segoe UI', Roboto; background:#111; color:#fff; }
  #wrap { position:relative; height:100vh; display:flex; align-items:center; justify-content:center; }
  canvas { border-radius:12px; box-shadow:0 6px 18px rgba(0,0,0,0.6); }
  #uiTop { position:absolute; top:8px; left:8px; z-index:40; }
  #controls { position:absolute; top:8px; right:8px; z-index:40; display:flex; gap:8px; }
  .btn { padding:8px 12px; border-radius:10px; background:rgba(0,0,0,0.45); color:white; border:1px solid rgba(255,255,255,0.06); cursor:pointer; }
  #countOverlay { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:50; background:rgba(0,0,0,0.6); visibility:hidden; }
  #countVal { font-size:120px; font-weight:900; color:white; text-shadow:0 6px 18px rgba(0,0,0,0.6); }
  #tapBtn { position:absolute; right:8px; bottom:26px; z-index:48; padding:14px 18px; font-size:18px; border-radius:12px; }
  @media (max-width:600px) {
    #countVal { font-size:72px; }
    canvas { width: calc(100vw - 20px) !important; height: calc((100vw - 20px) * 2 / 3) !important; }
    #tapBtn { right:12px; bottom:18px; padding:12px 16px; font-size:16px; }
  }
</style>
</head>
<body>
  <div id="wrap">
    <div id="uiTop">
      <div id="scoreDisplay">Score: 0 | Best: 0</div>
    </div>
    <div id="controls">
      <button id="muteBtn" class="btn">Mute</button>
      <button id="pauseBtn" class="btn">Pause</button>
    </div>
    <div id="countOverlay"><div id="countVal">3</div></div>
    <canvas id="gameCanvas" width="720" height="480"></canvas>
    <button id="tapBtn" class="btn">TAP</button>
  </div>

<script>
(() => {
  const BG_URL = __BG_URL__;
  const MUSIC_URL = __MUSIC_URL__;
  const OBSTACLES = __OBSTACLES__;
  const PLAYER_URL = __PLAYER_URL__;
  const START_FROM_PY = __START_FROM_PY__;

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  const bgImg = new Image(); bgImg.src = BG_URL;

  const obstacleImgs = [];
  for (let i=0;i<OBSTACLES.length;i++){
    const img = new Image();
    img.src = OBSTACLES[i].url;
    obstacleImgs.push(img);
  }

  const playerImg = new Image();
  if (PLAYER_URL) playerImg.src = PLAYER_URL;

  // audio
  const audio = new Audio(MUSIC_URL);
  audio.loop = true;
  audio.volume = 0.55;

  // game state
  let playing=false, paused=false;
  let lastTs=null, elapsedMs=0;
  let bird={x:120, y: H/2, vel:0, w:48, h:36};
  let pipes=[];
  let spawnTimer=0;
  let score=0;
  let best=0;
  try{ best = parseInt(localStorage.getItem('best_flappy')||'0'); }catch(e){ best=0; }
  document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`;

  // difficulty staging
  const SCORE_TO_MID = 5;
  const SCORE_TO_FINAL = 20;
  const T_INITIAL = 25; // seconds
  const T_FINAL = 180;
  const params = {
    INITIAL: {pipeFreq:2200, speed:1.4, gap:220, gravity:0.32, lift:-7},
    MID:     {pipeFreq:1600, speed:2.4, gap:160, gravity:0.45, lift:-9},
    FINAL:   {pipeFreq:1100, speed:3.4, gap:120, gravity:0.62, lift:-10}
  };
  let runtime = Object.assign({}, params.INITIAL);

  function computeStage(score, elapsedMs){
    const elapsed = elapsedMs/1000;
    if (score < SCORE_TO_MID || elapsed < T_INITIAL) return 'INITIAL';
    if (score >= SCORE_TO_MID && score < SCORE_TO_FINAL && elapsed < T_FINAL) return 'MID';
    return 'FINAL';
  }
  function lerp(a,b,t){return a + (b-a)*t;}

  function updateScoreUI(){ document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`; }

  function resetGame(){
    bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; elapsedMs = 0; lastTs = null;
    updateScoreUI();
  }

  // controls
  function flap(){ bird.vel = runtime.lift; }
  window.addEventListener('keydown', e=>{ if (e.code === 'Space') flap(); });
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', e=>{ e.preventDefault(); flap(); }, {passive:false});
  document.getElementById('tapBtn').addEventListener('click', ()=>{ flap(); });

  document.getElementById('muteBtn').addEventListener('click', ()=>{
    audio.muted = !audio.muted;
    document.getElementById('muteBtn').innerText = audio.muted ? 'Unmute' : 'Mute';
  });
  document.getElementById('pauseBtn').addEventListener('click', ()=>{
    paused = !paused;
    document.getElementById('pauseBtn').innerText = paused ? 'Resume' : 'Pause';
    if (paused) audio.pause(); else audio.play().catch(()=>{});
  });

  // countdown
  const overlay = document.getElementById('countOverlay');
  const countVal = document.getElementById('countVal');
  function startCountdown(n=3){
    overlay.style.visibility = 'visible';
    countVal.innerText = n;
    const tick = ()=>{
      n--;
      if (n >= 1){ countVal.innerText = n; setTimeout(tick, 1000); }
      else { overlay.style.visibility = 'hidden'; startPlaying(); }
    };
    setTimeout(tick, 1000);
  }

  function startPlaying(){
    playing = true; paused = false;
    resetGame();
    audio.play().catch(()=>{});
    requestAnimationFrame(loop);
  }

  function loop(ts){
    if (!lastTs) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;
    if (!paused){
      elapsedMs += dt;

      // stage & smooth runtime
      const stage = computeStage(score, elapsedMs);
      const tgt = params[stage];
      const smooth = 0.04;
      runtime.pipeFreq = lerp(runtime.pipeFreq, tgt.pipeFreq, smooth);
      runtime.speed = lerp(runtime.speed, tgt.speed, smooth);
      runtime.gap = lerp(runtime.gap, tgt.gap, smooth);
      runtime.gravity = lerp(runtime.gravity, tgt.gravity, smooth);
      runtime.lift = lerp(runtime.lift, tgt.lift, smooth);

      // physics
      bird.vel += runtime.gravity;
      bird.y += bird.vel;

      spawnTimer += dt;
      if (spawnTimer > runtime.pipeFreq){
        spawnTimer = 0;
        const gap = Math.max(90, runtime.gap - Math.min(score*0.8, 60));
        const top = 60 + Math.random() * (H - 260);
        pipes.push({x: W + 40, top: top, gap: gap, imgIndex: pipes.length % Math.max(1, obstacleImgs.length)});
      }

      // move pipes & scoring
      for (let i = pipes.length-1; i >= 0; i--){
        const p = pipes[i];
        p.x -= runtime.speed + Math.min(score/100, 2.0);
        if (!p.scored && p.x + 60 < bird.x){
          score++; p.scored = true;
          if (score > best){ best = score; try{ localStorage.setItem('best_flappy', String(best)); }catch(e){} }
          updateScoreUI();
        }
        if (p.x < -120) pipes.splice(i,1);
      }

      // collision
      let dead = false;
      if (bird.y - bird.h/2 < 0 || bird.y + bird.h/2 > H) dead = true;
      for (const p of pipes){
        const pw = 60;
        if (bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){
          if (bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){ dead = true; break; }
        }
      }

      if (dead){
        playing = false;
        audio.pause();
        try{ let s = JSON.parse(localStorage.getItem('scores_local') || '{"scores":[]}'); s.scores.push(score); localStorage.setItem('scores_local', JSON.stringify(s)); }catch(e){}
        // also attempt to persist best locally
        try{ localStorage.setItem('best_flappy', String(best)); }catch(e){}
        // send score to Streamlit by instructing user to press Save (below) - server-side write handled in Python on request
      }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    // background
    try{ ctx.drawImage(bgImg, 0, 0, W, H); } catch(e){ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }

    // pipes / obstacles
    for (const p of pipes){
      if (obstacleImgs.length > 0){
        const img = obstacleImgs[p.imgIndex % obstacleImgs.length];
        try{
          ctx.drawImage(img, p.x, 0, 60, p.top);
          ctx.drawImage(img, p.x, p.top + p.gap, 60, H - (p.top + p.gap));
        }catch(e){
          ctx.fillStyle='#2d8f39'; ctx.fillRect(p.x, 0, 60, p.top); ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap));
        }
      } else {
        ctx.fillStyle='#2d8f39'; ctx.fillRect(p.x, 0, 60, p.top); ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap));
      }
    }

    // bird
    if (PLAYER_URL && playerImg && playerImg.complete && playerImg.src){
      try{
        ctx.save();
        const rot = Math.max(-0.7, Math.min(0.7, bird.vel / 12));
        ctx.translate(bird.x, bird.y); ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      }catch(e){
        ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x, bird.y, 18, 14, 0, 0, Math.PI*2); ctx.fill();
      }
    } else {
      ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x, bird.y, 18, 14, 0, 0, Math.PI*2); ctx.fill();
    }

    if (playing) requestAnimationFrame(loop);
  }

  // responsive
  function resizeCanvas(){
    const containerW = Math.min(window.innerWidth - 40, 900);
    const containerH = Math.min(window.innerHeight - 140, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if (ch > containerH){ ch = containerH; cw = Math.round(ch * ratio); }
    canvas.width = cw; canvas.height = ch;
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // auto start if python button pressed
  if (START_FROM_PY === true) startCountdown(3);

  // expose helper to get local scores (user can copy-paste)
  window._getLocalScores = function(){ try{ return JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); }catch(e){ return {"scores":[]} } };

})();
</script>
</body>
</html>
"""

# Inject jsonified payloads safely
injected = html_template
injected = injected.replace("__BG_URL__", json.dumps(bg_url))
injected = injected.replace("__MUSIC_URL__", json.dumps(music_url if music_url else ""))

# obstacles JSON array
injected = injected.replace("__OBSTACLES__", json.dumps(obstacle_urls))
injected = injected.replace("__PLAYER_URL__", json.dumps(player_data_url))
injected = injected.replace("__START_FROM_PY__", "true" if start_button else "false")

# Render
html(injected, height=760, scrolling=True)

# ---------- Save server-side score endpoint emulation ----------
st.markdown("---")
st.write("After a run, press the button below to save the browser's best score to server `scores.json` (best-effort). On Streamlit Cloud filesystem writes may be ephemeral across redeploys.")
if st.button("Save best score from browser to server (best-effort)"):
    # Attempt to read localStorage via manual user copy-paste flow:
    st.info("Open browser console and run: `copy(window._getLocalScores())` then paste here the JSON (or paste the best integer).")
    pasted = st.text_area("Paste the JSON returned from copy(window._getLocalScores()) or just paste the best score integer:", height=120)
    if pasted:
        # try to parse integer or JSON
        try:
            obj = json.loads(pasted)
            if isinstance(obj, dict) and "scores" in obj:
                last = obj["scores"][-1] if obj["scores"] else None
                if last is not None:
                    save_score_to_file(int(last))
                    st.success(f"Saved score {last} to {SCORES_FILE} (server-side).")
                else:
                    st.error("No scores found in pasted JSON.")
            else:
                # maybe user pasted an int or array
                if isinstance(obj, int):
                    save_score_to_file(int(obj)); st.success(f"Saved score {obj}.")
                elif isinstance(obj, list) and obj:
                    save_score_to_file(int(obj[-1])); st.success(f"Saved score {obj[-1]}.")
                else:
                    st.error("Couldn't interpret pasted JSON.")
        except Exception:
            # try integer
            try:
                val = int(pasted.strip())
                save_score_to_file(val)
                st.success(f"Saved score {val} to {SCORES_FILE}.")
            except Exception as e:
                st.error("Failed to parse pasted content. Paste the JSON copied from browser console or a number.")
st.write(f"Server-side best (scores.json): {load_scores().get('best',0)}")
st.markdown("**Note:** Streamlit Cloud may reset files on redeploy. For permanent storage, I can add Google Sheets/Firestore backend.")

