            }
        }

        function flap() {
            if (!gameState.gameRunning || gameState.gameOver || gameState.countdownActive) return;
            gameState.player.vy = CONFIG.JUMP_POWER;

            // Play jump sound
            playSoundEffect(gameState.jumpEffect, 'Jump');
        }

        function resizeCanvas() {
            elements.canvas.width = elements.canvas.clientWidth;
            elements.canvas.height = elements.canvas.clientHeight;
        }

        function render() {
            // Clear
            ctx.clearRect(0, 0, elements.canvas.width, elements.canvas.height);

            // Draw background if available
            if (gameState.images.bg) {
                // cover-style draw
                ctx.drawImage(gameState.images.bg, 0, 0, elements.canvas.width, elements.canvas.height);
            } else {
                ctx.fillStyle = '#000';
                ctx.fillRect(0, 0, elements.canvas.width, elements.canvas.height);
            }

            // Draw pipes
            const pipeWidth = elements.canvas.width * 0.08;
            for (const pipe of gameState.pipes) {
                const topHeight = pipe.center - (CONFIG.PIPE_GAP / 2);
                const bottomY = pipe.center + (CONFIG.PIPE_GAP / 2);

                // top
                if (gameState.images.pipe) {
                    ctx.drawImage(gameState.images.pipe, pipe.x, 0, pipeWidth, topHeight);
                } else {
                    ctx.fillStyle = '#2ecc71';
                    ctx.fillRect(pipe.x, 0, pipeWidth, topHeight);
                }

                // bottom
                if (gameState.images.pipe) {
                    ctx.drawImage(gameState.images.pipe, pipe.x, bottomY, pipeWidth, elements.canvas.height - bottomY);
                } else {
                    ctx.fillStyle = '#2ecc71';
                    ctx.fillRect(pipe.x, bottomY, pipeWidth, elements.canvas.height - bottomY);
                }
            }

            // Draw player
            if (gameState.images.player) {
                ctx.drawImage(gameState.images.player, gameState.player.x, gameState.player.y, gameState.player.size, gameState.player.size);
            } else {
                ctx.fillStyle = '#ffd93d';
                ctx.fillRect(gameState.player.x, gameState.player.y, gameState.player.size, gameState.player.size);
            }
        }

        function gameLoop(timestamp) {
            const deltaTime = timestamp - gameState.lastTime;
            gameState.lastTime = timestamp;

            update(deltaTime);
            render();

            if (gameState.gameRunning && !gameState.gameOver) {
                requestAnimationFrame(gameLoop);
            }
        }

        initGame();
    </script>
</body>
</html>
'''
# --- End of HTML game string ---

# Embed into Streamlit app (Python side)
# Use streamlit components to show the HTML/JS game
try:
    components.html(game_html, height=900, scrolling=True)
except Exception as e:
    st.error(f"Failed to render game HTML: {e}")
