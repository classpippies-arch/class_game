# flappy_streamlit.py
import streamlit as st
from streamlit.components.v1 import html
import base64
import time
import json

st.set_page_config(page_title="Flappy - Streamlit", layout="wide")

st.title("Flappy-style Game — Streamlit Web App (Single Python file)")
st.write("Upload sprites/background/music → press Start → play with mouse/tap/spacebar. (All in one .py)")

# Sidebar controls / uploads
with st.sidebar:
    st.header("Game Assets & Options")
    st.markdown("Upload images (PNG with transparency recommended). If you skip, default sprites will be used.")
    player_file = st.file_uploader("Player sprite (image)", type=["png", "jpg", "jpeg"], key="player")
    obstacle_file = st.file_uploader("Obstacle sprite (image)", type=["png", "jpg", "jpeg"], key="obstacle")
    bg_file = st.file_uploader("Background image", type=["png", "jpg", "jpeg"], key="bg")
    music_file = st.file_uploader("Music (mp3/ogg) — optional", type=["mp3", "ogg"], key="music")

    st.markdown("---")
    minutes = st.number_input("Auto end after (minutes). 0 = no timer", min_value=0, max_value=120, value=0, step=1)
    start_immediately = st.button("START GAME (Streamlit)")

    st.markdown("---")
    st.write("Best score (client saved to browser localStorage). Use Share button in-game to tweet score.")
    st.write("If you want server-side save, tell me and I will add a small backend (JSON file or DB).")

# Helper: convert uploaded file to data URL
def file_to_data_url(uploaded):
    if uploaded is None:
        return None
    data = uploaded.read()
    mime = uploaded.type if hasattr(uploaded, "type") else "application/octet-stream"
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"

player_url = file_to_data_url(player_file) or ""
obstacle_url = file_to_data_url(obstacle_file) or ""
bg_url = file_to_data_url(bg_file) or ""
music_url = file_to_data_url(music_file) or ""

# Streamlit top control (single start/pause button visible in page header area)
col1, col2, col3 = st.columns([1, 6, 1])
with col3:
    # This acts like an "always visible" start button in the Streamlit chrome
    st.markdown("<div style='text-align:right'>", unsafe_allow_html=True)
    start_button_top = st.button("Start / Restart Game", key="top_start")
    st.markdown("</div>", unsafe_allow_html=True)

start_game = start_immediately or start_button_top

# Build HTML/JS game as a plain string with tokens to replace (avoids f-string/brace issues).
game_html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Flappy - Embedded</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html,body { margin:0; height:100%; background:#111; }
    #gameArea { display:flex; align-items:center; justify-content:center; height:100%; }
    canvas { border-radius:12px; box-shadow:0 6px 16px rgba(0,0,0,0.6); background:#88c; }
    .ui-top {
      position:absolute; top:8px; left:8px; right:8px; display:flex; justify-content:space-between; pointer-events:none;
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
      color:white; z-index:10;
    }
    .ui-top .left, .ui-top .right { pointer-events:auto; }
    .btn { background:rgba(0,0,0,0.3); color:white; padding:6px 10px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); cursor:pointer; }
    .small { font-size:14px; }
  </style>
</head>
<body>
  <div class="ui-top">
    <div class="left">
      <span id="scoreDisplay" style="font-weight:700; font-size:20px; padding:6px 10px; background:rgba(0,0,0,0.35); border-radius:8px;">Score: 0</span>
    </div>
    <div class="right">
      <button id="startPauseBtn" class="btn small">Start</button>
      <button id="muteBtn" class="btn small">Mute</button>
      <button id="shareBtn" class="btn small">Share</button>
    </div>
  </div>
  <div id="gameArea">
    <canvas id="gameCanvas" width="720" height="480"></canvas>
  </div>

<script>
(() => {
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // Load images (data URLs passed from Python)
  const playerSrc = __PLAYER_URL__;
  const obstacleSrc = __OBSTACLE_URL__;
  const bgSrc = __BG_URL__;
  const musicSrc = __MUSIC_URL__;

  // Default images (simple drawn shapes) if user didn't upload
  const playerImg = new Image();
  const obstacleImg = new Image();
  const bgImg = new Image();
  let imagesLoaded = 0;
  const toLoad = [];

  function maybeCount(){ imagesLoaded++; }

  if (playerSrc) {
    playerImg.src = playerSrc;
    playerImg.onload = maybeCount;
    playerImg.onerror = maybeCount;
  } else {
    // draw later
    maybeCount();
  }

  if (obstacleSrc) {
    obstacleImg.src = obstacleSrc;
    obstacleImg.onload = maybeCount;
    obstacleImg.onerror = maybeCount;
  } else {
    maybeCount();
  }

  if (bgSrc) {
    bgImg.src = bgSrc;
    bgImg.onload = maybeCount;
    bgImg.onerror = maybeCount;
  } else {
    maybeCount();
  }

  // Music
  let audio = null;
  if (musicSrc) {
    audio = new Audio(musicSrc);
    audio.loop = true;
    audio.volume = 0.5;
  }

  // Game state
  let playing = false;
  let paused = false;
  let gravity = 0.45;
  let lift = -9;
  let bird = { x: 100, y: H/2, vel: 0, w: 48, h: 36 };
  let pipes = [];
  let spawnTimer = 0;
  let score = 0;
  let best = localStorage.getItem('flappy_best') || 0;
  let lastTimestamp = null;
  let elapsedMs = 0;
  const timeLimitMinutes = __MINUTES__; // passed from sidebar

  // Start / reset
  function resetGame() {
    bird.y = H/2;
    bird.vel = 0;
    pipes = [];
    spawnTimer = 0;
    score = 0;
    elapsedMs = 0;
    lastTimestamp = null;
    updateScoreDisplay();
  }

  // Input
  function flap() {
    bird.vel = lift;
  }
  window.addEventListener('keydown', (e)=>{ if(e.code==='Space') flap(); });
  canvas.addEventListener('mousedown', (e)=>{ flap(); });
  canvas.addEventListener('touchstart', (e)=>{ e.preventDefault(); flap(); }, {passive:false});

  // Buttons
  const startPauseBtn = document.getElementById('startPauseBtn');
  const muteBtn = document.getElementById('muteBtn');
  const shareBtn = document.getElementById('shareBtn');

  startPauseBtn.addEventListener('click', ()=>{
    if(!playing) {
      startPlaying();
    } else {
      paused = !paused;
      startPauseBtn.textContent = paused ? 'Resume' : 'Pause';
      if(audio) audio[paused ? 'pause' : 'play']();
    }
  });

  muteBtn.addEventListener('click', ()=>{
    if(!audio) return;
    if(audio.muted) { audio.muted = false; muteBtn.textContent='Mute'; }
    else { audio.muted = true; muteBtn.textContent='Unmute'; }
  });

  shareBtn.addEventListener('click', ()=>{
    const text = encodeURIComponent(`I scored ${score} points playing this Flappy-style game!`);
    const url = encodeURIComponent(location.href);
    const tweet = `https://twitter.com/intent/tweet?text=${text}&url=${url}`;
    window.open(tweet, '_blank');
  });

  function startPlaying() {
    playing = true;
    paused = false;
    startPauseBtn.textContent = 'Pause';
    if(audio) audio.play().catch(()=>{/* ignore autoplay block */});
    resetGame();
    requestAnimationFrame(loop);
  }

  function updateScoreDisplay() {
    document.getElementById('scoreDisplay').textContent = `Score: ${score}  | Best: ${best}`;
  }

  // Game loop
  function loop(ts) {
    if (!lastTimestamp) lastTimestamp = ts;
    const dt = ts - lastTimestamp;
    lastTimestamp = ts;
    if(!paused) {
      // update
      elapsedMs += dt;
      bird.vel += gravity;
      bird.y += bird.vel;
      spawnTimer += dt;

      // spawn pipes every ~1.6s
      if(spawnTimer > 1600) {
        spawnTimer = 0;
        const gap = 140 + Math.random()*60;
        const topH = 80 + Math.random()*(H - 300);
        pipes.push({ x: W + 20, top: topH, gap });
      }

      // move pipes
      for(let i=pipes.length-1;i>=0;i--) {
        pipes[i].x -= 2.6 + Math.min(score/100, 2.0);
        // scoring when pipe passes bird.x
        if(!pipes[i].scored && pipes[i].x + 40 < bird.x) {
          score += 1;
          pipes[i].scored = true;
          if(score > best) {
            best = score;
            localStorage.setItem('flappy_best', best);
          }
          updateScoreDisplay();
        }
        // remove offscreen
        if(pipes[i].x < -80) pipes.splice(i,1);
      }

      // collisions: floor and ceiling
      if(bird.y + bird.h/2 >= H || bird.y - bird.h/2 <= 0) {
        playing = false;
      }

      // pipe collisions
      for(const p of pipes) {
        const pipeW = 60;
        const px = p.x, top = p.top, gap = p.gap;
        if(bird.x + bird.w/2 > px - pipeW/2 && bird.x - bird.w/2 < px + pipeW/2) {
          if(bird.y - bird.h/2 < top || bird.y + bird.h/2 > top + gap) {
            playing = false;
            break;
          }
        }
      }

      // time limit
      if(timeLimitMinutes > 0) {
        if(elapsedMs >= timeLimitMinutes * 60 * 1000) {
          playing = false;
        }
      }
    }

    // draw
    ctx.clearRect(0,0,W,H);
    // background
    if(bgSrc) {
      // draw bg image stretched
      try { ctx.drawImage(bgImg, 0, 0, W, H); } catch(e) { ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H); }
    } else {
      ctx.fillStyle='#70c5ce'; ctx.fillRect(0,0,W,H);
      // some clouds
      ctx.fillStyle='rgba(255,255,255,0.6)';
      ctx.beginPath(); ctx.ellipse(120,80,40,24,0,0,Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(220,60,60,30,0,0,Math.PI*2); ctx.fill();
    }

    // pipes
    ctx.fillStyle = '#2d8f39';
    for(const p of pipes) {
      const pipeW = 60;
      // top
      if(obstacleSrc) {
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, 0, pipeW, p.top); } catch(e) { ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top); }
      } else {
        ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top);
      }
      // bottom
      if(obstacleSrc) {
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); } catch(e) { ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); }
      } else {
        ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap));
      }
    }

    // bird
    if(playerSrc) {
      try {
        ctx.save();
        // rotate a bit based on vel
        const rot = Math.max(-0.6, Math.min(0.6, bird.vel / 12));
        ctx.translate(bird.x, bird.y);
        ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      } catch(e) {
        ctx.fillStyle='yellow'; ctx.fillRect(bird.x - bird.w/2, bird.y - bird.h/2, bird.w, bird.h);
      }
    } else {
      ctx.fillStyle='yellow';
      ctx.beginPath();
      ctx.ellipse(bird.x, bird.y, 18, 14, 0, 0, Math.PI*2);
      ctx.fill();
    }

    // if not playing show overlay
    if(!playing) {
      ctx.fillStyle='rgba(0,0,0,0.45)';
      ctx.fillRect(0,0,W,H);
      ctx.fillStyle='white';
      ctx.textAlign='center';
      ctx.font = '28px system-ui';
      ctx.fillText('Press Start to Play', W/2, H/2 - 20);
      ctx.font = '18px system-ui';
      ctx.fillText('Controls: tap / click / spacebar', W/2, H/2 + 10);
      ctx.font = '16px system-ui';
      ctx.fillText(`Score: ${score}  |  Best: ${best}`, W/2, H/2 + 40);
    }

    if(playing) requestAnimationFrame(loop);
    else {
      // stop music if ended
      if(audio) audio.pause();
      startPauseBtn.textContent = 'Start';
      // final update to best localStorage (already updated during scoring)
      updateScoreDisplay();
    }
  }

  // start automatically if Streamlit asked to start
  const startFromPython = __STARTGAME__;
  if(startFromPython) {
    startPlaying();
  }
  // initial display update
  updateScoreDisplay();

  // handle resize to keep things responsive
  function resizeCanvas() {
    const containerW = Math.min(window.innerWidth - 100, 900);
    const containerH = Math.min(window.innerHeight - 160, 700);
    // maintain aspect ratio approx 3:2
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if(ch > containerH) {
      ch = containerH; cw = Math.round(ch * ratio);
    }
    canvas.width = cw; canvas.height = ch;
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

})();
</script>
</body>
</html>
"""

# Safely inject Python values into the HTML by replacing tokens.
# Use json.dumps so strings are properly quoted/escaped for JS string literals.
game_html = game_html.replace("__PLAYER_URL__", json.dumps(player_url))
game_html = game_html.replace("__OBSTACLE_URL__", json.dumps(obstacle_url))
game_html = game_html.replace("__BG_URL__", json.dumps(bg_url))
game_html = game_html.replace("__MUSIC_URL__", json.dumps(music_url))
game_html = game_html.replace("__MINUTES__", str(int(minutes)))
game_html = game_html.replace("__STARTGAME__", "true" if start_game else "false")

# Render the HTML in Streamlit - this is still a single .py file; HTML lives inside the string
# Height is set to allow the canvas and UI comfortably
html(game_html, height=680, scrolling=True)

# Provide short instructions and Hindi+English explanation per your preference
st.markdown("---")
st.subheader("Instructions / निर्देश")
st.markdown("""
- Use the sidebar to upload **player**, **obstacle**, **background** and optional **music** files.  
- Click **Start Game** (sidebar or top-right) to begin. Use mouse click / tap / **spacebar** to flap.  
- The in-game top-right buttons: **Start/Pause**, **Mute**, **Share** (tweet).  
- Best score is saved in your browser's **localStorage**. If you want server-side saving (so score persists across devices) tell me and I will add a small JSON backend or connect to a Google Sheet.
- अगर आप बिल्कुल भी HTML नहीं चाहते (न तो embed), तो ब्राउज़र में गेम बनाना संभव नहीं होगा — उस स्थिति में मैं एक `pygame`-based desktop Python game बना दूँगा जिसे आप अपने कंप्यूटर पर चला सकते हैं.
""")

st.markdown("### Developer notes (short):\n- The game canvas and logic are implemented in embedded JS/HTML inside the Python file. This is required for smooth browser gameplay.\n- All assets are encoded and passed from Python to the embedded game as data URLs, so no external files are needed after upload.\n- Timer option: set minutes in the sidebar; 0 disables the timer.\n")

st.markdown("If you want any of the following, tell me and I'll update the single .py file accordingly:")
st.write("- Server-side best-score saving (JSON file or DB).")
st.write("- Different physics (stronger gravity / slower speed).")
st.write("- More UI polish: custom fonts, flashy animations, more responsive layouts.")
st.write("- A downloadable build (PWA) or a desktop pygame version instead of browser.")
