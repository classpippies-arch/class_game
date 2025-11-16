# flappy_streamlit26.py
import streamlit as st
import base64
import os

st.set_page_config(page_title="Premium Flappy Bird", layout="wide", page_icon="🐦")

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.2rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .upload-section {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎮 Premium Flappy Bird</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Customize your gaming experience with stunning visuals and audio</div>', unsafe_allow_html=True)

# --------- Premium Sidebar Design ---------
with st.sidebar:
    st.markdown("### 🎨 Game Studio")
    
    with st.container():
        st.markdown("#### 🖼️ Visual Assets")
        with st.expander("Upload Images", expanded=True):
            up_bg = st.file_uploader("🌅 Background", type=["png","jpg","jpeg"], key="bg")
            up_player = st.file_uploader("🐦 Player Character", type=["png","jpg","jpeg"], key="player")
            up_pipe = st.file_uploader("🚧 Obstacles", type=["png","jpg","jpeg"], key="pipe")
            up_bag = st.file_uploader("💼 Character's Bag", type=["png","jpg","jpeg"], key="bag")

    with st.container():
        st.markdown("#### 🎵 Audio Library")
        with st.expander("Music & Sound Effects", expanded=True):
            st.markdown("**🎵 Background Music**")
            up_menu_music = st.file_uploader("🏠 Menu Music", type=["mp3","ogg","wav"], key="menu_music")
            up_ingame_music = st.file_uploader("🎮 Game Music", type=["mp3","ogg","wav"], key="ingame_music")
            up_gameover_music = st.file_uploader("💀 Game Over Music", type=["mp3","ogg","wav"], key="gameover_music")
            
            st.markdown("**🔊 Sound Effects**")
            up_start_effect = st.file_uploader("🚀 Game Start Effect", type=["mp3","ogg","wav"], key="start_effect")
            up_countdown_effect = st.file_uploader("⏱️ Countdown Effect", type=["mp3","ogg","wav"], key="countdown_effect")
            up_jump_effect = st.file_uploader("🦅 Jump Effect", type=["mp3","ogg","wav"], key="jump_effect")
            up_score_effect = st.file_uploader("⭐ Score Effect (0-5)", type=["mp3","ogg","wav"], key="score_effect")
            up_highscore_effect = st.file_uploader("🏆 High Score Effect (6-10)", type=["mp3","ogg","wav"], key="highscore_effect")
            up_random_effect = st.file_uploader("🎲 Random Effect", type=["mp3","ogg","wav"], key="random_effect")
            up_elimination_effect = st.file_uploader("💥 Elimination Effect", type=["mp3","ogg","wav"], key="elimination_effect")

    with st.container():
        st.markdown("#### ⚙️ Game Settings")
        with st.expander("Difficulty & Controls", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                game_speed = st.slider("Speed", 1, 10, 3)
                gravity_strength = st.slider("Gravity", 0.1, 1.0, 0.5)
            with col2:
                jump_power = st.slider("Jump Power", 5, 20, 12)
                pipe_gap = st.slider("Pipe Gap", 120, 250, 180)

    st.markdown("---")
    st.success("🎯 **Pro Tip**: Upload high-quality assets for the best gaming experience!")

# --------- File Processing ---------
def fileobj_to_data_url(fileobj, default_path=None):
    if fileobj is not None:
        raw = fileobj.read()
        name = fileobj.name.lower()
        mime = "image/png"
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            mime = "image/jpeg"
        elif name.endswith(".mp3"):
            mime = "audio/mpeg"
        elif name.endswith(".ogg"):
            mime = "audio/ogg"
        elif name.endswith(".wav"):
            mime = "audio/wav"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    
    if default_path and os.path.exists(default_path):
        with open(default_path, "rb") as f:
            raw = f.read()
        ext = default_path.lower().split(".")[-1]
        mime = "image/png"
        if ext in ("jpg", "jpeg"):
            mime = "image/jpeg"
        elif ext == "mp3":
            mime = "audio/mpeg"
        elif ext == "ogg":
            mime = "audio/ogg"
        elif ext == "wav":
            mime = "audio/wav"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    return None

# File mappings
REPO_BG = "background_image.png"
REPO_PLAYER = "player_character.png"
REPO_PIPE = "obstacle_enemy.png"
REPO_BAG = "player_character.png"

# Process files
BG_URL = fileobj_to_data_url(up_bg, REPO_BG) or ""
PLAYER_URL = fileobj_to_data_url(up_player, REPO_PLAYER) or ""
PIPE_URL = fileobj_to_data_url(up_pipe, REPO_PIPE) or ""
BAG_URL = fileobj_to_data_url(up_bag, REPO_BAG) or ""

# Music files - using your uploaded files
MENU_MUSIC_URL = fileobj_to_data_url(up_menu_music, "very starting point.mp3")
INGAME_MUSIC_URL = fileobj_to_data_url(up_ingame_music, "random effect.mp3")
GAMEOVER_MUSIC_URL = fileobj_to_data_url(up_gameover_music, "ending effect.mp3")

# Sound effects
START_EFFECT_URL = fileobj_to_data_url(up_start_effect, "game starting effect.mp3")
COUNTDOWN_EFFECT_URL = fileobj_to_data_url(up_countdown_effect, "starting effect.mp3")
JUMP_EFFECT_URL = fileobj_to_data_url(up_jump_effect, "random effect used in game.mp3")
SCORE_EFFECT_URL = fileobj_to_data_url(up_score_effect, "0 to 5 elimination effect.mp3")
HIGHSCORE_EFFECT_URL = fileobj_to_data_url(up_highscore_effect, "6 to 10 point effect.mp3")
RANDOM_EFFECT_URL = fileobj_to_data_url(up_random_effect, "random effect.mp3")
ELIMINATION_EFFECT_URL = fileobj_to_data_url(up_elimination_effect, "0 to 5 elimination effect.mp3")

# --------- Premium Game HTML ---------
game_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Flappy Bird</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }}

        .game-container {{
            position: relative;
            width: 95%;
            max-width: 900px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        #gameCanvas {{
            width: 100%;
            height: 70vh;
            background: #000;
            border-radius: 15px;
            display: block;
            border: 3px solid rgba(255, 255, 255, 0.3);
            box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.5);
        }}

        .controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 100;
            display: flex;
            gap: 10px;
        }}

        .control-btn {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}

        .control-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }}

        .score-display {{
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: #ffd93d;
            padding: 10px 25px;
            border-radius: 25px;
            font-size: 1.5rem;
            font-weight: 700;
            z-index: 100;
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 217, 61, 0.3);
        }}

        .countdown {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 6rem;
            font-weight: 900;
            color: #ffd93d;
            text-shadow: 0 0 30px rgba(255, 217, 61, 0.8);
            z-index: 200;
            animation: pulse 1s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: translate(-50%, -50%) scale(1); opacity: 1; }}
            50% {{ transform: translate(-50%, -50%) scale(1.1); opacity: 0.7; }}
        }}

        .start-screen {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 300;
            border-radius: 15px;
        }}

        .start-content {{
            text-align: center;
            color: white;
            padding: 40px;
        }}

        .start-title {{
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffd93d, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }}

        .start-subtitle {{
            font-size: 1.2rem;
            color: #ccc;
            margin-bottom: 30px;
            line-height: 1.6;
        }}

        .start-btn {{
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            color: white;
            border: none;
            padding: 20px 50px;
            font-size: 1.5rem;
            font-weight: 700;
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4);
        }}

        .start-btn:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(255, 107, 107, 0.6);
        }}

        .game-over {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 400;
            border-radius: 15px;
        }}

        .game-over-content {{
            text-align: center;
            color: white;
            padding: 40px;
        }}

        .character-popup {{
            position: absolute;
            bottom: 50px;
            left: 50%;
            transform: translateX(-50%);
            animation: float 3s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateX(-50%) translateY(0px); }}
            50% {{ transform: translateX(-50%) translateY(-20px); }}
        }}

        .bag-popup {{
            position: absolute;
            bottom: 120px;
            left: 50%;
            transform: translateX(-50%);
            animation: float 3s ease-in-out infinite 0.5s;
        }}

        .final-score {{
            font-size: 4rem;
            font-weight: 800;
            color: #ffd93d;
            margin: 20px 0;
            text-shadow: 0 0 20px rgba(255, 217, 61, 0.5);
        }}

        .restart-btn {{
            background: linear-gradient(135deg, #4ecdc4, #44a08d);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
        }}

        .restart-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(78, 205, 196, 0.4);
        }}

        .audio-status {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div class="game-container">
        <canvas id="gameCanvas"></canvas>
        
        <div class="controls">
            <button class="control-btn" id="musicToggle">🔊 Music ON</button>
            <button class="control-btn" id="startBtn">🚀 Start</button>
        </div>
        
        <div class="score-display">
            Score: <span id="score">0</span>
        </div>

        <div class="audio-status" id="audioStatus">🔊 Menu Music</div>

        <div class="countdown" id="countdown" style="display: none;">3</div>

        <div class="start-screen" id="startScreen">
            <div class="start-content">
                <div class="start-title">🎮 Flappy Bird</div>
                <div class="start-subtitle">
                    Customize your game with amazing visuals and audio!<br>
                    Avoid obstacles and achieve the highest score!
                </div>
                <button class="start-btn" id="mainStartBtn">START GAME</button>
            </div>
        </div>

        <div class="game-over" id="gameOverScreen">
            <div class="game-over-content">
                <div style="font-size: 3rem; color: #ff6b6b; margin-bottom: 20px;">💀 Game Over</div>
                <div class="final-score" id="finalScore">0</div>
                <div style="color: #ccc; margin-bottom: 30px; font-size: 1.1rem;">
                    Better luck next time! 🎯
                </div>
                <img src="{BAG_URL or PLAYER_URL}" class="bag-popup" style="width: 80px; height: 80px; border-radius: 10px;" alt="Bag">
                <img src="{PLAYER_URL}" class="character-popup" style="width: 100px; height: 100px; border-radius: 15px;" alt="Character">
                <br>
                <button class="restart-btn" id="restartBtn">🔄 Play Again</button>
            </div>
        </div>
    </div>

    <script>
        // Game Configuration
        const CONFIG = {{
            PLAYER_URL: "{PLAYER_URL}",
            PIPE_URL: "{PIPE_URL}",
            BG_URL: "{BG_URL}",
            
            // Background Music
            MENU_MUSIC_URL: {('"' + MENU_MUSIC_URL + '"') if MENU_MUSIC_URL else 'null'},
            INGAME_MUSIC_URL: {('"' + INGAME_MUSIC_URL + '"') if INGAME_MUSIC_URL else 'null'},
            GAMEOVER_MUSIC_URL: {('"' + GAMEOVER_MUSIC_URL + '"') if GAMEOVER_MUSIC_URL else 'null'},
            
            // Sound Effects
            START_EFFECT_URL: {('"' + START_EFFECT_URL + '"') if START_EFFECT_URL else 'null'},
            COUNTDOWN_EFFECT_URL: {('"' + COUNTDOWN_EFFECT_URL + '"') if COUNTDOWN_EFFECT_URL else 'null'},
            JUMP_EFFECT_URL: {('"' + JUMP_EFFECT_URL + '"') if JUMP_EFFECT_URL else 'null'},
            SCORE_EFFECT_URL: {('"' + SCORE_EFFECT_URL + '"') if SCORE_EFFECT_URL else 'null'},
            HIGHSCORE_EFFECT_URL: {('"' + HIGHSCORE_EFFECT_URL + '"') if HIGHSCORE_EFFECT_URL else 'null'},
            RANDOM_EFFECT_URL: {('"' + RANDOM_EFFECT_URL + '"') if RANDOM_EFFECT_URL else 'null'},
            ELIMINATION_EFFECT_URL: {('"' + ELIMINATION_EFFECT_URL + '"') if ELIMINATION_EFFECT_URL else 'null'},
            
            // Game Settings
            GAME_SPEED: {game_speed},
            GRAVITY: {gravity_strength},
            JUMP_POWER: -{jump_power},
            PIPE_GAP: {pipe_gap}
        }};

        // Game State
        let gameState = {{
            // Audio objects
            menuAudio: null,
            ingameAudio: null,
            gameoverAudio: null,
            startEffect: null,
            countdownEffect: null,
            jumpEffect: null,
            scoreEffect: null,
            highscoreEffect: null,
            randomEffect: null,
            eliminationEffect: null,
            
            // Game state
            musicEnabled: true,
            gameRunning: false,
            gameOver: false,
            score: 0,
            player: {{ x: 100, y: 200, vy: 0, size: 50 }},
            pipes: [],
            pipeTimer: 0,
            lastTime: performance.now(),
            images: {{ bg: null, player: null, pipe: null }},
            countdownActive: false,
            countdownValue: 3,
            currentAudio: null
        }};

        // DOM Elements
        const elements = {{
            canvas: document.getElementById('gameCanvas'),
            startScreen: document.getElementById('startScreen'),
            gameOverScreen: document.getElementById('gameOverScreen'),
            countdown: document.getElementById('countdown'),
            score: document.getElementById('score'),
            finalScore: document.getElementById('finalScore'),
            musicToggle: document.getElementById('musicToggle'),
            startBtn: document.getElementById('startBtn'),
            mainStartBtn: document.getElementById('mainStartBtn'),
            restartBtn: document.getElementById('restartBtn'),
            audioStatus: document.getElementById('audioStatus')
        }};

        const ctx = elements.canvas.getContext('2d');

        // Initialize Game
        function initGame() {{
            setupEventListeners();
            loadAssets();
            setupAudio();
            resizeCanvas();
            renderMenu();
            startMenuMusic();
        }}

        // Setup Event Listeners
        function setupEventListeners() {{
            // Window resize
            window.addEventListener('resize', resizeCanvas);

            // Music toggle
            elements.musicToggle.addEventListener('click', toggleMusic);

            // Start buttons
            elements.mainStartBtn.addEventListener('click', startGame);
            elements.startBtn.addEventListener('click', startGame);
            elements.restartBtn.addEventListener('click', restartGame);

            // Game controls
            window.addEventListener('keydown', (e) => {{
                if (e.code === 'Space' || e.key === 'ArrowUp') flap();
            }});
            elements.canvas.addEventListener('mousedown', flap);
            elements.canvas.addEventListener('touchstart', (e) => {{
                e.preventDefault();
                flap();
            }}, {{passive: false}});
        }}

        // Audio Management - FIXED: No mixing of music
        function setupAudio() {{
            // Background Music
            if (CONFIG.MENU_MUSIC_URL) {{
                gameState.menuAudio = new Audio(CONFIG.MENU_MUSIC_URL);
                gameState.menuAudio.loop = true;
                gameState.menuAudio.volume = 0.5;
            }}
            if (CONFIG.INGAME_MUSIC_URL) {{
                gameState.ingameAudio = new Audio(CONFIG.INGAME_MUSIC_URL);
                gameState.ingameAudio.loop = true;
                gameState.ingameAudio.volume = 0.5;
            }}
            if (CONFIG.GAMEOVER_MUSIC_URL) {{
                gameState.gameoverAudio = new Audio(CONFIG.GAMEOVER_MUSIC_URL);
                gameState.gameoverAudio.volume = 0.5;
            }}

            // Sound Effects
            if (CONFIG.START_EFFECT_URL) {{
                gameState.startEffect = new Audio(CONFIG.START_EFFECT_URL);
                gameState.startEffect.volume = 0.7;
            }}
            if (CONFIG.COUNTDOWN_EFFECT_URL) {{
                gameState.countdownEffect = new Audio(CONFIG.COUNTDOWN_EFFECT_URL);
                gameState.countdownEffect.volume = 0.7;
            }}
            if (CONFIG.JUMP_EFFECT_URL) {{
                gameState.jumpEffect = new Audio(CONFIG.JUMP_EFFECT_URL);
                gameState.jumpEffect.volume = 0.6;
            }}
            if (CONFIG.SCORE_EFFECT_URL) {{
                gameState.scoreEffect = new Audio(CONFIG.SCORE_EFFECT_URL);
                gameState.scoreEffect.volume = 0.7;
            }}
            if (CONFIG.HIGHSCORE_EFFECT_URL) {{
                gameState.highscoreEffect = new Audio(CONFIG.HIGHSCORE_EFFECT_URL);
                gameState.highscoreEffect.volume = 0.7;
            }}
            if (CONFIG.RANDOM_EFFECT_URL) {{
                gameState.randomEffect = new Audio(CONFIG.RANDOM_EFFECT_URL);
                gameState.randomEffect.volume = 0.6;
            }}
            if (CONFIG.ELIMINATION_EFFECT_URL) {{
                gameState.eliminationEffect = new Audio(CONFIG.ELIMINATION_EFFECT_URL);
                gameState.eliminationEffect.volume = 0.7;
            }}

            // Load music preference
            try {{
                const saved = localStorage.getItem('flappy_music_enabled');
                if (saved !== null) gameState.musicEnabled = saved === '1';
                updateMusicButton();
            }} catch (e) {{}}
        }}

        function stopAllBackgroundMusic() {{
            if (gameState.menuAudio) {{
                gameState.menuAudio.pause();
                gameState.menuAudio.currentTime = 0;
            }}
            if (gameState.ingameAudio) {{
                gameState.ingameAudio.pause();
                gameState.ingameAudio.currentTime = 0;
            }}
            if (gameState.gameoverAudio) {{
                gameState.gameoverAudio.pause();
                gameState.gameoverAudio.currentTime = 0;
            }}
        }}

        function startMenuMusic() {{
            if (!gameState.musicEnabled) return;
            stopAllBackgroundMusic();
            if (gameState.menuAudio) {{
                gameState.menuAudio.play().catch(() => {{}});
                gameState.currentAudio = 'menu';
                elements.audioStatus.textContent = '🎵 Menu Music';
            }}
        }}

        function startGameMusic() {{
            if (!gameState.musicEnabled) return;
            stopAllBackgroundMusic();
            if (gameState.ingameAudio) {{
                gameState.ingameAudio.play().catch(() => {{}});
                gameState.currentAudio = 'ingame';
                elements.audioStatus.textContent = '🎮 Game Music';
            }}
        }}

        function startGameOverMusic() {{
            if (!gameState.musicEnabled) return;
            stopAllBackgroundMusic();
            if (gameState.gameoverAudio) {{
                gameState.gameoverAudio.play().catch(() => {{}});
                gameState.currentAudio = 'gameover';
                elements.audioStatus.textContent = '💀 Game Over Music';
            }}
        }}

        function playSoundEffect(audio, type = 'random') {{
            if (!gameState.musicEnabled || !audio) return;
            try {{
                audio.currentTime = 0;
                audio.play().catch(() => {{}});
                if (type !== 'random') {{
                    elements.audioStatus.textContent = `🔊 ${{type}} Effect`;
                    setTimeout(() => {{
                        // Restore current music status after effect
                        if (gameState.currentAudio === 'menu') {{
                            elements.audioStatus.textContent = '🎵 Menu Music';
                        }} else if (gameState.currentAudio === 'ingame') {{
                            elements.audioStatus.textContent = '🎮 Game Music';
                        }} else if (gameState.currentAudio === 'gameover') {{
                            elements.audioStatus.textContent = '💀 Game Over Music';
                        }}
                    }}, 2000);
                }}
            }} catch (e) {{}}
        }}

        function toggleMusic() {{
            gameState.musicEnabled = !gameState.musicEnabled;
            updateMusicButton();
            try {{
                localStorage.setItem('flappy_music_enabled', gameState.musicEnabled ? '1' : '0');
            }} catch (e) {{}}

            if (!gameState.musicEnabled) {{
                stopAllBackgroundMusic();
                elements.audioStatus.textContent = '🔇 Music Off';
            }} else {{
                // Restore appropriate music based on current state
                if (gameState.gameOver) {{
                    startGameOverMusic();
                }} else if (gameState.gameRunning) {{
                    startGameMusic();
                }} else {{
                    startMenuMusic();
                }}
            }}
        }}

        function updateMusicButton() {{
            elements.musicToggle.textContent = gameState.musicEnabled ? '🔊 Music ON' : '🔇 Music OFF';
        }}

        // Asset Loading
        function loadImage(url) {{
            return new Promise((resolve, reject) => {{
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = reject;
                img.src = url;
            }});
        }}

        async function loadAssets() {{
            try {{
                if (CONFIG.BG_URL) gameState.images.bg = await loadImage(CONFIG.BG_URL);
                if (CONFIG.PLAYER_URL) gameState.images.player = await loadImage(CONFIG.PLAYER_URL);
                if (CONFIG.PIPE_URL) gameState.images.pipe = await loadImage(CONFIG.PIPE_URL);
            }} catch (error) {{
                console.warn('Failed to load some assets:', error);
            }}
        }}

        // Game Flow
        function startGame() {{
            elements.startScreen.style.display = 'none';
            gameState.gameRunning = true;
            gameState.gameOver = false;
            
            // Play start effect
            playSoundEffect(gameState.startEffect, 'Game Start');
            
            startCountdown();
        }}

        function startCountdown() {{
            gameState.countdownActive = true;
            gameState.countdownValue = 3;
            elements.countdown.style.display = 'block';
            elements.countdown.textContent = gameState.countdownValue;

            // Play countdown effect for first number
            playSoundEffect(gameState.countdownEffect, 'Countdown');

            const countdownInterval = setInterval(() => {{
                gameState.countdownValue--;
                elements.countdown.textContent = gameState.countdownValue;

                // Play countdown effect for each number
                if (gameState.countdownValue > 0) {{
                    playSoundEffect(gameState.countdownEffect, 'Countdown');
                }}

                if (gameState.countdownValue <= 0) {{
                    clearInterval(countdownInterval);
                    elements.countdown.style.display = 'none';
                    gameState.countdownActive = false;
                    resetGame();
                    gameState.lastTime = performance.now();
                    
                    // Start game music after countdown
                    startGameMusic();
                    
                    requestAnimationFrame(gameLoop);
                }}
            }}, 1000);
        }}

        function restartGame() {{
            elements.gameOverScreen.style.display = 'none';
            startGame();
        }}

        function endGame() {{
            gameState.gameRunning = false;
            gameState.gameOver = true;

            // Play elimination effect
            playSoundEffect(gameState.eliminationEffect, 'Game Over');
            
            elements.finalScore.textContent = gameState.score;
            elements.gameOverScreen.style.display = 'flex';

            // Start game over music
            startGameOverMusic();

            // Save best score
            try {{
                const best = parseInt(localStorage.getItem('flappy_best') || '0');
                if (gameState.score > best) {{
                    localStorage.setItem('flappy_best', gameState.score.toString());
                }}
            }} catch (e) {{}}
        }}

        // Game Logic
        function resetGame() {{
            gameState.score = 0;
            gameState.player.y = elements.canvas.height / 2;
            gameState.player.vy = 0;
            gameState.pipes = [];
            gameState.pipeTimer = 0;
            elements.score.textContent = '0';
        }}

        function spawnPipe() {{
            const margin = elements.canvas.height * 0.15;
            const center = Math.random() * (elements.canvas.height - margin * 2 - CONFIG.PIPE_GAP) + margin + CONFIG.PIPE_GAP / 2;
            gameState.pipes.push({{ x: elements.canvas.width + 100, center, scored: false }});
        }}

        function update(deltaTime) {{
            if (!gameState.gameRunning || gameState.gameOver || gameState.countdownActive) return;

            // Spawn pipes
            gameState.pipeTimer += deltaTime;
            if (gameState.pipeTimer > 1800) {{
                gameState.pipeTimer = 0;
                spawnPipe();
            }}

            // Update pipes
            gameState.pipes.forEach(pipe => {{
                pipe.x -= (CONFIG.GAME_SPEED * 0.8) * (deltaTime / 16);
            }});

            // Remove off-screen pipes
            if (gameState.pipes.length > 0 && gameState.pipes[0].x + 120 < 0) {{
                gameState.pipes.shift();
            }}

            // Update player
            gameState.player.vy += CONFIG.GRAVITY * (deltaTime / 16);
            gameState.player.y += gameState.player.vy * (deltaTime / 16);

            // Check collisions
            checkCollisions();

            // Check boundaries
            if (gameState.player.y + gameState.player.size > elements.canvas.height - 10) {{
                endGame();
            }}
            if (gameState.player.y < 0) {{
                gameState.player.y = 0;
                gameState.player.vy = 0;
            }}
        }}

        function checkCollisions() {{
            const playerRect = {{
                x: gameState.player.x,
                y: gameState.player.y,
                width: gameState.player.size,
                height: gameState.player.size
            }};

            for (const pipe of gameState.pipes) {{
                const pipeWidth = elements.canvas.width * 0.08;
                const topHeight = pipe.center - (CONFIG.PIPE_GAP / 2);
                const bottomY = pipe.center + (CONFIG.PIPE_GAP / 2);

                // Score point
                if (!pipe.scored && pipe.x + pipeWidth < gameState.player.x) {{
                    pipe.scored = true;
                    gameState.score++;
                    elements.score.textContent = gameState.score;
                    
                    // Play score effect based on score range
                    if (gameState.score <= 5) {{
                        playSoundEffect(gameState.scoreEffect, 'Score');
                    }} else {{
                        playSoundEffect(gameState.highscoreEffect, 'High Score');
                    }}
                }}

                // Collision detection
                const topPipe = {{ x: pipe.x, y: 0, width: pipeWidth, height: topHeight }};
                const bottomPipe = {{ x: pipe.x, y: bottomY, width: pipeWidth, height: elements.canvas.height - bottomY }};

                if (checkRectCollision(playerRect, topPipe) || checkRectCollision(playerRect, bottomPipe)) {{
                    endGame();
                    return;
                }}
            }}
        }}

        function checkRectCollision(rect1, rect2) {{
            return rect1.x < rect2.x + rect2.width &&
                   rect1.x + rect1.width > rect2.x &&
                   rect1.y < rect2.y + rect2.height &&
                   rect1.y + rect1.height > rect2.y;
        }}

        function flap() {{
            if (!game
