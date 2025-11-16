# flappy_streamlit_countdown.py
import streamlit as st
from streamlit.components.v1 import html
import base64
import os
import json
import zipfile
from pathlib import Path

st.set_page_config(page_title="Flappy - Streamlit (Countdown + Playlist)", layout="wide")

st.title("Flappy-style Game — Streamlit (3s countdown + playlist)")
st.write("Uploads, default folder and previously uploaded files (in /mnt/data) are auto-included. Press Start → 3..2..1 → Game begins.")

# ---------------------------
# Music folders / detect uploaded files in /mnt/data (if present)
# ---------------------------
DEFAULT_MUSIC_DIR = "./default_music"
os.makedirs(DEFAULT_MUSIC_DIR, exist_ok=True)

# Also check /mnt/data for any mp3/ogg the user may have uploaded in this environment
ALT_UPLOAD_DIR = "/mnt/data"

def list_music_in_dir(d):
    try:
        return sorted([f for f in os.listdir(d) if f.lower().endswith(('.mp3', '.ogg'))])
    except Exception:
        return []

default_files = list_music_in_dir(DEFAULT_MUSIC_DIR)
alt_files = list_music_in_dir(ALT_UPLOAD_DIR) if os.path.exists(ALT_UPLOAD_DIR) else []

# ---------------------------
# Sidebar UI
# ---------------------------
with st.sidebar:
    st.header("Assets & Music")

    st.markdown("**Sprites / Background**")
    player_file = st.file_uploader("Player sprite (image)", type=["png", "jpg", "jpeg"], key="player")
    obstacle_file = st.file_uploader("Obstacle sprite (image)", type=["png", "jpg", "jpeg"], key="obstacle")
    bg_file = st.file_uploader("Background image", type=["png", "jpg", "jpeg"], key="bg")

    st.markdown("---")
    st.markdown("**Playlist sources**")
    st.write(f"Default folder `{DEFAULT_MUSIC_DIR}`: {len(default_files)} files.")
    st.write(f"Detected environment `/mnt/data`: {len(alt_files)} files.")
    st.write("You can upload a single music file (adds to top of playlist) or upload a ZIP to extract into `./default_music/`.")

    uploaded_zip = st.file_uploader("Upload folder as ZIP (optional)", type=["zip"])
    if uploaded_zip is not None:
        try:
            zdata = uploaded_zip.read()
            tmp_zip = "tmp_uploaded_music.zip"
            with open(tmp_zip, "wb") as f:
                f.write(zdata)
            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(DEFAULT_MUSIC_DIR)
            st.success("ZIP extracted to ./default_music")
            # refresh list
            default_files = list_music_in_dir(DEFAULT_MUSIC_DIR)
        except Exception as e:
            st.error(f"Failed to extract ZIP: {e}")

    uploaded_music_single = st.file_uploader("Upload single music (mp3/ogg) — optional", type=["mp3", "ogg"], key="music_single")

    st.markdown("---")
    play_mode = st.selectbox("Play mode", ["Sequential", "Shuffle"])
    auto_advance_on_track_end = st.checkbox("Auto-advance when track ends", value=True)
    auto_advance_on_match_end = st.checkbox("Auto-advance to next track after match (game over)", value=True)

    st.markdown("---")
    minutes = st.number_input("Auto end after (minutes). 0 = no timer", min_value=0, max_value=120, value=0, step=1)
    start_immediately = st.button("START GAME (Streamlit)")

# ---------------------------
# Helpers to convert to data URLs
# ---------------------------
def fileobj_to_data_url(uploaded):
    if uploaded is None:
        return None
    data = uploaded.read()
    mime = uploaded.type if hasattr(uploaded, "type") else "audio/mpeg"
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

def local_file_to_data_url(path):
    # read local path and return data URL
    with open(path, "rb") as fh:
        data = fh.read()
    if path.lower().endswith(".mp3"):
        mime = "audio/mpeg"
    elif path.lower().endswith(".ogg"):
        mime = "audio/ogg"
    else:
        mime = "application/octet-stream"
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

# ---------------------------
# Build playlist: uploaded single (session) -> ./default_music -> /mnt/data detected files
# ---------------------------
playlist_urls = []
playlist_names = []

# 1) uploaded single (if any)
if uploaded_music_single is not None:
    try:
        playlist_urls.append(fileobj_to_data_url(uploaded_music_single))
        playlist_names.append(uploaded_music_single.name)
    except Exception as e:
        st.sidebar.warning(f"Couldn't read uploaded single music: {e}")

# 2) files in default_music folder
for fname in default_files:
    path = os.path.join(DEFAULT_MUSIC_DIR, fname)
    try:
        playlist_urls.append(local_file_to_data_url(path))
        playlist_names.append(fname)
    except Exception as e:
        st.sidebar.warning(f"Can't read {fname}: {e}")

# 3) files found in /mnt/data (these are the ones you uploaded earlier to the environment)
#    we avoid adding duplicates by name
existing_names = set(playlist_names)
for fname in alt_files:
    if fname in existing_names:
        continue
    path = os.path.join(ALT_UPLOAD_DIR, fname)
    try:
        playlist_urls.append(local_file_to_data_url(path))
        playlist_names.append(fname)
    except Exception as e:
        st.sidebar.warning(f"Can't read /mnt/data/{fname}: {e}")

# show playlist summary
st.sidebar.markdown("### Current playlist")
if playlist_names:
    for i, n in enumerate(playlist_names):
        st.sidebar.write(f"{i+1}. {n}")
else:
    st.sidebar.write("Playlist empty — upload files or put mp3/ogg in ./default_music/ or /mnt/data")

# ---------------------------
# Sprites/background urls
# ---------------------------
player_url = fileobj_to_data_url(player_file) or ""
obstacle_url = fileobj_to_data_url(obstacle_file) or ""
bg_url = fileobj_to_data_url(bg_file) or ""

# top-right start button
col1, col2, col3 = st.columns([1, 6, 1])
with col3:
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    start_button_top = st.button("Start / Restart Game", key="top_start")
    st.markdown("</div>", unsafe_allow_html=True)

start_game = start_immediately or start_button_top

# ---------------------------
# JS/HTML game with 3-second countdown overlay
# ---------------------------
game_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flappy - Countdown</title>
  <style>
    html,body { margin:0; height:100%; background:#111; font-family: system-ui, -apple-system, 'Segoe UI', Roboto; color:#fff; }
    #gameArea { display:flex; align-items:center; justify-content:center; height:100vh; }
    canvas { border-radius:12px; box-shadow:0 6px 16px rgba(0,0,0,0.6); background:#88c; }
    .ui-top {
      position:absolute; top:8px; left:8px; right:8px; display:flex; justify-content:space-between; pointer-events:none; z-index:25;
    }
    .ui-top .left, .ui-top .right { pointer-events:auto; }
    .btn { background:rgba(0,0,0,0.35); color:white; padding:6px 10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06); cursor:pointer; }
    #countdownOverlay {
      position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:30;
      background:rgba(0,0,0,0.5); font-weight:700; font-size:120px; color:#fff; visibility:hidden;
    }
    #miniCountdown {
      font-size: 120px;
      line-height: 1;
      text-align: center;
      text-shadow: 0 6px 18px rgba(0,0,0,0.8);
    }
  </style>
</head>
<body>
  <div class="ui-top">
    <div class="left">
      <span id="scoreDisplay" style="font-weight:700; font-size:20px; padding:6px 10px; background:rgba(0,0,0,0.35); border-radius:8px;">Score: 0</span>
    </div>
    <div class="right">
      <button id="startPauseBtn" class="btn">Start</button>
      <button id="muteBtn" class="btn">Mute</button>
      <button id="shareBtn" class="btn">Share</button>
    </div>
  </div>

  <div id="gameArea">
    <canvas id="gameCanvas" width="720" height="480"></canvas>
  </div>

  <div id="countdownOverlay"><div id="miniCountdown">3</div></div>

<script>
(() => {
  // Config injected by Python
  const playlist = __PLAYLIST__;
  const playMode = __PLAYMODE__;
  const autoAdvanceOnTrackEnd = __AUTO_TRACK_END__;
  const autoAdvanceOnMatchEnd = __AUTO_MATCH_END__;
  const timeLimitMinutes = __MINUTES__;
  const startFromPython = __STARTGAME__;
  const playerSrc = __PLAYER_URL__;
  const obstacleSrc = __OBSTACLE_URL__;
  const bgSrc = __BG_URL__;

  // Canvas
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // Images
  const playerImg = new Image();
  const obstacleImg = new Image();
  const bgImg = new Image();
  try { playerImg.src = playerSrc; } catch(e){}
  try { obstacleImg.src = obstacleSrc; } catch(e){}
  try { bgImg.src = bgSrc; } catch(e){}

  // Audio & playlist handling
  let audio = new Audio();
  audio.loop = false;
  audio.volume = 0.5;
  let playlistArr = playlist || []; // {url,name}
  let currentIndex = 0;

  function setTrack(idx) {
    if(!playlistArr.length) return;
    currentIndex = ((idx%playlistArr.length)+playlistArr.length)%playlistArr.length;
    audio.src = playlistArr[currentIndex].url;
    try { audio.play().catch(()=>{}); } catch(e){}
    renderPlaylistUI();
  }
  function nextTrack() {
    if(!playlistArr.length) return;
    if(playMode === "Shuffle") {
      let next = Math.floor(Math.random()*playlistArr.length);
      if(playlistArr.length>1 && next===currentIndex) next = (next+1)%playlistArr.length;
      setTrack(next);
    } else {
      setTrack((currentIndex+1)%playlistArr.length);
    }
  }
  audio.addEventListener('ended', () => { if(autoAdvanceOnTrackEnd) nextTrack(); });

  // Playlist UI (small bottom row)
  const playlistUI = document.createElement('div');
  playlistUI.style.position = 'absolute';
  playlistUI.style.bottom = '10px';
  playlistUI.style.left = '10px';
  playlistUI.style.right = '10px';
  playlistUI.style.display = 'flex';
  playlistUI.style.justifyContent = 'center';
  playlistUI.style.gap = '8px';
  playlistUI.style.zIndex = 26;
  document.body.appendChild(playlistUI);

  function renderPlaylistUI() {
    playlistUI.innerHTML = '';
    playlistArr.forEach((it, i) => {
      const el = document.createElement('div');
      el.innerText = `${i+1}. ${it.name}`;
      el.style.padding = '6px 10px';
      el.style.background = (i===currentIndex) ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.32)';
      el.style.borderRadius = '14px';
      el.style.cursor = 'pointer';
      el.style.fontSize = '13px';
      el.onclick = () => setTrack(i);
      playlistUI.appendChild(el);
    });
  }

  if(playlistArr.length) {
    currentIndex = 0;
    audio.src = playlistArr[0].url;
  }
  renderPlaylistUI();

  // basic game state
  let playing = false, paused = false;
  let gravity = 0.45, lift = -9;
  let bird = {x:100, y: H/2, vel:0, w:48, h:36};
  let pipes = [], spawnTimer=0, score=0, lastTimestamp=null, elapsedMs=0;
  let best = localStorage.getItem('flappy_best') || 0;

  function updateScoreDisplay() {
    document.getElementById('scoreDisplay').textContent = `Score: ${score}  | Best: ${best}`;
  }

  function resetGame() {
    bird.y = H/2; bird.vel = 0; pipes = []; spawnTimer = 0; score = 0; elapsedMs = 0; lastTimestamp = null;
    updateScoreDisplay();
  }

  // inputs
  function flap() { bird.vel = lift; }
  window.addEventListener('keydown', (e)=>{ if(e.code==='Space') flap(); });
  canvas.addEventListener('mousedown', ()=>{ flap(); });
  canvas.addEventListener('touchstart', (e)=>{ e.preventDefault(); flap(); }, {passive:false});

  // start/pause button with countdown
  const startPauseBtn = document.getElementById('startPauseBtn');
  const countdownOverlay = document.getElementById('countdownOverlay');
  const miniCountdown = document.getElementById('miniCountdown');

  startPauseBtn.addEventListener('click', ()=> {
    if(!playing) {
      // Show 3-second countdown, then start
      showCountdownThenStart(3);
    } else {
      paused = !paused;
      startPauseBtn.textContent = paused ? 'Resume' : 'Pause';
      if(paused) audio.pause(); else audio.play().catch(()=>{});
    }
  });

  function showCountdownThenStart(seconds) {
    countdownOverlay.style.visibility = 'visible';
    let n = seconds;
    miniCountdown.innerText = n;
    const tick = () => {
      n -= 1;
      if(n >= 1) {
        miniCountdown.innerText = n;
        setTimeout(tick, 1000);
      } else {
        // hide and start
        countdownOverlay.style.visibility = 'hidden';
        startPlaying();
      }
    };
    // play small beep? (not implemented) — just start countdown
    setTimeout(tick, 1000);
  }

  function startPlaying() {
    playing = true; paused = false;
    startPauseBtn.textContent = 'Pause';
    if(audio.src) audio.play().catch(()=>{});
    resetGame();
    requestAnimationFrame(loop);
  }

  // mute button
  const muteBtn = document.getElementById('muteBtn');
  muteBtn.addEventListener('click', ()=> {
    audio.muted = !audio.muted;
    muteBtn.textContent = audio.muted ? 'Unmute' : 'Mute';
  });

  // share button
  const shareBtn = document.getElementById('shareBtn');
  shareBtn.addEventListener('click', ()=> {
    const text = encodeURIComponent(`I scored ${score} points playing this Flappy-style game!`);
    const url = encodeURIComponent(location.href);
    const tweet = `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
    window.open(tweet, '_blank');
  });

  // game loop
  function loop(ts) {
    if(!lastTimestamp) lastTimestamp = ts;
    const dt = ts - lastTimestamp; lastTimestamp = ts;
    if(!paused) {
      elapsedMs += dt;
      bird.vel += gravity; bird.y += bird.vel;
      spawnTimer += dt;
      if(spawnTimer > 1600) {
        spawnTimer = 0;
        const gap = 140 + Math.random()*60;
        const topH = 80 + Math.random()*(H - 300);
        pipes.push({x: W+20, top: topH, gap});
      }
      for(let i=pipes.length-1;i>=0;i--) {
        pipes[i].x -= 2.6 + Math.min(score/100, 2.0);
        if(!pipes[i].scored && pipes[i].x + 40 < bird.x) {
          score += 1; pipes[i].scored = true;
          if(score > best) { best = score; localStorage.setItem('flappy_best', best); }
          updateScoreDisplay();
        }
        if(pipes[i].x < -80) pipes.splice(i,1);
      }

      // collisions
      let died = false;
      if(bird.y + bird.h/2 >= H || bird.y - bird.h/2 <= 0) died = true;
      for(const p of pipes) {
        const pipeW = 60; const px = p.x, top = p.top, gap = p.gap;
        if(bird.x + bird.w/2 > px - pipeW/2 && bird.x - bird.w/2 < px + pipeW/2) {
          if(bird.y - bird.h/2 < top || bird.y + bird.h/2 > top + gap) { died = true; break; }
        }
      }
      if(died) {
        playing = false;
        // if auto-advance on match end, move to next
        if(__AUTO_MATCH_END__ === true) {
          // advance track in JS context:
          if(playlistArr.length) {
            // next track behavior: follow playMode
            if(playMode === "Shuffle") {
              let next = Math.floor(Math.random()*playlistArr.length);
              if(playlistArr.length>1 && next===currentIndex) next = (next+1)%playlistArr.length;
              currentIndex = next;
            } else {
              currentIndex = (currentIndex+1)%playlistArr.length;
            }
            audio.src = playlistArr[currentIndex].url;
          }
        }
      }

      if(timeLimitMinutes > 0) {
        if(elapsedMs >= timeLimitMinutes * 60 * 1000) playing = false;
      }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    if(bgSrc) {
      try { ctx.drawImage(bgImg,0,0,W,H); } catch(e) { ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }
    } else {
      ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H);
      ctx.fillStyle='rgba(255,255,255,0.6)'; ctx.beginPath(); ctx.ellipse(120,80,40,24,0,0,Math.PI*2); ctx.fill();
    }

    // pipes
    ctx.fillStyle = '#2d8f39';
    for(const p of pipes) {
      const pipeW = 60;
      if(obstacleImg && obstacleImg.complete) {
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, 0, pipeW, p.top); } catch(e) { ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top); }
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); } catch(e) { ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); }
      } else {
        ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top);
        ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap));
      }
    }

    // bird
    if(playerImg && playerImg.complete && playerImg.src) {
      try {
        ctx.save();
        const rot = Math.max(-0.6, Math.min(0.6, bird.vel / 12));
        ctx.translate(bird.x, bird.y); ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      } catch(e) {
        ctx.fillStyle='yellow'; ctx.fillRect(bird.x - bird.w/2, bird.y - bird.h/2, bird.w, bird.h);
      }
    } else {
      ctx.fillStyle='yellow'; ctx.beginPath(); ctx.ellipse(bird.x, bird.y, 18, 14, 0, 0, Math.PI*2); ctx.fill();
    }

    if(!playing) {
      ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.fillRect(0,0,W,H);
      ctx.fillStyle='white'; ctx.textAlign='center'; ctx.font='28px system-ui';
      ctx.fillText('Press Start to Play', W/2, H/2 - 20);
      ctx.font='18px system-ui'; ctx.fillText('Controls: tap / click / spacebar', W/2, H/2 + 10);
      ctx.font='16px system-ui'; ctx.fillText(`Score: ${score}  |  Best: ${best}`, W/2, H/2 + 40);
    }

    if(playing) requestAnimationFrame(loop);
    else {
      if(audio) audio.pause();
      startPauseBtn.textContent = 'Start';
    }
  }

  // responsive
  function resizeCanvas() {
    const containerW = Math.min(window.innerWidth - 100, 900);
    const containerH = Math.min(window.innerHeight - 160, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if(ch > containerH) { ch = containerH; cw = Math.round(ch * ratio); }
    canvas.width = cw; canvas.height = ch; W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // expose small helpers
  window._setTrack = (i) => { if(playlistArr.length) { currentIndex = i%playlistArr.length; audio.src = playlistArr[currentIndex].url; audio.play().catch(()=>{}); renderPlaylistUI(); } };
  window._next = () => { nextTrack(); };

})();
</script>
</body>
</html>
"""

# ---------------------------
# Build playlist payload
# ---------------------------
playlist_payload = []
for url, name in zip(playlist_urls, playlist_names):
    playlist_payload.append({"url": url, "name": name})

# Safely inject Python values
game_html = game_html.replace("__PLAYLIST__", json.dumps(playlist_payload))
game_html = game_html.replace("__PLAYMODE__", json.dumps(play_mode))
game_html = game_html.replace("__AUTO_TRACK_END__", "true" if auto_advance_on_track_end else "false")
game_html = game_html.replace("__AUTO_MATCH_END__", "true" if auto_advance_on_match_end else "false")
game_html = game_html.replace("__MINUTES__", str(int(minutes)))
game_html = game_html.replace("__STARTGAME__", "true" if start_game else "false")
game_html = game_html.replace("__PLAYER_URL__", json.dumps(player_url))
game_html = game_html.replace("__OBSTACLE_URL__", json.dumps(obstacle_url))
game_html = game_html.replace("__BG_URL__", json.dumps(bg_url))

# Render component
html(game_html, height=780, scrolling=True)

# Footer / instructions
st.markdown("---")
st.subheader("Instructions / निर्देश")
st.markdown("""
- App auto-detects music in `./default_music/` (server folder) and `/mnt/data` (environment upload).  
- You can also upload one music file or upload a ZIP with many files.  
- Press **Start** → you will see **3 → 2 → 1** countdown → game + music start.  
- If you want Next/Prev controls in the UI, ya phir auto-pick-last behavior, bata do — main turant add kar dunga.
""")
