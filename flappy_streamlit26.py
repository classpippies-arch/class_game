# flappy_home_music_switch.py
"""
Flappy — Home music (fixed) on menu, switch to user-selected in-game music when Play starts.
- Home screen does NOT show main-character image.
- Home music: a fixed repo mp3 (HOME_MUSIC_NAME) - attempts autoplay, shows Play Home Music button if blocked.
- In-game music: selected by user from repo mp3s in sidebar.
- Start button triggers 3..2..1 countdown, stops home music, starts in-game music.
- Single-file Streamlit app. Place in repo root with your images/mp3s.
"""

import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, time

st.set_page_config(page_title="Flappy — Home Music Switch", layout="wide")
st.title("Flappy — Home Music on Menu, Switch to Selected Music on Start")
st.write("Home music plays on menu (tap Play Home Music if browser blocks). On Start, home music stops and game music (selected in sidebar) will play.")

# ---------- CONFIG: filenames in repo ----------
# Change these names if your files have different names in the repo root
BG_NAME = "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
# The specific track you want to play on Home Screen (put it in repo root)
HOME_MUSIC_NAME = "audioblocks-mind-game-or-quiz-tension-back.mp3"  # replace with exact filename if differs

# Optional: fallback to first mp3 in repo if HOME_MUSIC_NAME not found
def list_mp3s():
    root = Path(".")
    mp3s = []
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix.lower() in (".mp3", ".ogg"):
            mp3s.append(f.name)
    return mp3s

# helper to convert local file to data URL
def file_to_data_url(p: Path):
    b = p.read_bytes()
    ext = p.suffix.lower()
    if ext == ".mp3": mime = "audio/mpeg"
    elif ext == ".ogg": mime = "audio/ogg"
    elif ext == ".png": mime = "image/png"
    elif ext in (".jpg", ".jpeg"): mime = "image/jpeg"
    else: mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

# Check repo mp3s
mp3_files = list_mp3s()
if not mp3_files:
    st.error("No mp3 files found in repo root. Add at least one mp3 file and reload.")
    st.stop()

# Ensure HOME_MUSIC exists; fallback if not
if not Path(HOME_MUSIC_NAME).exists():
    # pick first mp3 as home music
    HOME_MUSIC_NAME = mp3_files[0]

# Sidebar: choose in-game music (from repo mp3s)
st.sidebar.header("Game Music (choose for in-game)")
game_music_selected = st.sidebar.selectbox("Select in-game music (from repo)", mp3_files, index=0)

# Sidebar: optional player sprite upload (user may upload)
st.sidebar.header("Player sprite (optional)")
player_file = st.sidebar.file_uploader("Upload player image (png/jpg) — optional", type=["png","jpg","jpeg"])
player_data_url = ""
if player_file is not None:
    data = player_file.read()
    mime = player_file.type if hasattr(player_file, "type") else "image/png"
    player_data_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

# Background image (kept as visual; no main-character shown on home screen)
bg_url = ""
if Path(BG_NAME).exists():
    bg_url = file_to_data_url(Path(BG_NAME))

# Home music and in-game music data URLs
home_music_url = file_to_data_url(Path(HOME_MUSIC_NAME))
game_music_url = file_to_data_url(Path(game_music_selected)) if Path(game_music_selected).exists() else home_music_url

# Start button in Streamlit UI triggers JS start too
start_clicked = st.button("Start Game (3..2..1)")

# Also provide a 'Play Home Music' fallback button for browsers that block autoplay
play_home_music_clicked = st.button("Play Home Music (if silent)")

# Build and inject HTML+JS. Use json.dumps injection to avoid f-string brace issues.
import json
bg_json = json.dumps(bg_url)
home_music_json = json.dumps(home_music_url)
game_music_json = json.dumps(game_music_url)
player_json = json.dumps(player_data_url)
start_flag = "true" if start_clicked else "false"
play_home_flag = "true" if play_home_music_clicked else "false"

game_html = f"""
<!doctype html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flappy - Home Music Switch</title>
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
  @media (max-width:600px){{ #countVal{{font-size:72px}} canvas{{width:calc(100vw - 20px)!important;height:calc((100vw - 20px)*2/3)!important}} #tapBtn{{right:12px;bottom:18px;padding:12px 16px;font-size:16px}} }}
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
  // Injected assets
  const BG_URL = {bg_json};
  const HOME_MUSIC_URL = {home_music_json};
  const GAME_MUSIC_URL = {game_music_json};
  const PLAYER_URL = {player_json};
  const START_FROM_PY = {start_flag};
  const PLAY_HOME_FROM_PY = {play_home_flag};

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // load images
  const bgImg = new Image();
  if (BG_URL) bgImg.src = BG_URL;

  const playerImg = new Image();
  if (PLAYER_URL) playerImg.src = PLAYER_URL;

  // Audio: two audio objects
  const homeAudio = new Audio(HOME_MUSIC_URL || '');
  homeAudio.loop = true; homeAudio.volume = 0.55;
  const gameAudio = new Audio(GAME_MUSIC_URL || '');
  gameAudio.loop = true; gameAudio.volume = 0.55;

  // small WebAudio SFX
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq,d=0.05){ try{{ const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.frequency.value=freq; o.connect(g); g.connect(audioCtx.destination); g.gain.setValueAtTime(0.12,audioCtx.currentTime); o.start(); o.stop(audioCtx.currentTime+d); }}catch(e){{}} }
  function flapSnd(){ beep(880,0.05); }
  function scoreSnd(){ beep(1200,0.06); setTimeout(()=>beep(1500,0.04),60); }
  function hitSnd(){ beep(180,0.12); }

  // try to autoplay homeAudio (may be blocked)
  let homeAudioAllowed = false;
  function tryPlayHomeAuto(){ 
    if(!homeAudio.src) return;
    homeAudio.play().then(()=>{{ homeAudioAllowed=true; }}).catch(()=>{{ homeAudioAllowed=false; }});
  }
  // attempt right away
  tryPlayHomeAuto();

  // If Streamlit sidebar "Play Home Music" button clicked, flag will be true and we should force-play
  if (PLAY_HOME_FROM_PY === "true") {{
    // user clicked Streamlit Play Home Music button before, so attempt to play now
    homeAudio.play().catch(()=>{{/* ignored */}});
  }}

  // UI controls
  const muteBtn = document.getElementById('muteBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  muteBtn.addEventListener('click', ()=>{{ homeAudio.muted = !homeAudio.muted; gameAudio.muted = homeAudio.muted; muteBtn.innerText = homeAudio.muted ? 'Unmute' : 'Mute'; }});
  pauseBtn.addEventListener('click', ()=>{{ if(!homeAudio.paused) {{ homeAudio.pause(); pauseBtn.innerText='Resume'; }} else {{ homeAudio.play().catch(()=>{{}}); pauseBtn.innerText='Pause'; }} }});

  // Game state (same minimal game as before)
  let playing=false, paused=false;
  let lastTs=null, elapsedMs=0;
  let bird = {{ x:120, y:H/2, vel:0, w:40, h:30 }};
  let pipes = [];
  let spawnTimer=0;
  let score=0, best=0;
  try{{ best = parseInt(localStorage.getItem('best_flappy')||'0'); }}catch(e){{ best=0; }}
  document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`;

  // small difficulty params
  const params = {{
    pipeFreq: 1800, speed: 2.0, gap: 160, gravity: 0.45, lift: -9
  }};
  let runtime = Object.assign({{}}, params);

  function updateScoreUI(){ document.getElementById('scoreDisplay').innerText = `Score: ${score} | Best: ${best}`; }
  function resetGame(){ bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; elapsedMs = 0; lastTs = null; updateScoreUI(); }

  // input
  function flap(){ bird.vel = runtime.lift; flapSnd(); }
  window.addEventListener('keydown', e => {{ if(e.code === 'Space') flap(); }});
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', e => {{ e.preventDefault(); flap(); }}, {{passive:false}});
  document.getElementById('tapBtn').addEventListener('click', () => {{ flap(); }});

  // countdown overlay
  const countOverlay = document.getElementById('countOverlay');
  const countVal = document.getElementById('countVal');
  function startCountdown(sec=3) {{
    countOverlay.style.visibility = 'visible';
    let n = sec; countVal.innerText = n;
    const tick = () => {{
      n--;
      if (n >= 1) {{
        countVal.innerText = n;
        // small tick sound
        beep(800, 0.04);
        setTimeout(tick, 1000);
      }} else {{
        countOverlay.style.visibility = 'hidden';
        startGame();
      }}
    }};
    setTimeout(tick, 1000);
  }}

  // starting the game
  function startGame(){ 
    // stop home audio, start game audio
    try{{ homeAudio.pause(); }}catch(e){{}}
    try{{ gameAudio.play().catch(()=>{{}}); }}catch(e){{}}
    playing = true; paused = false; resetGame(); requestAnimationFrame(loop);
  }

  function loop(ts){ 
    if(!lastTs) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;
    if(!paused){
      elapsedMs += dt;
      bird.vel += runtime.gravity;
      bird.y += bird.vel;

      spawnTimer += dt;
      if(spawnTimer > runtime.pipeFreq){
        spawnTimer = 0;
        const gap = Math.max(80, runtime.gap - Math.min(score*0.5, 60));
        const top = 60 + Math.random() * (H - 260);
        pipes.push({ x: W + 40, top: top, gap: gap });
      }

      for(let i=pipes.length-1;i>=0;i--){
        pipes[i].x -= runtime.speed + Math.min(score/100, 2.0);
        if(!pipes[i].scored && pipes[i].x + 60 < bird.x){ score++; pipes[i].scored = true; if(score > best){ best = score; try{{ localStorage.setItem('best_flappy', String(best)); }}catch(e){{}} } updateScoreUI(); }
        if(pipes[i].x < -120) pipes.splice(i,1);
      }

      // collisions
      let dead=false;
      if(bird.y - bird.h/2 < 0 || bird.y + bird.h/2 > H) dead = true;
      for(const p of pipes){
        const pw = 60;
        if(bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){
          if(bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){
            dead = true; break;
          }
        }
      }
      if(dead){ playing = false; try{{ gameAudio.pause(); }}catch(e){{}} hitSnd(); try{{ let s = JSON.parse(localStorage.getItem('scores_local')||'{{"scores":[]}}'); s.scores.push(score); localStorage.setItem('scores_local', JSON.stringify(s)); }}catch(e){{}} try{{ localStorage.setItem('best_flappy', String(best)); }}catch(e){{}} }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    if(BG_URL){ try{{ ctx.drawImage(bgImg, 0, 0, W, H); }}catch(e){{ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }} } else {{ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }}

    // draw pipes (simple green for speed)
    ctx.fillStyle = '#2d8f39';
    for(const p of pipes){ ctx.fillRect(p.x, 0, 60, p.top); ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap)); }

    // draw bird (player upload if present)
    if(PLAYER_URL && playerImg && playerImg.complete && playerImg.src){ try{{ ctx.save(); const rot = Math.max(-0.7, Math.min(0.7, bird.vel / 12)); ctx.translate(bird.x, bird.y); ctx.rotate(rot); ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h); ctx.restore(); }}catch(e){{ ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill(); }} } else {{ ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill(); } }

    if(playing) requestAnimationFrame(loop);
  }

  // responsive
  function resizeCanvas(){ const containerW = Math.min(window.innerWidth - 40, 900); const containerH = Math.min(window.innerHeight - 140, 700); const ratio = 3/2; let cw = containerW, ch = Math.round(cw / ratio); if(ch > containerH){ ch = containerH; cw = Math.round(ch * ratio); } canvas.width = cw; canvas.height = ch; W = canvas.width; H = canvas.height; }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // if Streamlit Start clicked, run countdown (StartFromPy true)
  if (START_FROM_PY === "true") {{
    // if homeAudio is playing, we will stop it at startGame()
    startCountdown(3);
  }}

  // if Streamlit Play Home Music clicked (fallback), try play now
  if (PLAY_HOME_FROM_PY === "true") {{
    homeAudio.play().catch(()=>{{}});
  }} else {{
    // otherwise, if autoplay failed earlier, show a visible small toast/button
    // We'll create a temporary overlay button so user can allow home music easily.
    setTimeout(()=>{{
      if (!homeAudioAllowed) {{
        // create a simple floating "Play Home Music" button
        const btn = document.createElement('button');
        btn.innerText = 'Play Home Music';
        btn.style.position='absolute';
        btn.style.left='12px';
        btn.style.bottom='12px';
        btn.style.zIndex='80';
        btn.style.padding='8px 12px';
        btn.style.borderRadius='8px';
        btn.style.background='rgba(0,0,0,0.6)';
        btn.style.color='white';
        btn.onclick = ()=>{{ homeAudio.play().catch(()=>{{}}); btn.remove(); }};
        document.body.appendChild(btn);
      }}
    }}, 900);
  }}

  // expose helper to get local scores for manual save
  window._getLocalScores = function(){{ try{{ return JSON.parse(localStorage.getItem('scores_local')||'{{"scores":[]}}'); }}catch(e){{ return {{scores:[]}}; }} }};

})();
</script>
</body></html>
"""

# safe injection
injected = game_html
injected = injected.replace("{bg_json}", json.dumps(bg_url))  # not used but safe
injected = injected.replace("{bg}", json.dumps(bg_url))
injected = injected.replace("{home}", json.dumps(home_music_url))
injected = injected.replace("{game}", json.dumps(game_music_url))
injected = injected.replace("{player}", json.dumps(player_data_url))
injected = injected.replace("{start_flag}", "true" if start_clicked else "false")
# We passed start and play flags earlier in formatted strings; but to keep simple we reassign directly below:
injected = injected.replace("{start_flag}", "true" if start_clicked else "false")
# Final replace of placeholders used in template:
injected = injected.replace("{bg_json}", json.dumps(bg_url))
injected = injected.replace("{home_music_json}", json.dumps(home_music_url))
injected = injected.replace("{game_music_json}", json.dumps(game_music_url))

# For simplicity, directly replace the JS placeholders we used:
injected = injected.replace("{bg_json}", json.dumps(bg_url))
injected = injected.replace("HOME_MUSIC_URL = {home_music_json};", f"HOME_MUSIC_URL = {json.dumps(home_music_url)};")
injected = injected.replace("GAME_MUSIC_URL = {game_music_json};", f"GAME_MUSIC_URL = {json.dumps(game_music_url)};")
# But because template already used f-string injection earlier, we will build final by formatting:
final_html = injected.format(bg=json.dumps(bg_url), music=json.dumps(home_music_url),
                              game=json.dumps(game_music_url), player=json.dumps(player_data_url),
                              start="true" if start_clicked else "false",
                              play="true" if play_home_music_clicked else "false")

# Render the HTML game
html(final_html, height=760, scrolling=True)

# ------ Server-side score save helper (manual copy-paste from browser localStorage) ------
st.markdown("---")
st.write("If you want to save your last score to server `scores.json`: open browser console after finishing a run and run `copy(window._getLocalScores())`. Paste the copied JSON here and press Save.")
paste_area = st.text_area("Paste copied JSON (or just paste integer score):", height=140)
if st.button("Save pasted score to server"):
    if not paste_area.strip():
        st.error("Paste something first.")
    else:
        try:
            obj = json.loads(paste_area)
            if isinstance(obj, dict) and "scores" in obj and obj["scores"]:
                last = int(obj["scores"][-1])
                # save locally
                p = Path("scores.json")
                s = {"best": 0, "history": []}
                if p.exists():
                    try:
                        s = json.loads(p.read_text(encoding="utf8"))
                    except:
                        s = {"best":0,"history":[]}
                if last > s.get("best",0):
                    s["best"] = last
                s.setdefault("history",[]).append({"score": last, "time": int(time.time())})
                try:
                    p.write_text(json.dumps(s, indent=2), encoding="utf8")
                    st.success(f"Saved score {last} to scores.json")
                except Exception as e:
                    st.error("Failed to write file on server: " + str(e))
            else:
                # maybe integer
                try:
                    val = int(paste_area.strip())
                    p = Path("scores.json")
                    s = {"best":0,"history":[]}
                    if p.exists():
                        try:
                            s = json.loads(p.read_text(encoding="utf8"))
                        except:
                            s = {"best":0,"history":[]}
                    if val > s.get("best",0):
                        s["best"]=val
                    s.setdefault("history",[]).append({"score": val, "time": int(time.time())})
                    p.write_text(json.dumps(s, indent=2), encoding="utf8")
                    st.success(f"Saved score {val} to scores.json")
                except:
                    st.error("Couldn't parse pasted content. Paste the JSON from browser console or a number.")
