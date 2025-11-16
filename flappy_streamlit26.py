# flappy_streamlit26_fixed.py
"""
Fixed single-file Streamlit Flappy app.
- No f-strings around HTML/JS to avoid { } parsing issues.
- JS/HTML placed in a raw template with placeholders %%NAME%% replaced safely.
- Supports uploads for images & audio, fallback to repo files if present.
- Mobile-friendly canvas, countdown, music switching (menu -> in-game -> gameover).
"""

import streamlit as st
from streamlit.components.v1 import html
from pathlib import Path
import base64, json, os, time

st.set_page_config(page_title="Premium Flappy Bird (Fixed)", layout="wide", page_icon="🐦")
st.markdown("""
<style>
/* minimal page spacing so the embedded html sits nicely */
.block-container{ padding-top: 8px; padding-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# --------- UI / Premium sidebar (keeps your original inputs) ----------
st.markdown('<div style="text-align:center"><h1>🎮 Premium Flappy Bird</h1><p style="color:gray">Customize visuals & audio — safe JS injection</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎨 Visual Assets")
    up_bg = st.file_uploader("🌅 Background (png/jpg)", type=["png","jpg","jpeg"], key="bg")
    up_player = st.file_uploader("🐦 Player sprite (png/jpg)", type=["png","jpg","jpeg"], key="player")
    up_pipe = st.file_uploader("🛑 Pipe/Obstacle sprite (png/jpg)", type=["png","jpg","jpeg"], key="pipe")
    up_bag = st.file_uploader("💼 Bag / accessory (png/jpg) optional", type=["png","jpg","jpeg"], key="bag")

    st.markdown("### 🎵 Audio (Menu / In-game / Gameover)")
    up_menu_music = st.file_uploader("🏠 Menu Music (mp3/ogg/wav)", type=["mp3","ogg","wav"], key="menu_music")
    up_ingame_music = st.file_uploader("🎮 In-Game Music (mp3/ogg/wav)", type=["mp3","ogg","wav"], key="ingame_music")
    up_gameover_music = st.file_uploader("💀 Game Over Music (mp3/ogg/wav)", type=["mp3","ogg","wav"], key="gameover_music")

    st.markdown("### 🔊 Sound Effects")
    up_start_effect = st.file_uploader("🚀 Start Effect", type=["mp3","ogg","wav"], key="start_eff")
    up_countdown_effect = st.file_uploader("⏱ Countdown Effect", type=["mp3","ogg","wav"], key="count_eff")
    up_jump_effect = st.file_uploader("🦅 Jump Effect", type=["mp3","ogg","wav"], key="jump_eff")
    up_score_effect = st.file_uploader("⭐ Score Effect", type=["mp3","ogg","wav"], key="score_eff")
    up_highscore_effect = st.file_uploader("🏆 High Score Effect", type=["mp3","ogg","wav"], key="hscore_eff")
    up_elim_effect = st.file_uploader("💥 Elimination Effect", type=["mp3","ogg","wav"], key="elim_eff")

    st.markdown("### ⚙️ Game Settings")
    col1, col2 = st.columns(2)
    with col1:
        game_speed = st.slider("Speed", 1, 10, 3)
        gravity_strength = st.slider("Gravity (0.1-1.0)", 0.1, 1.0, 0.45, step=0.05)
    with col2:
        jump_power = st.slider("Jump Power", 5, 20, 12)
        pipe_gap = st.slider("Pipe Gap", 120, 240, 160)

    st.markdown("---")
    st.write("Home music will try to autoplay on menu (browser may block). Use 'Play Home Music' if silent.")
    play_home_button = st.button("Play Home Music (unlock audio)")

# --------- helper: convert uploaded file or repo file to data URL ----------
def fileobj_to_data_url(fileobj, fallback_path=None):
    """Return data URL for uploaded fileobj or fallback_path if provided and exists."""
    try:
        if fileobj is not None:
            raw = fileobj.read()
            name = getattr(fileobj, "name", "").lower()
            if name.endswith(".png"):
                mime = "image/png"
            elif name.endswith(".jpg") or name.endswith(".jpeg"):
                mime = "image/jpeg"
            elif name.endswith(".mp3"):
                mime = "audio/mpeg"
            elif name.endswith(".ogg"):
                mime = "audio/ogg"
            elif name.endswith(".wav"):
                mime = "audio/wav"
            else:
                mime = "application/octet-stream"
            return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
    except Exception:
        pass

    if fallback_path:
        try:
            p = Path(fallback_path)
            if p.exists():
                raw = p.read_bytes()
                ext = p.suffix.lower().lstrip(".")
                mime = "application/octet-stream"
                if ext == "png": mime = "image/png"
                elif ext in ("jpg","jpeg"): mime = "image/jpeg"
                elif ext == "mp3": mime = "audio/mpeg"
                elif ext == "ogg": mime = "audio/ogg"
                elif ext == "wav": mime = "audio/wav"
                return f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
        except Exception:
            pass
    return ""

# --------- fallback repo filenames (if you have files committed to repo) ----------
# update these names if you committed specific files to the repository
REPO_BG = "Screenshot 2025-11-16 131426.png"
REPO_PLAYER = "game ke andar Jis chij Se Bachana hai.jpg"
REPO_PIPE = "game_pipe.png"   # optional repo file name
REPO_BAG = "player_bag.png"

REPO_MENU_MUSIC = "audioblocks-mind-game-or-quiz-tension-back.mp3"
REPO_INGAME_MUSIC = "miaw-miaw-miaw-song-sad-lyrics-video-visual_XBvfuPbJ.mp3"
REPO_GAMEOVER_MUSIC = "doraemon-title-song-in-tamil_L76vcUzg.mp3"

# --------- get data URLs for assets (uploaded or repo fallback) ----------
BG_URL = fileobj_to_data_url(up_bg, REPO_BG) or ""
PLAYER_URL = fileobj_to_data_url(up_player, REPO_PLAYER) or ""
PIPE_URL = fileobj_to_data_url(up_pipe, REPO_PIPE) or ""
BAG_URL = fileobj_to_data_url(up_bag, REPO_BAG) or ""

MENU_MUSIC_URL = fileobj_to_data_url(up_menu_music, REPO_MENU_MUSIC) or ""
INGAME_MUSIC_URL = fileobj_to_data_url(up_ingame_music, REPO_INGAME_MUSIC) or ""
GAMEOVER_MUSIC_URL = fileobj_to_data_url(up_gameover_music, REPO_GAMEOVER_MUSIC) or ""

START_EFFECT_URL = fileobj_to_data_url(up_start_effect)
COUNTDOWN_EFFECT_URL = fileobj_to_data_url(up_countdown_effect)
JUMP_EFFECT_URL = fileobj_to_data_url(up_jump_effect)
SCORE_EFFECT_URL = fileobj_to_data_url(up_score_effect)
HIGHSCORE_EFFECT_URL = fileobj_to_data_url(up_highscore_effect)
ELIM_EFFECT_URL = fileobj_to_data_url(up_elim_effect)

# --------- Start trigger (button on main area) ----------
start_clicked = st.button("Start Game (3..2..1)")

# --------- Safe HTML/JS template (raw string, NO f-string) ----------
html_template = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Premium Flappy Bird (embedded)</title>
<style>
/* compact styles for the embedded game area */
html,body{margin:0;height:100%;font-family:system-ui;background:#0f1724;color:#fff}
#wrap{position:relative;height:80vh;display:flex;align-items:center;justify-content:center;padding:20px}
canvas{border-radius:12px;box-shadow:0 12px 40px rgba(2,6,23,0.8);background:#7fc8ff}
.ui-top{position:absolute;top:12px;left:12px;right:12px;display:flex;justify-content:space-between;pointer-events:none;z-index:20}
.ui-top .left,.ui-top .right{pointer-events:auto}
.btn{background:rgba(0,0,0,0.35);color:white;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);cursor:pointer}
.count-overlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:40;pointer-events:none}
.count-overlay .val{font-size:120px;font-weight:900;color:white;text-shadow:0 6px 18px rgba(0,0,0,0.8)}
#tapBtn{position:absolute;right:16px;bottom:24px;z-index:30;padding:12px 14px;border-radius:10px;background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.06);cursor:pointer}
.audio-toast{position:absolute;left:16px;bottom:24px;z-index:30;background:rgba(0,0,0,0.5);padding:8px 12px;border-radius:8px}
@media (max-width:600px){ .count-overlay .val{font-size:64px} canvas{width:calc(100vw - 28px)!important;height:calc((100vw - 28px)*2/3)!important} }
</style>
</head>
<body>
<div id="wrap">
  <div class="ui-top">
    <div class="left"><span id="scoreDisplay" style="font-weight:700;font-size:18px;padding:6px 10px;border-radius:8px;background:rgba(0,0,0,0.35)">Score: 0</span></div>
    <div class="right"><button id="startPauseBtn" class="btn">Start</button> <button id="muteBtn" class="btn">Mute</button></div>
  </div>

  <div class="count-overlay" id="countOverlay" style="visibility:hidden"><div class="val" id="countVal">3</div></div>
  <canvas id="gameCanvas" width="720" height="480"></canvas>
  <button id="tapBtn">TAP</button>
  <div class="audio-toast" id="audioToast" style="display:none">🔊 Menu Music</div>
</div>

<script>
(function(){
  // placeholders replaced server-side
  const BG_URL = %%BG%%;
  const PLAYER_URL = %%PLAYER%%;
  const PIPE_URL = %%PIPE%%;
  const BAG_URL = %%BAG%%;

  const MENU_MUSIC_URL = %%MENU%%;
  const INGAME_MUSIC_URL = %%INGAME%%;
  const GAMEOVER_MUSIC_URL = %%GAMEOVER%%;

  const START_EFFECT_URL = %%STARTEFF%%;
  const COUNTDOWN_EFFECT_URL = %%COUNTEFF%%;
  const JUMP_EFFECT_URL = %%JUMP%%;
  const SCORE_EFFECT_URL = %%SCORE%%;
  const HIGHSCORE_EFFECT_URL = %%HIGHSCORE%%;
  const ELIM_EFFECT_URL = %%ELIM%%;

  const CONFIG = {
    SPEED: %%SPEED%%,
    GRAVITY: %%GRAV%%,
    JUMP_POWER: %%JUMP_POW%%,
    PIPE_GAP: %%PIPE_GAP%%
  };

  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // images
  const bgImg = new Image(); if(BG_URL) bgImg.src = BG_URL;
  const playerImg = new Image(); if(PLAYER_URL) playerImg.src = PLAYER_URL;
  const pipeImg = new Image(); if(PIPE_URL) pipeImg.src = PIPE_URL;
  const bagImg = new Image(); if(BAG_URL) bagImg.src = BAG_URL;

  // audio objects
  const homeAudio = MENU_MUSIC_URL ? new Audio(MENU_MUSIC_URL) : null;
  if(homeAudio) { homeAudio.loop = true; homeAudio.volume = 0.5; }
  const ingameAudio = INGAME_MUSIC_URL ? new Audio(INGAME_MUSIC_URL) : null;
  if(ingameAudio) { ingameAudio.loop = true; ingameAudio.volume = 0.5; }
  const gameoverAudio = GAMEOVER_MUSIC_URL ? new Audio(GAMEOVER_MUSIC_URL) : null;
  if(gameoverAudio) { gameoverAudio.volume = 0.6; }

  // effects
  const startEff = START_EFFECT_URL ? new Audio(START_EFFECT_URL) : null;
  const countEff = COUNTDOWN_EFFECT_URL ? new Audio(COUNTDOWN_EFFECT_URL) : null;
  const jumpEff = JUMP_EFFECT_URL ? new Audio(JUMP_EFFECT_URL) : null;
  const scoreEff = SCORE_EFFECT_URL ? new Audio(SCORE_EFFECT_URL) : null;
  const highEff = HIGHSCORE_EFFECT_URL ? new Audio(HIGHSCORE_EFFECT_URL) : null;
  const elimEff = ELIM_EFFECT_URL ? new Audio(ELIM_EFFECT_URL) : null;

  // small beep fallback using WebAudio if available
  let audioCtx = null;
  try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch(e){ audioCtx = null; }
  function beep(f,d){ if(!audioCtx) return; try{ const o=audioCtx.createOscillator(); const g=audioCtx.createGain(); o.type='sine'; o.frequency.value=f; g.gain.setValueAtTime(0.12, audioCtx.currentTime); o.connect(g); g.connect(audioCtx.destination); o.start(); o.stop(audioCtx.currentTime + d); }catch(e){} }

  // state
  let playing=false, paused=false;
  let bird = { x: 120, y: H/2, vel:0, w:48, h:36 };
  let pipes = [], spawnTimer = 0, score = 0, best = 0;
  try{ best = parseInt(localStorage.getItem('flappy_best')||'0'); }catch(e){ best = 0; }
  document.getElementById('scoreDisplay').textContent = `Score: ${score} | Best: ${best}`;

  // start/pause/mute controls
  const startPauseBtn = document.getElementById('startPauseBtn');
  const muteBtn = document.getElementById('muteBtn');
  const tapBtn = document.getElementById('tapBtn');
  const audioToast = document.getElementById('audioToast');
  startPauseBtn.addEventListener('click', ()=>{ if(!playing){ startSequence(); } else { paused = !paused; startPauseBtn.textContent = paused ? 'Resume' : 'Pause'; if(paused){ if(ingameAudio) ingameAudio.pause(); } else { if(ingameAudio) ingameAudio.play().catch(()=>{}); } } });
  muteBtn.addEventListener('click', ()=>{ if(homeAudio) homeAudio.muted = !homeAudio.muted; if(ingameAudio) ingameAudio.muted = homeAudio ? homeAudio.muted : (ingameAudio.muted?false:true); muteBtn.textContent = (homeAudio && homeAudio.muted) ? 'Unmute' : 'Mute'; });

  // input
  window.addEventListener('keydown', (e)=>{ if(e.code==='Space') flap(); });
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', (e)=>{ e.preventDefault(); flap(); }, {passive:false});
  tapBtn.addEventListener('click', flap);

  // helpers
  function updateScoreDisplay(){ document.getElementById('scoreDisplay').textContent = `Score: ${score} | Best: ${best}`; }

  function flap(){ bird.vel = -Math.abs(CONFIG.JUMP_POWER); try{ if(jumpEff){ jumpEff.currentTime = 0; jumpEff.play().catch(()=>{}); } else beep(880,0.05); }catch(e){} }

  function resetGame(){ bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; updateScoreDisplay(); }

  function spawnPipe(){ const gap = CONFIG.PIPE_GAP; const top = 80 + Math.random()*(H - 260); pipes.push({ x: W + 40, top: top, gap: gap, scored:false }); }

  // start sequence with countdown
  function startSequence(){ // show countdown 3..2..1
    document.getElementById('countOverlay').style.visibility = 'visible';
    let n = 3;
    document.getElementById('countVal').textContent = n;
    try{ if(startEff){ startEff.currentTime=0; startEff.play().catch(()=>{}); } }catch(e){}
    const t = setInterval(()=>{ n--; if(n>0){ document.getElementById('countVal').textContent = n; try{ if(countEff){ countEff.currentTime=0; countEff.play().catch(()=>{}); } else beep(800,0.04);}catch(e){} } else { clearInterval(t); document.getElementById('countOverlay').style.visibility='hidden'; startGame(); } }, 1000);
  }

  function startGame(){ playing=true; paused=false; startPauseBtn.textContent='Pause'; resetGame(); if(homeAudio) try{ homeAudio.pause(); }catch(e){} if(ingameAudio) try{ ingameAudio.play().catch(()=>{}); }catch(e){} requestAnimationFrame(loop); audioToast.style.display = 'block'; audioToast.textContent = '🎮 Game Music'; }

  function endGame(){ playing=false; try{ if(ingameAudio) ingameAudio.pause(); if(gameoverAudio) { gameoverAudio.currentTime = 0; gameoverAudio.play().catch(()=>{}); } }catch(e){} if(score>best){ best = score; try{ localStorage.setItem('flappy_best', String(best)); }catch(e){} } updateScoreDisplay(); // show small gameover toast
    audioToast.style.display='block'; audioToast.textContent='💀 Game Over Music';
    try{ if(elimEff){ elimEff.currentTime=0; elimEff.play().catch(()=>{}); } }catch(e){}
  }

  // main loop
  let lastTs = null;
  function loop(ts){
    if(!lastTs) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;

    if(!paused && playing){
      bird.vel += CONFIG.GRAVITY * (dt/16);
      bird.y += bird.vel * (dt/16);

      spawnTimer += dt;
      if(spawnTimer > 1600){ spawnTimer = 0; spawnPipe(); }

      // move pipes
      for(let i=pipes.length-1;i>=0;i--){
        pipes[i].x -= (CONFIG.SPEED + Math.min(score/100,2)) * (dt/16);
        if(!pipes[i].scored && (pipes[i].x + 40) < bird.x){ pipes[i].scored = true; score++; try{ if(score<=5 && scoreEff){ scoreEff.currentTime=0; scoreEff.play().catch(()=>{}); } else if(score>5 && highEff){ highEff.currentTime=0; highEff.play().catch(()=>{}); } }catch(e){} if(score>best){ best = score; try{ localStorage.setItem('flappy_best', String(best)); }catch(e){} } updateScoreDisplay(); }
        if(pipes[i].x < -120) pipes.splice(i,1);
      }

      // collisions
      if(bird.y - bird.h/2 <= 0 || bird.y + bird.h/2 >= H){ endGame(); }

      for(const p of pipes){
        const pw = 60;
        if(bird.x + bird.w/2 > p.x && bird.x - bird.w/2 < p.x + pw){
          if(bird.y - bird.h/2 < p.top || bird.y + bird.h/2 > p.top + p.gap){ endGame(); break; }
        }
      }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    if(BG_URL){
      try{ ctx.drawImage(bgImg, 0, 0, W, H); }catch(e){ ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }
    } else { ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }

    // pipes
    ctx.fillStyle = '#2d8f39';
    for(const p of pipes){
      const pipeW = 60;
      if(PIPE_URL){
        try{ ctx.drawImage(pipeImg, p.x - pipeW/2, 0, pipeW, p.top); }catch(e){ ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top); }
        try{ ctx.drawImage(pipeImg, p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); }catch(e){ ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); }
      } else {
        ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top);
        ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap));
      }
    }

    // bird
    if(PLAYER_URL){
      try{
        ctx.save();
        const rot = Math.max(-0.6, Math.min(0.6, bird.vel / 12));
        ctx.translate(bird.x, bird.y);
        ctx.rotate(rot);
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

  // responsive resize
  function resizeCanvas(){
    const containerW = Math.min(window.innerWidth - 80, 900);
    const containerH = Math.min(window.innerHeight - 200, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if(ch > containerH){ ch = containerH; cw = Math.round(ch * ratio); }
    canvas.width = cw; canvas.height = ch; W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // attempt autoplay menu audio (may be blocked)
  if(homeAudio){
    homeAudio.play().then(()=>{ audioToast.style.display='block'; audioToast.textContent='🔊 Menu Music'; }).catch(()=>{ /* blocked */ });
  }

  // If play-home button was clicked on server side, Streamlit sets value; but since we're embedding we rely on page interaction
  // Expose helper for local save
  window._getLocalScores = function(){ try{ return JSON.parse(localStorage.getItem('scores_local')||'{"scores":[]}'); }catch(e){ return {scores:[]}; } };

})();
</script>
</body>
</html>
"""

# --------- safe replacements ----------
final_html = html_template
# inject JSON-encoded strings to ensure proper quoting
final_html = final_html.replace("%%BG%%", json.dumps(BG_URL))
final_html = final_html.replace("%%PLAYER%%", json.dumps(PLAYER_URL))
final_html = final_html.replace("%%PIPE%%", json.dumps(PIPE_URL))
final_html = final_html.replace("%%BAG%%", json.dumps(BAG_URL))

final_html = final_html.replace("%%MENU%%", json.dumps(MENU_MUSIC_URL))
final_html = final_html.replace("%%INGAME%%", json.dumps(INGAME_MUSIC_URL))
final_html = final_html.replace("%%GAMEOVER%%", json.dumps(GAMEOVER_MUSIC_URL))

final_html = final_html.replace("%%STARTEFF%%", json.dumps(START_EFFECT_URL))
final_html = final_html.replace("%%COUNTEFF%%", json.dumps(COUNTDOWN_EFFECT_URL))
final_html = final_html.replace("%%JUMP%%", json.dumps(JUMP_EFFECT_URL))
final_html = final_html.replace("%%SCORE%%", json.dumps(SCORE_EFFECT_URL))
final_html = final_html.replace("%%HIGHSCORE%%", json.dumps(HIGHSCORE_EFFECT_URL))
final_html = final_html.replace("%%ELIM%%", json.dumps(ELIM_EFFECT_URL))

# numeric settings
final_html = final_html.replace("%%SPEED%%", str(game_speed))
final_html = final_html.replace("%%GRAV%%", str(gravity_strength))
final_html = final_html.replace("%%JUMP_POW%%", str(jump_power))
final_html = final_html.replace("%%PIPE_GAP%%", str(pipe_gap))

# Render the embedded game (height tuned for canvas + UI)
html(final_html, height=760, scrolling=True)

# --------- Server-side manual score save helper (optional) ----------
st.markdown("---")
st.write("If you want to save scores server-side: open browser console after a run and run `copy(window._getLocalScores())`, paste here and Save.")
paste_area = st.text_area("Paste JSON from console or paste integer score:", height=140)
if st.button("Save pasted score to server"):
    if not paste_area.strip():
        st.error("Paste something first.")
    else:
        try:
            obj = json.loads(paste_area)
            if isinstance(obj, dict) and "scores" in obj and obj["scores"]:
                last = int(obj["scores"][-1])
            else:
                last = int(paste_area.strip())
            p = Path("scores.json")
            s = {"best": 0, "history": []}
            if p.exists():
                try:
                    s = json.loads(p.read_text(encoding="utf8"))
                except:
                    s = {"best": 0, "history": []}
            if last > s.get("best", 0):
                s["best"] = last
            s.setdefault("history", []).append({"score": last, "time": int(time.time())})
            p.write_text(json.dumps(s, indent=2), encoding="utf8")
            st.success(f"Saved score {last} to scores.json")
        except Exception as e:
            st.error("Couldn't parse pasted content. Error: " + str(e))
