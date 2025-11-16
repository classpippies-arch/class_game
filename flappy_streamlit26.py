# flappy_streamlit.py
import streamlit as st
import os, glob, base64

st.set_page_config(page_title="Flappy - Select Music from Repo", layout="wide", page_icon="🐦")
st.markdown("<h1 style='text-align:center'>🎮 Flappy Bird — Repo Music & Images</h1>", unsafe_allow_html=True)
st.write("Choose background and background music from files found in `./assets/images/` and `./assets/sounds/` (no uploads required).")

# ----------------- Paths -----------------
ASSETS_IMG_DIR = os.path.join(".", "assets", "images")
ASSETS_SND_DIR = os.path.join(".", "assets", "sounds")

# helper to list images and sounds from directories or fallback to repo root
def list_images():
    imgs = []
    if os.path.isdir(ASSETS_IMG_DIR):
        for ext in ("png","jpg","jpeg","svg"):
            imgs += sorted(glob.glob(os.path.join(ASSETS_IMG_DIR, f"*.{ext}")))
    # fallback to repo root filenames
    imgs_root = []
    for ext in ("png","jpg","jpeg","svg"):
        imgs_root += sorted(glob.glob(f"*.{ext}"))
    # prefer assets dir results but include root if no assets dir found
    if imgs:
        # return relative paths (posix-like in string)
        return [os.path.relpath(p) for p in imgs]
    return [os.path.relpath(p) for p in imgs_root]

def list_sounds():
    snds = []
    if os.path.isdir(ASSETS_SND_DIR):
        snds = sorted(glob.glob(os.path.join(ASSETS_SND_DIR, "*.mp3"))) + sorted(glob.glob(os.path.join(ASSETS_SND_DIR, "*.wav")))
    if not snds:
        snds = sorted(glob.glob("*.mp3")) + sorted(glob.glob("*.wav"))
    return [os.path.relpath(p) for p in snds]

def path_to_data_url(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        raw = f.read()
    ext = path.lower().split(".")[-1]
    if ext in ("png","svg"):
        mime = "image/png"
    elif ext in ("jpg","jpeg"):
        mime = "image/jpeg"
    elif ext == "mp3":
        mime = "audio/mpeg"
    elif ext == "wav":
        mime = "audio/wav"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(raw).decode()

# ----------------- Discover assets -----------------
images = list_images()
sounds = list_sounds()

if not images:
    st.warning("No image files found in ./assets/images/ or repo root. The game will use fallback visuals (shapes).")
else:
    st.success(f"Found {len(images)} image file(s).")

if not sounds:
    st.info("No sound files found in ./assets/sounds/ or repo root. Background music will be unavailable.")
else:
    st.success(f"Found {len(sounds)} sound file(s).")

# ----------------- Sidebar Controls (no upload) -----------------
with st.sidebar:
    st.header("Game Settings (from repo files)")
    # Music dropdown reads only files found in ./assets/sounds/ (or root)
    music_choice = None
    if sounds:
        music_choice = st.selectbox("Choose background music (from repo)", options=sounds, index=0, format_func=lambda p: os.path.basename(p))
        st.write("Selected:", os.path.basename(music_choice))
    else:
        st.write("No music files found.")

    # Background image dropdown (from repo)
    bg_choice = None
    if images:
        bg_choice = st.selectbox("Choose background image (from repo)", options=images, index=0, format_func=lambda p: os.path.basename(p))
        st.write("Selected:", os.path.basename(bg_choice))
    else:
        st.write("No background images found.")

    # mute toggle
    mute = st.checkbox("Mute audio (menu + in-game)", value=False)
    st.markdown("---")
    st.markdown("Controls: SPACE / Click to flap (jump).")
    st.markdown("Start flow: press START → 3 second countdown → game begins.")
    st.markdown("---")
    st.markdown("Note: If your files are in a different folder, move them to `./assets/images/` and `./assets/sounds/`.")

# ----------------- Session state defaults -----------------
if "menu" not in st.session_state:
    st.session_state.menu = True
if "game_running" not in st.session_state:
    st.session_state.game_running = False
if "game_over" not in st.session_state:
    st.session_state.game_over = False
if "selected_music" not in st.session_state:
    st.session_state.selected_music = music_choice if music_choice else None
if "selected_bg" not in st.session_state:
    st.session_state.selected_bg = bg_choice if bg_choice else None
if "muted" not in st.session_state:
    st.session_state.muted = mute

# If sidebar selection changed, update session_state
# (use a small sync button to commit changes to session state)
if st.sidebar.button("Apply selections"):
    st.session_state.selected_music = music_choice
    st.session_state.selected_bg = bg_choice
    st.session_state.muted = mute
    st.session_state.menu = True
    st.session_state.game_running = False
    st.session_state.game_over = False
    st.experimental_rerun()

# Keep displayed selected music in main UI too
st.markdown("### Menu")
st.write("Single START button below. Choose music & background from sidebar, then press START.")
if st.session_state.selected_music:
    st.info(f"Current music selection: **{os.path.basename(st.session_state.selected_music)}**")
else:
    st.info("No music selected (or none found).")

# Single START button on main page
start_btn = st.button("▶ START GAME", key="start_main", help="Press to start the game with a 3s countdown")

# Small Mute toggle visible in main page too
col_a, col_b = st.columns([1, 4])
with col_a:
    if st.button("🔇 Mute" if st.session_state.muted else "🔊 Unmute", key="mute_toggle"):
        st.session_state.muted = not st.session_state.muted

# When Start pressed: set session state and rerun to render embedded game
if start_btn:
    # apply any chosen sidebar selection if not already applied
    st.session_state.selected_music = music_choice if music_choice else st.session_state.selected_music
    st.session_state.selected_bg = bg_choice if bg_choice else st.session_state.selected_bg
    st.session_state.menu = False
    st.session_state.game_running = True
    st.session_state.game_over = False
    # push to re-run so the embedded HTML sees updated selections
    st.experimental_rerun()

# ----------------- Prepare URLs for HTML game (base64 data URLs) -----------------
BG_URL = path_to_data_url(st.session_state.selected_bg) if st.session_state.selected_bg else ""
MUSIC_URL = path_to_data_url(st.session_state.selected_music) if st.session_state.selected_music else None

# choose an optional gameover sound: pick the first file that contains 'over' / 'end' or fallback to second sound
GAMEOVER_URL = None
if sounds:
    found = None
    for p in sounds:
        low = os.path.basename(p).lower()
        if "over" in low or "end" in low or "gameover" in low:
            found = p; break
    if found:
        GAMEOVER_URL = path_to_data_url(found)
    elif len(sounds) >= 2:
        GAMEOVER_URL = path_to_data_url(sounds[1])
    else:
        GAMEOVER_URL = None

# ----------------- When menu: display big menu (Streamlit layout) -----------------
if st.session_state.menu:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;height:320px;">
      <div style="text-align:center;">
        <h2 style="margin-bottom:8px;">Press START to begin</h2>
        <p style="color:#aaa;">After START you'll see a 3-second countdown. Music will play after countdown (if not muted).</p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    # show available choices and best score saved in browser (best shown from localStorage only inside the embedded game)
    st.info("Tip: Use the 'Apply selections' button in the sidebar if you changed the dropdowns and want to commit them.")
    st.stop()  # stop further rendering — the embed below will be shown when game_running is True

# ----------------- If the game is running, embed the HTML/JS game -----------------
# The game is fully client-side. We inject the selected BG and Music via data-URLs.
# The HTML handles countdown, mute/unmute, Game Over popup with Restart which returns to menu (client-side).
if st.session_state.game_running:

    # safe helper to convert JS string literal or null
    def js_str_or_null(s):
        if s is None:
            return "null"
        # escape quotes
        return '"' + s.replace('"', '\\"') + '"'

    # JS/HTML template (no python f-string braces inside JS — use placeholders and replace)
    GAME_HTML_TEMPLATE = """
    <!doctype html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <style>
    body{margin:0;background:#0b0b0b;color:#fff;font-family:sans-serif}
    #wrap{width:95%;max-width:1000px;margin:10px auto;position:relative}
    canvas{width:100%;height:65vh;background:#000;border-radius:10px;display:block}
    #scoreText{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:999;font-size:22px;font-weight:700}
    .controlTop{position:absolute;top:10px;left:10px;z-index:999}
    .startTop{position:absolute;top:10px;right:10px;z-index:999}
    .popup{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.85);padding:28px;border-radius:12px;display:none;z-index:200;color:#fff;text-align:center}
    .popup h2{margin-bottom:12px}
    .countdown{position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);font-size:96px;color:#ffd93d;z-index:150;display:none}
    .menuOverlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}
    .menuCard{pointer-events:all;background:rgba(0,0,0,0.6);padding:18px;border-radius:10px;text-align:center}
    </style>
    </head>
    <body>
    <div id="wrap">
      <div id="scoreText">Score: <span id="score">0</span></div>
      <div class="controlTop">
        <button id="muteBtn">__MUTE_TEXT__</button>
      </div>
      <div class="startTop">
        <!-- restart/menu button will be injected by Streamlit server buttons; here we only show restart in-game -->
      </div>

      <div class="menuOverlay" id="menuOverlay">
        <div class="menuCard">
          <h3>Get ready</h3>
          <p>Game will start after countdown once you press START on the Streamlit page.</p>
          <p style="font-size:12px;color:#ccc">Tip: SPACE / CLICK to flap.</p>
          <div id="bestLocal" style="margin-top:6px;color:#ddd;font-size:13px"></div>
        </div>
      </div>

      <div class="countdown" id="cd">3</div>
      <div class="popup" id="gameOverPopup">
        <h2>💀 Game Over</h2>
        <div id="finalScore" style="font-size:24px;margin-bottom:12px">Score: 0</div>
        <button id="restartBtn">🔁 Restart to Menu</button>
      </div>

      <canvas id="c"></canvas>
    </div>

    <script>
    // placeholders replaced by Streamlit server
    const BG_URL = __BG_URL__;
    const MUSIC_URL = __MUSIC_URL__;
    const GAMEOVER_URL = __GAMEOVER_URL__;
    let muted = __MUTED__;

    // audio setup
    let audio = null;
    if (MUSIC_URL) {{
      audio = new Audio(MUSIC_URL);
      audio.loop = true;
      audio.volume = 0.5;
    }}
    let gameoverAudio = null;
    if (GAMEOVER_URL) {{
      gameoverAudio = new Audio(GAMEOVER_URL);
      gameoverAudio.volume = 0.6;
    }}

    // set mute button text
    const muteBtn = document.createElement('button');
    muteBtn.id = 'muteBtnInner';
    muteBtn.style.padding = '6px 10px';
    muteBtn.style.borderRadius = '6px';
    muteBtn.style.background = muted ? '#444' : '#20bf6b';
    muteBtn.style.color = '#fff';
    muteBtn.innerText = muted ? 'Muted' : 'Music ON';
    document.getElementById('muteBtn').replaceWith(muteBtn);
    muteBtn.addEventListener('click', ()=>{
      muted = !muted;
      muteBtn.innerText = muted ? 'Muted' : 'Music ON';
      if (muted) {{
        if (audio) audio.pause();
        if (gameoverAudio) gameoverAudio.pause();
      }} else {{
        // resume menu audio if present
        if (!gameRunning && audio) audio.play().catch(()=>{});
        if (gameRunning && audio) audio.play().catch(()=>{});
      }}
    });

    // canvas + game
    const canvas = document.getElementById('c');
    const ctx = canvas.getContext('2d');
    function resize(){{ canvas.width = Math.min(window.innerWidth*0.95, 1000); canvas.height = Math.min(window.innerHeight*0.72, 700); }}
    resize(); window.addEventListener('resize', resize);

    // load images if provided
    let images = {{bg:null}};
    async function loadImages() {{
      try {{ if (BG_URL) images.bg = await loadImage(BG_URL); }} catch(e){{ images.bg = null; console.warn(e); }}
    }}
    function loadImage(src) {{
      return new Promise((res, rej) => {{
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = ()=>res(img);
        img.onerror = rej;
        img.src = src;
      }});
    }}

    // game state
    let gameRunning = false;
    let gameOver = false;
    let score = 0;
    let player = {{x:100,y:200,vy:0,size:48}};
    let pipes = [];
    let pipeTimer = 0;
    const gravity = 0.6;
    const jump = -11;
    const pipeGap = 160;
    let last = performance.now();

    function reset() {{
      score = 0;
      player.y = canvas.height/2;
      player.vy = 0;
      pipes = [];
      gameOver = false;
      document.getElementById('score').innerText = 0;
    }}

    function spawnPipe() {{
      const margin = Math.floor(canvas.height*0.12);
      const center = Math.floor(Math.random()*(canvas.height-margin*2-pipeGap) + margin + pipeGap/2);
      pipes.push({{x: canvas.width + 100, center, scored:false}});
    }}

    function update(dt) {{
      if (!gameRunning || gameOver) return;
      pipeTimer += dt;
      if (pipeTimer > 1400) {{ pipeTimer = 0; spawnPipe(); }}
      for (let p of pipes) p.x -= 3 * (dt/16);
      if (pipes.length && pipes[0].x + 120 < 0) pipes.shift();
      player.vy += gravity * (dt/16);
      player.y += player.vy * (dt/16);
      for (let p of pipes) {{
        const w = Math.floor(canvas.width * 0.09);
        const topH = p.center - (pipeGap/2);
        const bottomY = p.center + (pipeGap/2);
        if (!p.scored && p.x + w < player.x) {{ p.scored = true; score++; document.getElementById('score').innerText = score; }}
        // rectangle collision
        const pr = {{x:player.x,y:player.y,w:player.size,h:player.size}};
        const topRect = {{x:p.x,y:0,w:w,h:topH}};
        const botRect = {{x:p.x,y:bottomY,w:w,h:canvas.height-bottomY}};
        if (rectCollision(pr, topRect) || rectCollision(pr, botRect)) {{ gameOver = true; }}
      }}
      if (player.y + player.size > canvas.height) gameOver = true;
    }}

    function rectCollision(a,b) {{
      return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
    }}

    function render() {{
      if (images.bg) ctx.drawImage(images.bg, 0, 0, canvas.width, canvas.height);
      else {{ ctx.fillStyle = '#000'; ctx.fillRect(0,0,canvas.width,canvas.height); }}
      for (let p of pipes) {{
        const w = Math.floor(canvas.width * 0.09);
        const topH = p.center - (pipeGap/2);
        ctx.fillStyle = '#217a4a';
        ctx.fillRect(p.x, 0, w, topH);
        ctx.fillRect(p.x, p.center + (pipeGap/2), w, canvas.height - (p.center + (pipeGap/2)));
      }}
      ctx.fillStyle = '#f1c40f';
      ctx.fillRect(player.x, player.y, player.size, player.size);
      if (gameOver) {{
        // pause music
        if (audio) audio.pause();
        if (gameoverAudio && !muted) gameoverAudio.play().catch(()=>{});
        // popup
        const popup = document.getElementById('gameOverPopup');
        popup.style.display = 'block';
        document.getElementById('finalScore').innerText = 'Score: ' + score;
      }}
    }}

    function flap() {{
      if (!gameRunning || gameOver) return;
      player.vy = jump;
    }}

    window.addEventListener('keydown', (e)=>{{ if (e.code === 'Space') flap(); }});
    canvas.addEventListener('mousedown', ()=>{{ flap(); }});
    canvas.addEventListener('touchstart', (e)=>{{ e.preventDefault(); flap(); }}, {{passive:false}});

    // countdown routine (3..1) and start
    async function startWithCountdown() {{
      // hide menu overlay
      document.getElementById('menuOverlay').style.display = 'none';
      const cdEl = document.getElementById('cd');
      cdEl.style.display = 'block';
      let val = 3;
      cdEl.innerText = val;
      for (let i=3;i>0;i--) {{
        cdEl.innerText = i;
        await new Promise(r=>setTimeout(r, 800));
      }}
      cdEl.style.display = 'none';
      // start game
      reset();
      gameRunning = true;
      last = performance.now();
      if (audio && !muted) {{
        audio.currentTime = 0;
        audio.play().catch(()=>{{}});
      }}
      requestAnimationFrame(loop);
    }}

    function loop(t) {{
      const dt = t - last; last = t;
      update(dt);
      render();
      if (!gameOver) requestAnimationFrame(loop);
    }}

    // restart button behavior: return to menu (client-side)
    document.getElementById('restartBtn').addEventListener('click', ()=>{{
      // reset audio
      if (audio) audio.pause();
      if (gameoverAudio) gameoverAudio.pause();
      // show menu overlay again and popup hide
      document.getElementById('gameOverPopup').style.display = 'none';
      document.getElementById('menuOverlay').style.display = 'flex';
      gameRunning = false;
      gameOver = false;
      // store best in localStorage
      try {{
        const prev = parseInt(localStorage.getItem('flappy_best')||'0');
        if (score > prev) localStorage.setItem('flappy_best', String(score));
      }} catch(e){{ console.warn(e); }}
      // reveal a small note about how to select different music via Streamlit (server side)
      alert('Restarted — return to the Streamlit menu if you want to pick different music/background.');
      // we cannot change Streamlit server-side session_state from here; user can press Apply selections to sync
    }});

    // show best score if stored
    try {{
      const b = parseInt(localStorage.getItem('flappy_best')||'0');
      if (b>0) document.getElementById('bestLocal').innerText = 'Best: ' + b;
    }} catch(e){{}}

    // load images then show initial menu overlay
    (async ()=>{{
      await loadImages();
      document.getElementById('menuOverlay').style.display = 'flex';
    }})();

    // Kickoff: listen for a start message from Streamlit? (we trigger countdown immediately because START button already set server state)
    // For safety, we'll auto-run the countdown once the page is mounted if gameRunning flag is true.
    // Start immediately (server already set state that it's running).
    startWithCountdown();

    </script>
    </body>
    </html>
    """

    # Build replacements
    html = GAME_HTML_TEMPLATE.replace("__BG_URL__", js_str_or_null(BG_URL))
    html = html.replace("__MUSIC_URL__", js_str_or_null(MUSIC_URL))
    html = html.replace("__GAMEOVER_URL__", js_str_or_null(GAMEOVER_URL))
    html = html.replace("__MUTED__", "true" if st.session_state.muted else "false")
    html = html.replace("__MUTE_TEXT__", "Muted" if st.session_state.muted else "Music ON")

    # Render the HTML component
    st.components.v1.html(html, height=760, scrolling=False)

    # Show small controls and Sync buttons below (optional)
    st.markdown("---")
    st.write("When game ends, use the Restart button in the popup to return to menu. If you want to change music/background, return to the Streamlit UI (sidebar) and press 'Apply selections'.")

    # Provide a server-side Restart action (button) that simply resets session state and reruns the app:
    if st.button("Return to Menu (server-side reset)"):
        st.session_state.menu = True
        st.session_state.game_running = False
        st.session_state.game_over = False
        st.experimental_rerun()

