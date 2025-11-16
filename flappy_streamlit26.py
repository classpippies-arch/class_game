# flappy_home_music_switch.py
"""
Flappy — Home music (fixed) on menu, switch to user-selected in-game music when Play starts.
Safe JS injection: NO f-strings used for JS (avoids `{}` parsing errors).
Place this file in repo root with your mp3s & optional background image.
"""

import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, time

st.set_page_config(page_title="Flappy — Home Music Switch (Safe)", layout="wide")
st.title("Flappy — Home Music on Menu, Switch to Selected Music on Start (Safe JS)")
st.write("Home music tries to autoplay on menu (browser may block). On Start, home music stops and selected in-game music plays.")

# --------- CONFIG ----------
BG_NAME = "ChatGPT Image Nov 16, 2025, 01_12_16 PM.png"
HOME_MUSIC_NAME = "audioblocks-mind-game-or-quiz-tension-back.mp3"  # change if your filename differs

# --------- helpers ----------
def list_mp3s():
    root = Path(".")
    mp3s = []
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix.lower() in (".mp3", ".ogg"):
            mp3s.append(f.name)
    return mp3s

def file_to_data_url(p: Path):
    b = p.read_bytes()
    ext = p.suffix.lower()
    if ext == ".mp3":
        mime = "audio/mpeg"
    elif ext == ".ogg":
        mime = "audio/ogg"
    elif ext == ".png":
        mime = "image/png"
    elif ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

# --------- check mp3s ----------
mp3_files = list_mp3s()
if not mp3_files:
    st.error("No .mp3 files found in repo root. Add at least one mp3 and reload.")
    st.stop()

# fallback if HOME_MUSIC not present
if not Path(HOME_MUSIC_NAME).exists():
    HOME_MUSIC_NAME = mp3_files[0]

# --------- Sidebar ----------
st.sidebar.header("Game Music (choose for in-game)")
game_music_selected = st.sidebar.selectbox("Select in-game music (from repo)", mp3_files, index=0)

st.sidebar.header("Player sprite (optional)")
player_file = st.sidebar.file_uploader("Upload player image (png/jpg) — optional", type=["png","jpg","jpeg"])
player_data_url = ""
if player_file is not None:
    data = player_file.read()
    mime = player_file.type if hasattr(player_file, "type") else "image/png"
    player_data_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")

# background data URL (visual only)
bg_url = ""
if Path(BG_NAME).exists():
    bg_url = file_to_data_url(Path(BG_NAME))

# music URLs
home_music_url = file_to_data_url(Path(HOME_MUSIC_NAME))
game_music_url = file_to_data_url(Path(game_music_selected)) if Path(game_music_selected).exists() else home_music_url

# buttons
start_clicked = st.button("Start Game (3..2..1)")
play_home_clicked = st.button("Play Home Music (if silent)")

# --------- Safe HTML/JS template with placeholders (NO Python f-strings inside JS) ----------
html_template = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flappy - Home Music Switch (Safe)</title>
<style>
  html,body{margin:0;height:100%;font-family:system-ui;background:#111;color:#fff}
  #wrap{position:relative;height:100vh;display:flex;align-items:center;justify-content:center}
  canvas{border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.6)}
  #uiTop{position:absolute;top:8px;left:8px;z-index:40}
  #controls{position:absolute;top:8px;right:8px;z-index:40;display:flex;gap:8px}
  .btn{padding:8px 12px;border-radius:10px;background:rgba(0,0,0,0.45);color:white;border:1px solid rgba(255,255,255,0.06);cursor:pointer}
  #countOverlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:60;background:rgba(0,0,0,0.6);visibility:hidden}
  #countVal{font-size:120px;font-weight:900;color:white;text-shadow:0 6px 18px rgba(0,0,0,0.8)}
  #tapBtn{position:absolute;right:14px;bottom:26px;z-index:58;padding:14px 18px;font-size:18px;border-radius:12px}
  @media (max-width:600px){ #countVal{font-size:72px} canvas{width:calc(100vw - 20px)!important;height:calc((100vw - 20px)*2/3)!important} #tapBtn{right:12px;bottom:18px;padding:12px 16px;font-size:16px} }
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
(function(){
  // --- injected placeholders ---
  const BG_URL = %%BG%%;
  const HOME_MUSIC_URL = %%HOME%%;
  const GAME_MUSIC_URL = %%GAME%%;
  const PLAYER_URL = %%PLAYER%%;
  const START_FROM_PY = %%START%%;
  const PLAY_HOME_FROM_PY = %%PLAY%%;

  // canvas
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // images
  const bgImg = new Image();
  if (BG_URL) bgImg.src = BG_URL;
  const playerImg = new Image();
  if (PLAYER_URL) playerImg.src = PLAYER_URL;

  // audio objects
  const homeAudio = new Audio(HOME_MUSIC_URL || '');
  homeAudio.loop = true; homeAudio.volume = 0.55;
  const gameAudio = new Audio(GAME_MUSIC_URL || '');
  gameAudio.loop = true; gameAudio.volume = 0.55;

  // WebAudio SFX - beep/flap/score/hit (pure JS)
  var audioCtx = null;
  try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e) { audioCtx = null; }
  function beep(freq, d){
    if(!audioCtx) return;
    try {
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.frequency.value = freq;
      o.type = 'sine';
      g.gain.setValueAtTime(0.12, audioCtx.currentTime);
      o.connect(g);
      g.connect(audioCtx.destination);
      o.start();
      o.stop(audioCtx.currentTime + d);
    } catch(e){}
  }
  function flapSnd(){ beep(880, 0.05); }
  function scoreSnd(){ beep(1200, 0.06); setTimeout(()=>beep(1500,0.04),60); }
  function hitSnd(){ beep(180, 0.12); }

  // try autoplay home audio (may be blocked)
  let homeAudioAllowed = false;
  function tryPlayHomeAuto(){
    if(!homeAudio.src) return;
    homeAudio.play().then(()=>{ homeAudioAllowed = true; }).catch(()=>{ homeAudioAllowed = false; });
  }
  tryPlayHomeAuto();

  // respond to streamlit-side "Play Home Music" click
  if(PLAY_HOME_FROM_PY === true){
    homeAudio.play().catch(()=>{});
  }

  // UI buttons
  const muteBtn = document.getElementById('muteBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  muteBtn.addEventListener('click', function(){ homeAudio.muted = !homeAudio.muted; gameAudio.muted = homeAudio.muted; muteBtn.innerText = homeAudio.muted ? 'Unmute' : 'Mute'; });
  pauseBtn.addEventListener('click', function(){ if(!homeAudio.paused){ homeAudio.pause(); pauseBtn.innerText = 'Resume'; } else { homeAudio.play().catch(()=>{}); pauseBtn.innerText = 'Pause'; } });

  // game state
  let playing=false, paused=false;
  let lastTs=null, elapsedMs=0;
  let bird = { x:120, y: H/2, vel:0, w:40, h:30 };
  let pipes = [];
  let spawnTimer = 0;
  let score = 0, best = 0;
  try{ best = parseInt(localStorage.getItem('best_flappy')||'0'); }catch(e){ best = 0; }
  document.getElementById('scoreDisplay').innerText = 'Score: ' + score + ' | Best: ' + best;

  // simple difficulty params
  const params = { pipeFreq: 1800, speed: 2.0, gap: 160, gravity: 0.45, lift: -9 };
  let runtime = Object.assign({}, params);

  function updateScoreUI(){ document.getElementById('scoreDisplay').innerText = 'Score: ' + score + ' | Best: ' + best; }
  function resetGame(){ bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; elapsedMs = 0; lastTs = null; updateScoreUI(); }

  // input
  function flap(){ bird.vel = runtime.lift; flapSnd(); }
  window.addEventListener('keydown', function(e){ if(e.code === 'Space') flap(); });
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', function(e){ e.preventDefault(); flap(); }, {passive:false});
  document.getElementById('tapBtn').addEventListener('click', function(){ flap(); });

  // countdown
  const overlay = document.getElementById('countOverlay');
  const countVal = document.getElementById('countVal');
  function startCountdown(sec){
    overlay.style.visibility = 'visible';
    let n = sec; countVal.innerText = n;
    function tick(){
      n--;
      if(n >= 1){
        countVal.innerText = n;
        beep(800, 0.04);
        setTimeout(tick, 1000);
      } else {
        overlay.style.visibility = 'hidden';
        startGame();
      }
    }
    setTimeout(tick, 1000);
  }

  function startGame(){
    try{ homeAudio.pause(); }catch(e){}
    try{ gameAudio.play().catch(()=>{}); }catch(e){}
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
        const gap = Math.max(80, runtime.gap - Math.min(score*0.5,60));
        const top = 60 + Math.random() * (H - 260);
        pipes.push({ x: W + 40, top: top, gap: gap });
      }

      for(let i = pipes.length-1; i >= 0; i--){
        pipes[i].x -= runtime.speed + Math.min(score/100, 2.0);
        if(!pipes[i].scored && pipes[i].x + 60 < bird.x){
          score++; pipes[i].scored = true;
          scoreSnd();
          if(score > best){ best = score; try{ localStorage.setItem('best_flappy', String(best)); }catch(e){} }
          updateScoreUI();
        }
        if(pipes[i].x < -120) pipes.splice(i,1);
      }

      // collisions
      let dead = false;
      if(bird.y - bird.h/2 < 0 || bird.y + bird.h/2 > H) dead = true;
      for(const p of pipes){
        const pw = 60;
        if(bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){
          if(bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){
            dead = true; break;
          }
        }
      }
      if(dead){
        playing = false;
        try{ gameAudio.pause(); }catch(e){}
        hitSnd();
        try{ let s = JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); s.scores.push(score); localStorage.setItem('scores_local', JSON.stringify(s)); }catch(e){}
        try{ localStorage.setItem('best_flappy', String(best)); }catch(e){}
      }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    if(BG_URL){
      try{ ctx.drawImage(bgImg, 0, 0, W, H); }catch(e){ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }
    } else {
      ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H);
    }

    // pipes
    ctx.fillStyle = '#2d8f39';
    for(const p of pipes){ ctx.fillRect(p.x, 0, 60, p.top); ctx.fillRect(p.x, p.top + p.gap, 60, H - (p.top + p.gap)); }

    // bird / player
    if(PLAYER_URL && playerImg && playerImg.complete && playerImg.src){
      try{
        ctx.save();
        const rot = Math.max(-0.7, Math.min(0.7, bird.vel / 12));
        ctx.translate(bird.x, bird.y); ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      }catch(e){
        ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill();
      }
    } else {
      ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x,bird.y,18,14,0,0,Math.PI*2); ctx.fill();
    }

    if(playing) requestAnimationFrame(loop);
  }

  // responsive
  function resizeCanvas(){
    const containerW = Math.min(window.innerWidth - 40, 900);
    const containerH = Math.min(window.innerHeight - 140, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if(ch > containerH){ ch = containerH; cw = Math.round(ch * ratio); }
    canvas.width = cw; canvas.height = ch;
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // start if python button clicked
  if(START_FROM_PY === true){
    startCountdown(3);
  }

  // if Play Home Music clicked from Python sidebar
  if(PLAY_HOME_FROM_PY === true){
    homeAudio.play().catch(()=>{});
  } else {
    setTimeout(function(){
      if(!homeAudioAllowed){
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
        btn.onclick = function(){ homeAudio.play().catch(()=>{}); this.remove(); };
        document.body.appendChild(btn);
      }
    }, 900);
  }

  // helper for copying scores to server
  window._getLocalScores = function(){ try{ return JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); }catch(e){ return {scores:[]}; } };

})();
</script>
</body>
</html>
"""

# --------- safe replacements (use json.dumps so strings are quoted correctly) ----------
final_html = html_template
final_html = final_html.replace("%%BG%%", json.dumps(bg_url))
final_html = final_html.replace("%%HOME%%", json.dumps(home_music_url))
final_html = final_html.replace("%%GAME%%", json.dumps(game_music_url))
final_html = final_html.replace("%%PLAYER%%", json.dumps(player_data_url))
final_html = final_html.replace("%%START%%", "true" if start_clicked else "false")
final_html = final_html.replace("%%PLAY%%", "true" if play_home_clicked else "false")

# Render
html(final_html, height=760, scrolling=True)

# ---------- server-side save helper ----------
st.markdown("---")
st.write("After a run, open browser console and run `copy(window._getLocalScores())`. Paste the JSON here and press Save to store best on server (best-effort).")
paste_area = st.text_area("Paste copied JSON (or paste an integer score):", height=140)
if st.button("Save pasted score to server"):
    if not paste_area.strip():
        st.error("Paste something first.")
    else:
        try:
            obj = json.loads(paste_area)
            if isinstance(obj, dict) and "scores" in obj and obj["scores"]:
                last = int(obj["scores"][-1])
                p = Path("scores.json")
                s = {"best":0,"history":[]}
                if p.exists():
                    try:
                        s = json.loads(p.read_text(encoding="utf8"))
                    except:
                        s = {"best":0,"history":[]}
                if last > s.get("best",0): s["best"] = last
                s.setdefault("history",[]).append({"score": last, "time": int(time.time())})
                try:
                    p.write_text(json.dumps(s, indent=2), encoding="utf8")
                    st.success(f"Saved score {last} to scores.json")
                except Exception as e:
                    st.error("Failed to write file on server: " + str(e))
            else:
                val = int(paste_area.strip())
                p = Path("scores.json")
                s = {"best":0,"history":[]}
                if p.exists():
                    try:
                        s = json.loads(p.read_text(encoding="utf8"))
                    except:
                        s = {"best":0,"history":[]}
                if val > s.get("best",0): s["best"] = val
                s.setdefault("history",[]).append({"score": val, "time": int(time.time())})
                p.write_text(json.dumps(s, indent=2), encoding="utf8")
                st.success(f"Saved score {val} to scores.json")
        except Exception as e:
            st.error("Couldn't parse pasted content. Paste JSON from browser console or a number. Error: " + str(e))
