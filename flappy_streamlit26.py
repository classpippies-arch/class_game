import streamlit as st
import base64
import os

st.set_page_config(page_title="Flappy Bird Game", layout="wide")

st.title("Flappy Bird – Streamlit Edition")
st.write("Tap/Click/Space to jump. Works on mobile + PC. Custom images and music loaded from your repository files.")

# ---------------------------
# Convert local files → base64 URLs
# ---------------------------
def file_to_data_url(filepath, mime):
    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

# Load local assets from repo
PLAYER = file_to_data_url("player_character.png", "image/png")
PIPE = file_to_data_url("obstacle_enemy.png", "image/png")
BG = file_to_data_url("background_image.png", "image/png")

# Choose any one music file from repo
MUSIC = file_to_data_url("ingame_music_1.mp3", "audio/mpeg")

# ---------------------------
# HTML + JS GAME ENGINE
# ---------------------------
game_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    margin: 0;
    background: black;
}}
canvas {{
    background: black;
    display: block;
    margin: auto;
    border-radius: 10px;
}}
#startBtn {{
    position: fixed;
    top: 12px;
    right: 12px;
    padding: 10px 15px;
    font-weight: bold;
    background: #ff4757;
    color: white;
    border: none;
    border-radius: 10px;
    z-index: 9999;
}}
</style>
</head>

<body>

<button id="startBtn">START / RESTART</button>
<canvas id="gameCanvas"></canvas>

<script>
// ----------- LOAD ASSETS FROM PYTHON -----------
const PLAYER_URL = "{PLAYER}";
const PIPE_URL = "{PIPE}";
const BG_URL = "{BG}";
const MUSIC_URL = "{MUSIC}";

// ----------- CANVAS SETUP -----------
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

function resizeCanvas() {{
    canvas.width = Math.min(window.innerWidth * 0.95, 900);
    canvas.height = Math.min(window.innerHeight * 0.75, 700);
}}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// ----------- GAME GLOBALS -----------
let gameRunning = false;
let gameOver = false;
let score = 0;

let player = {{
    x: 100,
    y: 250,
    vy: 0,
    size: 45
}};

let gravity = 0.5;
let jumpStrength = -9;

let pipes = [];
let pipeGap = 160;
let pipeSpeed = 3;

// Load images
let playerImg = new Image();
playerImg.src = PLAYER_URL;

let pipeImg = new Image();
pipeImg.src = PIPE_URL;

let bgImg = new Image();
bgImg.src = BG_URL;

// Load music
let bgMusic = new Audio(MUSIC_URL);
bgMusic.loop = true;

// ----------- GAME FUNCTIONS -----------

function resetGame() {{
    score = 0;
    pipes = [];
    player.y = 250;
    player.vy = 0;
    gameOver = false;
}}

function createPipe() {{
    let topPipeHeight = Math.random() * (canvas.height - pipeGap - 100) + 50;
    pipes.push({{
        x: canvas.width,
        top: topPipeHeight,
        bottom: topPipeHeight + pipeGap
    }});
}}

function update() {{
    if (!gameRunning || gameOver) {{
        draw();
        return;
    }}

    // gravity
    player.vy += gravity;
    player.y += player.vy;

    // add pipes
    if (pipes.length === 0 || pipes[pipes.length - 1].x < canvas.width - 250) {{
        createPipe();
    }}

    // move pipes
    for (let p of pipes) {{
        p.x -= pipeSpeed;
    }}

    // remove off-screen pipes
    pipes = pipes.filter(p => p.x + 80 > 0);

    // collision detection + scoring
    for (let p of pipes) {{
        if (player.x > p.x + 80 && !p.scored) {{
            score++;
            p.scored = true;
        }}

        if (
            player.x + player.size > p.x &&
            player.x < p.x + 80 &&
            (player.y < p.top || player.y + player.size > p.bottom)
        ) {{
            gameOver = true;
        }}
    }}

    // ground collision
    if (player.y + player.size > canvas.height) {{
        gameOver = true;
    }}

    draw();

    if (!gameOver) {{
        requestAnimationFrame(update);
    }} else {{
        ctx.fillStyle = "white";
        ctx.font = "40px Arial";
        ctx.fillText("GAME OVER", canvas.width/2 - 110, canvas.height/2);
    }}
}}

function draw() {{
    ctx.drawImage(bgImg, 0, 0, canvas.width, canvas.height);

    // draw pipes
    for (let p of pipes) {{
        ctx.drawImage(pipeImg, p.x, 0, 80, p.top);
        ctx.drawImage(pipeImg, p.x, p.bottom, 80, canvas.height - p.bottom);
    }}

    // draw player
    ctx.drawImage(playerImg, player.x, player.y, player.size, player.size);

    // draw score
    ctx.fillStyle = "white";
    ctx.font = "30px Arial";
    ctx.fillText("Score: " + score, 20, 40);
}}

function jump() {{
    if (!gameRunning) return;
    player.vy = jumpStrength;
}}

// ----------- CONTROLS -----------
document.addEventListener("keydown", (e) => {{
    if (e.code === "Space") jump();
}});

canvas.addEventListener("mousedown", jump);
canvas.addEventListener("touchstart", (e) => {{
    e.preventDefault();
    jump();
}});

// ----------- START BUTTON -----------
document.getElementById("startBtn").addEventListener("click", () => {{
    bgMusic.play().catch(() => {{}})
    gameRunning = true;
    resetGame();
    update();
}});

// initial draw
draw();
</script>

</body>
</html>
"""

# Render HTML game
st.components.v1.html(game_html, height=750, scrolling=False)
