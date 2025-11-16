# flappy_game_fixed_music.py
import streamlit as st
from streamlit.components.v1 import html
import base64
from pathlib import Path
import json

st.set_page_config(page_title="Flappy Game", layout="wide")
st.title("Flappy Game — Fixed Background Music (No Upload Needed)")
st.write("Press Start → 3..2..1 countdown → game + fixed background music will start.")

# -----------------------------
# Path to your fixed background music on the machine where Streamlit runs
# Update this path if your file name/path is different.
# -----------------------------
MUSIC_PATH = "/mnt/data/miaw-miaw-miaw-song-sad-lyrics-video-visual_XBvfuPbJ.mp3"

if not Path(MUSIC_PATH).exists():
    st.error(f"Music file not found at: {MUSIC_PATH}")
    st.stop()

def local_file_to_data_url(path: str) -> str:
    """Read a local file and return a data URL (audio/mpeg)."""
    b = Path(path).read_bytes()
    b64 = base64.b64encode(b).decode("ascii")
    return f"data:audio/mpeg;base64,{b64}"

music_url = local_file_to_data_url(MUSIC_PATH)

# Optional: You can leave sprite/background URLs empty or customize by embedding other files similarly.
player_url = ""
obstacle_url = ""
bg_url = ""

# A simple Start button in Streamlit (keeps parity with in-game Start)
start_game = st.button("Start / Restart Game")

# -----------------------------
# Build the HTML/JS for the game.
# We avoid f-string brace collisions by placing tokens and replacing them with safe JSON-encoded strings.
# -----------------------------
game_html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flappy - Fixed Music</title>
  <style>
    html,body { margin:0; height:100%; background:#111; font-family: system-ui, -apple-system, 'Segoe UI', Roboto; color:#fff; }
    #gameArea { display:flex; align-items:center; justify-content:center; height:100vh; }
    canvas { border-radius:12px; box-shadow:0 6px 16px rgba(0,0,0,0.6); background:#70c5ce; }
    .ui-top { position:absolute; top:8px; left:8px; right:8px; display:flex; justify-content:space-between; pointer-events:none; z-index:50; }
    .ui-top .left, .ui-top .right { pointer-events:auto; }
    .btn { background:rgba(0,0,0,0.35); color:white; padding:6px 10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06); cursor:pointer; }
    #countdownOverlay { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; z-index:60; background:rgba(0,0,0,0.5); visibility:hidden; }
    #miniCountdown { font-size:120px; font-weight:800; text-shadow:0 6px 18px rgba(0,0,0,0.8); color:#fff; }
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
    </div>
  </div>

  <div id="gameArea">
    <canvas id="gameCanvas" width="720" height="480"></canvas>
  </div>

  <div id="countdownOverlay"><div id="miniCountdown">3</div></div>

<script>
(() => {
  // Injected values (will be replaced)
  const MUSIC_URL = __MUSIC_URL__;
  const PLAYER_SRC = __PLAYER_URL__;
  const OBSTACLE_SRC = __OBSTACLE_URL__;
  const BG_SRC = __BG_URL__;
  const START_FROM_PY = __START_FROM_PY__;

  // Canvas setup
  const canvas = document.getElementById('gameCanvas');
  const ctx = canvas.getContext('2d');
  let W = canvas.width, H = canvas.height;

  // Load images (if provided)
  const playerImg = new Image(); const obstacleImg = new Image(); const bgImg = new Image();
  try { playerImg.src = PLAYER_SRC; } catch(e) {}
  try { obstacleImg.src = OBSTACLE_SRC; } catch(e) {}
  try { bgImg.src = BG_SRC; } catch(e) {}

  // Fixed background music (embedded)
  const bgm = new Audio(MUSIC_URL);
  bgm.loop = true;
  bgm.volume = 0.6;

  // Game state
  let playing = false;
  let paused = false;
  let gravity = 0.45;
  let lift = -9;
  let bird = { x: 100, y: H/2, vel: 0, w: 40, h: 30 };
  let pipes = [];
  let spawnTimer = 0;
  let score = 0;
  let lastTimestamp = null;
  let best = localStorage.getItem('flappy_best') || 0;

  function updateScoreDisplay() {
    document.getElementById('scoreDisplay').textContent = `Score: ${score}  | Best: ${best}`;
  }

  function resetGame() {
    bird.y = H/2;
    bird.vel = 0;
    pipes = [];
    spawnTimer = 0;
    score = 0;
    lastTimestamp = null;
    updateScoreDisplay();
  }

  // Input
  function flap() { bird.vel = lift; }
  window.addEventListener('keydown', (e) => { if (e.code === 'Space') flap(); });
  canvas.addEventListener('mousedown', flap);
  canvas.addEventListener('touchstart', (e) => { e.preventDefault(); flap(); }, {passive:false});

  // Buttons + Countdown
  const startPauseBtn = document.getElementById('startPauseBtn');
  const muteBtn = document.getElementById('muteBtn');
  const countdownOverlay = document.getElementById('countdownOverlay');
  const miniCountdown = document.getElementById('miniCountdown');

  startPauseBtn.addEventListener('click', () => {
    if (!playing) {
      showCountdownThenStart(3);
    } else {
      paused = !paused;
      startPauseBtn.textContent = paused ? 'Resume' : 'Pause';
      if (paused) bgm.pause(); else bgm.play().catch(()=>{});
    }
  });

  muteBtn.addEventListener('click', () => {
    bgm.muted = !bgm.muted;
    muteBtn.textContent = bgm.muted ? 'Unmute' : 'Mute';
  });

  function showCountdownThenStart(seconds) {
    countdownOverlay.style.visibility = 'visible';
    let n = seconds;
    miniCountdown.innerText = n;
    const tick = () => {
      n -= 1;
      if (n >= 1) {
        miniCountdown.innerText = n;
        setTimeout(tick, 1000);
      } else {
        countdownOverlay.style.visibility = 'hidden';
        startPlaying();
      }
    };
    setTimeout(tick, 1000);
  }

  function startPlaying() {
    playing = true;
    paused = false;
    startPauseBtn.textContent = 'Pause';
    resetGame();
    if (bgm.src) bgm.play().catch(()=>{});
    requestAnimationFrame(loop);
  }

  // Game loop
  function loop(ts) {
    if (!lastTimestamp) lastTimestamp = ts;
    const dt = ts - lastTimestamp;
    lastTimestamp = ts;

    if (!paused) {
      // physics
      bird.vel += gravity;
      bird.y += bird.vel;

      spawnTimer += dt;
      if (spawnTimer > 1600) {
        spawnTimer = 0;
        const gap = 160;
        const topH = 80 + Math.random() * (H - 300);
        pipes.push({ x: W + 40, top: topH, gap: gap });
      }

      for (let i = pipes.length - 1; i >= 0; i--) {
        const p = pipes[i];
        p.x -= 2.8;
        // scoring
        if (!p.scored && p.x + 60 < bird.x) {
          score += 1;
          p.scored = true;
          if (score > best) { best = score; localStorage.setItem('flappy_best', best); }
          updateScoreDisplay();
        }
        // remove offscreen
        if (p.x < -120) pipes.splice(i, 1);
      }

      // collisions
      let died = false;
      if (bird.y + bird.h/2 >= H || bird.y - bird.h/2 <= 0) died = true;
      for (const p of pipes) {
        const pipeW = 60;
        const px = p.x, top = p.top, gap = p.gap;
        if (bird.x + bird.w/2 > px - pipeW/2 && bird.x - bird.w/2 < px + pipeW/2) {
          if (bird.y - bird.h/2 < top || bird.y + bird.h/2 > top + gap) {
            died = true;
            break;
          }
        }
      }
      if (died) playing = false;
    }

    // draw
    ctx.clearRect(0, 0, W, H);
    // background
    if (bgImg && bgImg.complete && bgImg.src) {
      try { ctx.drawImage(bgImg, 0, 0, W, H); } catch(e) { ctx.fillStyle = '#70c5ce'; ctx.fillRect(0,0,W,H); }
    } else {
      ctx.fillStyle = '#70c5ce'; ctx.fillRect(0,0,W,H);
      ctx.fillStyle = 'rgba(255,255,255,0.6)';
      ctx.beginPath(); ctx.ellipse(120,80,40,24,0,0,Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.ellipse(220,60,60,30,0,0,Math.PI*2); ctx.fill();
    }

    // pipes
    ctx.fillStyle = '#2d8f39';
    for (const p of pipes) {
      const pipeW = 60;
      if (obstacleImg && obstacleImg.complete && obstacleImg.src) {
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, 0, pipeW, p.top); } catch(e) { ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top); }
        try { ctx.drawImage(obstacleImg, p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); } catch(e) { ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap)); }
      } else {
        ctx.fillRect(p.x - pipeW/2, 0, pipeW, p.top);
        ctx.fillRect(p.x - pipeW/2, p.top + p.gap, pipeW, H - (p.top + p.gap));
      }
    }

    // bird
    if (playerImg && playerImg.complete && playerImg.src) {
      try {
        ctx.save();
        const rot = Math.max(-0.6, Math.min(0.6, bird.vel / 12));
        ctx.translate(bird.x, bird.y);
        ctx.rotate(rot);
        ctx.drawImage(playerImg, -bird.w/2, -bird.h/2, bird.w, bird.h);
        ctx.restore();
      } catch(e) {
        ctx.fillStyle = 'yellow';
        ctx.fillRect(bird.x - bird.w/2, bird.y - bird.h/2, bird.w, bird.h);
      }
    } else {
      ctx.fillStyle = 'yellow';
      ctx.beginPath();
      ctx.ellipse(bird.x, bird.y, 18, 14, 0, 0, Math.PI*2);
      ctx.fill();
    }

    // UI overlay when not playing
    if (!playing) {
      ctx.fillStyle = 'rgba(0,0,0,0.45)';
      ctx.fillRect(0,0,W,H);
      ctx.fillStyle = 'white';
      ctx.textAlign = 'center';
      ctx.font = '28px system-ui';
      ctx.fillText('Press Start to Play', W/2, H/2 - 20);
      ctx.font = '18px system-ui';
      ctx.fillText('Controls: tap / click / spacebar', W/2, H/2 + 10);
      ctx.font = '16px system-ui';
      ctx.fillText(`Score: ${score}  |  Best: ${best}`, W/2, H/2 + 40);
    }

    if (playing) requestAnimationFrame(loop);
    else {
      if (bgm) bgm.pause();
      startPauseBtn.textContent = 'Start';
    }
  }

  // responsive
  function resizeCanvas() {
    const containerW = Math.min(window.innerWidth - 100, 900);
    const containerH = Math.min(window.innerHeight - 160, 700);
    const ratio = 3/2;
    let cw = containerW, ch = Math.round(cw / ratio);
    if (ch > containerH) { ch = containerH; cw = Math.round(ch * ratio); }
    canvas.width = cw; canvas.height = ch;
    W = canvas.width; H = canvas.height;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // start if Python button pressed
  if (START_FROM_PY) {
    showCountdownThenStart(3);
  }
})();
</script>
</body>
</html>
"""

# Safe injection: replace tokens using json.dumps to make valid JS strings/literals
game_html = game_html_template.replace("__MUSIC_URL__", json.dumps(music_url))
game_html = game_html.replace("__PLAYER_URL__", json.dumps(player_url))
game_html = game_html.replace("__OBSTACLE_URL__", json.dumps(obstacle_url))
game_html = game_html.replace("__BG_URL__", json.dumps(bg_url))
game_html = game_html.replace("__START_FROM_PY__", "true" if start_game else "false")

# Render the game
html(game_html, height=740, scrolling=False)

# Small instructions below the canvas
st.markdown("---")
st.markdown("**Controls:** Tap / Click / Spacebar — Press Start to see the 3..2..1 countdown and begin.")
st.markdown("**Note:** Music is fixed and embedded in the app; users can't change it from the web UI.")
