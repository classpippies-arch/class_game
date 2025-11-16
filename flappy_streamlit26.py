# flappy_premium.py
"""
Flappy — Premium single-file Streamlit app
- Uses repo images / mp3s
- Shows main character image above Start button (fixed)
- Player sprite can be uploaded (optional)
- Obstacles use repo images (up to 2) or fallback pipes
- Music selector from repo MP3s
- Sound effects (flap/score/hit) via WebAudio (no extra files needed)
- Dynamic difficulty, 3-2-1 countdown, mobile-friendly
- Saves best score to scores.json (best-effort)
"""
import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, time

st.set_page_config(page_title="Flappy — Premium", layout="wide")
st.title("Flappy — Premium (Main character shown + Sound Effects + Music selector)")
st.write("Main character shown above Start — choose music from repo, upload player sprite optionally.")

# -------------- helpers to read repo files ----------------
ROOT = Path(".")
def list_images(exclude=set(), limit=10):
    ext = (".png", ".jpg", ".jpeg")
    files = []
    for f in sorted(ROOT.iterdir()):
        if f.is_file() and f.suffix.lower() in ext and f.name not in exclude:
            files.append(f.name)
            if len(files) >= limit:
                break
    return files

def list_mp3s():
    ext = (".mp3", ".ogg")
    files = []
    for f in sorted(ROOT.iterdir()):
        if f.is_file() and f.suffix.lower() in ext:
            files.append(f.name)
    return files

def file_to_data_url(path: Path):
    b = path.read_bytes()
    ext = path.suffix.lower()
    if ext == ".mp3": mime = "audio/mpeg"
    elif ext == ".ogg": mime = "audio/ogg"
    elif ext == ".png": mime = "image/png"
    elif ext in (".jpg", ".jpeg"): mime = "image/jpeg"
    else: mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

# -------------- auto-detect assets in repo ----------------
# prefer the filenames you uploaded earlier
BG_CANDIDATE = "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
MAIN_CHAR_CANDIDATE = "Screenshot 2025-11-16 131426.png"  # I saw this in your repo
# we'll search repo for images, prioritizing the above names
all_images = list_images()
bg_name = BG_CANDIDATE if Path(BG_CANDIDATE).exists() else (all_images[0] if all_images else "")
main_char_name = MAIN_CHAR_CANDIDATE if Path(MAIN_CHAR_CANDIDATE).exists() else (all_images[1] if len(all_images)>1 else (all_images[0] if all_images else ""))

# Obstacles: choose up to two images in repo excluding bg and the main char and script file
exclude = {bg_name, main_char_name}
obstacle_files = [n for n in list_images(exclude=exclude)][:2]

# music list
mp3s = list_mp3s()

# -------------- Sidebar UI ----------------
st.sidebar.header("Customize / Upload")

st.sidebar.markdown("**Main character shown on screen** (fixed from repo).")
st.sidebar.markdown("**Optional:** Upload your player sprite (png/jpg) to override the default bird.")
player_file = st.sidebar.file_uploader("Upload player sprite (optional)", type=["png","jpg","jpeg"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Optional obstacle upload** (will be used for pipes if provided).")
ob_upload = st.sidebar.file_uploader("Upload an obstacle image (optional)", type=["png","jpg","jpeg"])

st.sidebar.markdown("---")
if not mp3s:
    st.sidebar.warning("No .mp3 files found in repo root. Add mp3 files to repo to select music.")
music_choice = None
if mp3s:
    music_choice = st.sidebar.selectbox("Choose background music (from repo)", mp3s, index=0)

st.sidebar.markdown("---")
st.sidebar.write("Sound effects: flap/score/hit are built-in (WebAudio).")

# -------------- prepare data URLs for injection ----------------
bg_url = file_to_data_url(Path(bg_name)) if bg_name else ""
main_char_url = file_to_data_url(Path(main_char_name)) if main_char_name else ""
player_url = ""
if player_file is not None:
    pdata = player_file.read()
    pmime = player_file.type if hasattr(player_file, "type") else "image/png"
    player_url = f"data:{pmime};base64," + base64.b64encode(pdata).decode("ascii")

# obstacle urls array (user uploaded first if present)
obstacles = []
if ob_upload is not None:
    data = ob_upload.read()
    mime = ob_upload.type if hasattr(ob_upload, "type") else "image/png"
    obstacles.append({"name": ob_upload.name, "url": f"data:{mime};base64," + base64.b64encode(data).decode("ascii")})

for f in obstacle_files:
    if len(obstacles) >= 2: break
    obstacles.append({"name": f, "url": file_to_data_url(Path(f))})

# music url
music_url = file_to_data_url(Path(music_choice)) if music_choice else ""

# -------------- main UI: show main character image & Start button -------------
col1, col2 = st.columns([2,1])
with col1:
    st.markdown("### Game preview")
    if bg_name:
        st.image(bg_url, caption="Background (fixed)", use_column_width=True)
    else:
        st.info("No background image found in repo root.")

with col2:
    st.markdown("### Main character")
    if main_char_url:
        st.image(main_char_url, width=200, caption="Main character (fixed)")
    else:
        st.info("No main character image found.")
    st.write("")
    # Start button shown in Streamlit UI (also embedded Start in canvas)
    start_clicked = st.button("Start Game (3..2..1)")

st.markdown("---")
st.write("Mobile: use TAP button or spacebar to flap. Pause / Mute available in-game.")

# -------------- Scores handling ----------------
SCORES_FILE = "scores.json"
def load_scores():
    p = Path(SCORES_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf8"))
        except:
            return {"best": 0, "history": []}
    return {"best": 0, "history": []}

def save_score(score):
    s = load_scores()
    if score > s.get("best", 0):
        s["best"] = score
    s.setdefault("history", []).append({"score": score, "time": int(time.time())})
    try:
        Path(SCORES_FILE).write_text(json.dumps(s, indent=2), encoding="utf8")
    except:
        pass

# -------------- Build HTML/JS and inject via json.dumps to avoid f-string brace issues --------------
html_template = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flappy Premium</title>
<style>
  html,body{{margin:0;height:100%;font-family:system-ui;background:#111;color:#fff}}
  #wrap{{position:relative;height:100vh;display:flex;align-items:center;justify-content:center}}
  canvas{{border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.6)}}
  #uiTop{{position:absolute;top:8px;left:8px;z-index:40}}
  #controls{{position:absolute;top:8px;right:8px;z-index:40;display:flex;gap:8px}}
  .btn{{padding:8px 12px;border-radius:10px;background:rgba(0,0,0,0.45);color:white;border:1px solid rgba(255,255,255,0.06);cursor:pointer}}
  #countOverlay{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:60;background:rgba(0,0,0,0.6);visibility:hidden}}
  #countVal{{font-size:120px;font-weight:900;color:white;text-shadow:0 6px 18px rgba(0,0,0,0.8)}}
  #tapBtn{{position:absolute;right:14px;bottom:26px;z-index:58;padding:14px 18px;font-size:18px;border-radius:12px}}
  @media (max-width:600px){ #countVal{{font-size:72px}} canvas{{width:calc(100vw - 20px)!important;height:calc((100vw - 20px)*2/3)!important}} #tapBtn{{right:12px;bottom:18px;padding:12px 16px;font-size:16px}}}
</style>
</head>
<body>
<div id="wrap">
  <div id="uiTop"><div id="scoreDisplay">Score: 0 | Best: 0</div></div>
  <div id="controls"><button id="muteBtn" class="btn">Mute</button><button id="pauseBtn" class="btn">Pause</button></div>
  <div id="countOverlay"><div id="countVal">3</div></div>
  <canvas id="gameCanvas" width="720" height="480"></canvas>
  <button id="tapBtn" class="btn">TAP</button>
</div>

<script>
(() => {{
  // injected assets
  const BG_URL = {bg};
  const MUSIC_URL = {music};
  const OBSTACLES = {obstacles};
  const PLAYER_URL = {player};
  const START_FROM_PY = {start};

  // canvas setup
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // images
  const bgImg = new Image(); if(BG_URL) bgImg.src = BG_URL;
  const obstacleImgs = [];
  for(let i=0;i<OBSTACLES.length;i++){{ const img=new Image(); img.src = OBSTACLES[i].url; obstacleImgs.push(img); }}
  const playerImg = new Image(); if(PLAYER_URL) playerImg.src = PLAYER_URL;

  // audio: background music (from repo)
  const audio = new Audio(MUSIC_URL || '');
  audio.loop = true; audio.volume = 0.55;

  // WebAudio sound effects (flap, score, hit)
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  function playBeep(freq, duration=0.06, type='sine', gain=0.12){ try{{ const o = audioCtx.createOscillator(); const g = audioCtx.createGain(); o.type=type; o.frequency.value=freq; g.gain.setValueAtTime(gain, audioCtx.currentTime); o.connect(g); g.connect(audioCtx.destination); o.start(); o.stop(audioCtx.currentTime + duration); }}catch(e){{}} }
  function flapSnd(){ playBeep(880,0.05,'square',0.08); }
  function scoreSnd(){ playBeep(1200,0.06,'sine',0.12); setTimeout(()=>playBeep(1500,0.04,'sine',0.08),60); }
  function hitSnd(){ playBeep(180,0.12,'sawtooth',0.16); }

  // game state
  let playing=false, paused=false;
  let lastTs=null, elapsedMs=0;
  let bird = {{ x:120, y:H/2, vel:0, w:48, h:36 }};
  let pipes = [];
  let spawnTimer=0;
  let score=0;
  let best = 0;
  try{{ best = parseInt(localStorage.getItem('best_flappy')||'0'); }}catch(e){{ best=0; }}
  document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`;

  // difficulty params and smoothing
  const SCORE_TO_MID = 5, SCORE_TO_FINAL = 20;
  const T_INITIAL = 22, T_FINAL = 180;
  const params = {{
    INITIAL: {{pipeFreq:2200, speed:1.4, gap:220, gravity:0.32, lift:-7}},
    MID:     {{pipeFreq:1600, speed:2.6, gap:160, gravity:0.45, lift:-9}},
    FINAL:   {{pipeFreq:1100, speed:3.6, gap:120, gravity:0.6, lift:-10}}
  }};
  let runtime = Object.assign({{}}, params.INITIAL);
  function computeStage(score, elapsedMs){ const e = elapsedMs/1000; if(score < SCORE_TO_MID || e < T_INITIAL) return 'INITIAL'; if(score >= SCORE_TO_MID && score < SCORE_TO_FINAL && e < T_FINAL) return 'MID'; return 'FINAL'; }
  function lerp(a,b,t){{return a + (b-a)*t;}}

  function updateScoreUI(){{ document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`; }}

  function resetGame(){ bird.y = H/2; bird.vel=0; pipes=[]; spawnTimer=0; score=0; elapsedMs=0; lastTs=null; updateScoreUI(); }

  // input
  function flap(){ bird.vel = runtime.lift; flapSnd(); }
  window.addEventListener('keydown', e=>{{ if(e.code==='Space') flap(); }});
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', e=>{{ e.preventDefault(); flap(); }}, {{passive:false}});
  document.getElementById('tapBtn').addEventListener('click', ()=>{{ flap(); }});

  // controls
  document.getElementById('muteBtn').addEventListener('click', ()=>{{ audio.muted = !audio.muted; document.getElementById('muteBtn').innerText = audio.muted ? 'Unmute' : 'Mute'; }});
  document.getElementById('pauseBtn').addEventListener('click', ()=>{{ paused = !paused; document.getElementById('pauseBtn').innerText = paused ? 'Resume' : 'Pause'; if(paused) audio.pause(); else audio.play().catch(()=>{{}}); }});

  // countdown
  const overlay = document.getElementById('countOverlay');
  const countVal = document.getElementById('countVal');
  function startCountdown(n=3){ overlay.style.visibility='visible'; countVal.innerText = n; const tick = ()=>{{ n--; if(n>=1){{ countVal.innerText=n; setTimeout(tick,1000); }} else {{ overlay.style.visibility='hidden'; startPlaying(); }} }}; setTimeout(tick,1000); }

  function startPlaying(){ playing=true; paused=false; resetGame(); if(MUSIC_URL) audio.play().catch(()=>{{}}); requestAnimationFrame(loop); }

  // main loop
  function loop(ts){ if(!lastTs) lastTs = ts; const dt = ts - lastTs; lastTs = ts; if(!paused){ elapsedMs += dt; // stage & smooth runtime
      const stage = computeStage(score, elapsedMs); const tgt = params[stage]; const smooth=0.04;
      runtime.pipeFreq = lerp(runtime.pipeFreq, tgt.pipeFreq, smooth);
      runtime.speed = lerp(runtime.speed, tgt.speed, smooth);
      runtime.gap = lerp(runtime.gap, tgt.gap, smooth);
      runtime.gravity = lerp(runtime.gravity, tgt.gravity, smooth);
      runtime.lift = lerp(runtime.lift, tgt.lift, smooth);

      // physics
      bird.vel += runtime.gravity; bird.y += bird.vel;

      spawnTimer += dt;
      if(spawnTimer > runtime.pipeFreq){ spawnTimer = 0; const gap = Math.max(80, runtime.gap - Math.min(score*0.8,60)); const top = 60 + Math.random() * (H - 260); pipes.push({x: W + 40, top: top, gap: gap, imgIndex: pipes.length % Math.max(1, obstacleImgs.length)}); }

      // move pipes, scoring
      for(let i=pipes.length-1;i>=0;i--){ const p = pipes[i]; p.x -= runtime.speed + Math.min(score/100,2.0); if(!p.scored && p.x + 60 < bird.x){ score++; p.scored=true; scoreSnd(); if(score>best){ best=score; try{{ localStorage.setItem('best_flappy', String(best)); }}catch(e){{}} } updateScoreUI(); } if(p.x < -120) pipes.splice(i,1); }

      // collisions
      let dead=false;
      if(bird.y - bird.h/2 < 0 || bird.y + bird.h/2 > H) dead=true;
      for(const p of pipes){ const pw=60; if(bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){ if(bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){ dead=true; break; } } }
      if(dead){ playing=false; audio.pause(); hitSnd(); try{{ let s = JSON.parse(localStorage.getItem('scores_local')||'{{"scores":[]}}'); s.scores.push(score); localStorage.setItem('scores_local', JSON.stringify(s)); }}catch(e){{}} try{{ localStorage.setItem('best_flappy', String(best)); }}catch(e){{}} }
  }

    // draw
    ctx.clearRect(0,0,W,H);
    if(BG_URL){ try{{ ctx.drawImage(bgImg,0,0,W,H); }}catch(e){{ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }} } else {{ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }}
    // pipes
    for(const p of pipes){ if(obstacleImgs.length>0){ const img = obstacleImgs[p.imgIndex % obstacleImgs.length]; try{{ ctx.drawImage(img, p.x, 0, 60, p.top); ctx.drawImage(img, p.x, p.top + p.gap, 60, H - (p.top + p.gap)); }}catch(e){{ ctx.fillStyle='#2d8f39'; ctx.fillRect(p.x,0,60,p.top); ctx.fillRect(p.x,p.top+p.gap,60,H-(p.top+p.gap)); }} } else {{ ctx.fillStyle='#2d8f39'; ctx.fillRect(p.x,0,60,p.top); ctx.fillRect(p.x,p.top+p.gap,60,H-(p.top+p.gap)); } }
    // bird
    if(PLAYER_URL && playerImg && playerImg.complete && playerImg.src){ try{{ ctx.save(); const rot = Math.max(-0.7, Math.min(0.7, bird.vel/12)); ctx.translate(bird.x,bird.y); ctx.rotate(rot); ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h); ctx.restore(); }}catch(e){{ ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill(); }} } else {{ ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill(); } }
    if(playing) requestAnimationFrame(loop);
  }

  // responsive canvas
  function resizeCanvas(){ const cW = Math.min(window.innerWidth - 40, 900); const cH = Math.min(window.innerHeight - 140, 700); const ratio = 3/2; let cw=cW, ch=Math.round(cw/ratio); if(ch>cH){ ch=cH; cw=Math.round(ch*ratio); } canvas.width=cw; canvas.height=ch; W=canvas.width; H=canvas.height; }
  window.addEventListener('resize', resizeCanvas); resizeCanvas();

  // auto-start if python button pressed
  if(START_FROM_PY === true) startCountdown(3);

  // expose helper for copying local scores
  window._getLocalScores = function(){ try{{ return JSON.parse(localStorage.getItem('scores_local')||'{{"scores":[]}}'); }}catch(e){{ return {{scores:[]}}; }} };

})();
</script>
</body>
</html>
"""

# safe inject values
injected = html_template
injected = injected.replace("{bg}", json.dumps(bg_url))
injected = injected.replace("{music}", json.dumps(music_url))
injected = injected.replace("{obstacles}", json.dumps(obstacles))
injected = injected.replace("{player}", json.dumps(player_url))
injected = injected.replace("{start}", "true" if start_clicked else "false")

# render
html(injected, height=760, scrolling=True)

# -------------- server-side score save flow --------------
st.markdown("---")
st.write("After playing, to save your last score server-side: open browser console, run `copy(window._getLocalScores())`, then paste the JSON below and press Save.")
pasted = st.text_area("Paste copied JSON from browser (or paste an integer score):", height=140)
if st.button("Save pasted score to server (scores.json)"):
    if not pasted.strip():
        st.error("Paste the JSON returned from the browser console first.")
    else:
        try:
            obj = json.loads(pasted)
            if isinstance(obj, dict) and "scores" in obj and obj["scores"]:
                last = int(obj["scores"][-1])
                save_score(last)
                st.success(f"Saved score {last} to scores.json (server).")
            elif isinstance(obj, int):
                save_score(int(obj)); st.success(f"Saved score {obj}")
            else:
                st.error("Couldn't parse pasted content. Paste the JSON or an integer.")
        except Exception:
            try:
                val = int(pasted.strip()); save_score(val); st.success(f"Saved score {val}")
            except Exception:
                st.error("Failed to parse pasted content. Paste the JSON from browser console or a number.")

st.write("Server-side best:", load_scores().get("best", 0))
st.markdown("Note: Streamlit Cloud file writes may be ephemeral across redeploys. For permanent storage I can add Google Sheets/Firestore backend.")
