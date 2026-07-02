from flask import Flask, render_template_string

app = Flask(__name__)

INDEX_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tetris</title>
<style>
  :root {
    --bg: #0f1117;
    --panel: #181b24;
    --border: #2a2f3d;
    --text: #e6e8ef;
    --muted: #8a90a3;
    --accent: #5b8cff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: 'Courier New', monospace;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .app {
    display: flex;
    gap: 24px;
    align-items: flex-start;
  }
  .board-wrap {
    position: relative;
    background: var(--panel);
    border: 2px solid var(--border);
    border-radius: 8px;
    padding: 8px;
  }
  #board {
    display: block;
    background: #0a0c11;
    border-radius: 4px;
  }
  .overlay {
    position: absolute;
    top: 8px; left: 8px; right: 8px; bottom: 8px;
    background: rgba(10, 12, 17, 0.88);
    border-radius: 4px;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 10px;
  }
  .overlay.show { display: flex; }
  .overlay h2 {
    margin: 0;
    font-size: 22px;
    letter-spacing: 2px;
    color: var(--accent);
  }
  .overlay p { margin: 0; color: var(--muted); font-size: 13px; }
  .overlay button {
    background: var(--accent);
    color: #0a0c11;
    border: none;
    padding: 8px 18px;
    border-radius: 4px;
    font-family: inherit;
    font-weight: bold;
    cursor: pointer;
    font-size: 13px;
    letter-spacing: 1px;
  }
  .overlay button:hover { opacity: 0.85; }
  .side {
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 180px;
  }
  .panel {
    background: var(--panel);
    border: 2px solid var(--border);
    border-radius: 8px;
    padding: 14px;
  }
  .panel h3 {
    margin: 0 0 10px 0;
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--muted);
    text-transform: uppercase;
  }
  #next-canvas {
    display: block;
    margin: 0 auto;
    background: #0a0c11;
    border-radius: 4px;
  }
  .stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    padding: 4px 0;
  }
  .stat-row .label { color: var(--muted); }
  .stat-row .value { color: var(--text); font-weight: bold; }
  .controls-list {
    font-size: 11px;
    color: var(--muted);
    line-height: 1.8;
  }
  .controls-list b { color: var(--text); }
  h1 {
    font-size: 18px;
    letter-spacing: 4px;
    margin: 0 0 14px 0;
    color: var(--accent);
    text-align: center;
  }
  .title-wrap { display: flex; flex-direction: column; }
</style>
</head>
<body>
  <div class="app">
    <div class="title-wrap">
      <h1>TETRIS</h1>
      <div class="board-wrap">
        <canvas id="board"></canvas>
        <div class="overlay" id="overlay">
          <h2 id="overlay-title">PAUSED</h2>
          <p id="overlay-text">Press P to resume</p>
          <button id="overlay-btn" style="display:none;">RESTART</button>
        </div>
      </div>
    </div>
    <div class="side">
      <div class="panel">
        <h3>Next</h3>
        <canvas id="next-canvas" width="100" height="100"></canvas>
      </div>
      <div class="panel">
        <h3>Stats</h3>
        <div class="stat-row"><span class="label">Score</span><span class="value" id="score">0</span></div>
        <div class="stat-row"><span class="label">Lines</span><span class="value" id="lines">0</span></div>
        <div class="stat-row"><span class="label">Level</span><span class="value" id="level">1</span></div>
      </div>
      <div class="panel">
        <h3>Controls</h3>
        <div class="controls-list">
          <div><b>&larr; &rarr;</b> Move</div>
          <div><b>&uarr; / X</b> Rotate CW</div>
          <div><b>Z</b> Rotate CCW</div>
          <div><b>&darr;</b> Soft drop</div>
          <div><b>Space</b> Hard drop</div>
          <div><b>P</b> Pause</div>
          <div><b>R</b> Restart</div>
        </div>
      </div>
    </div>
  </div>

<script>
(function () {
  const COLS = 10;
  const ROWS = 20;
  const BLOCK = 30;

  const boardCanvas = document.getElementById('board');
  boardCanvas.width = COLS * BLOCK;
  boardCanvas.height = ROWS * BLOCK;
  const ctx = boardCanvas.getContext('2d');

  const nextCanvas = document.getElementById('next-canvas');
  const nextCtx = nextCanvas.getContext('2d');

  const scoreEl = document.getElementById('score');
  const linesEl = document.getElementById('lines');
  const levelEl = document.getElementById('level');
  const overlay = document.getElementById('overlay');
  const overlayTitle = document.getElementById('overlay-title');
  const overlayText = document.getElementById('overlay-text');
  const overlayBtn = document.getElementById('overlay-btn');

  const COLORS = {
    I: '#00d3d3',
    J: '#3461e8',
    L: '#f0a020',
    O: '#f0e000',
    S: '#30c030',
    T: '#a030d0',
    Z: '#e03030'
  };

  const SHAPES = {
    I: [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    J: [[1,0,0],[1,1,1],[0,0,0]],
    L: [[0,0,1],[1,1,1],[0,0,0]],
    O: [[1,1],[1,1]],
    S: [[0,1,1],[1,1,0],[0,0,0]],
    T: [[0,1,0],[1,1,1],[0,0,0]],
    Z: [[1,1,0],[0,1,1],[0,0,0]]
  };

  const TYPES = Object.keys(SHAPES);

  function makeEmptyBoard() {
    const b = [];
    for (let r = 0; r < ROWS; r++) {
      b.push(new Array(COLS).fill(null));
    }
    return b;
  }

  function rotateCW(matrix) {
    const n = matrix.length;
    const result = [];
    for (let i = 0; i < n; i++) {
      result.push(new Array(n).fill(0));
    }
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        result[i][j] = matrix[n - 1 - j][i];
      }
    }
    return result;
  }

  function rotateCCW(matrix) {
    const n = matrix.length;
    const result = [];
    for (let i = 0; i < n; i++) {
      result.push(new Array(n).fill(0));
    }
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        result[i][j] = matrix[j][n - 1 - i];
      }
    }
    return result;
  }

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  let bag = [];
  function nextType() {
    if (bag.length === 0) {
      bag = shuffle(TYPES.slice());
    }
    return bag.pop();
  }

  function newPiece(type) {
    return {
      type: type,
      matrix: SHAPES[type].map(row => row.slice()),
      row: 0,
      col: Math.floor((COLS - SHAPES[type].length) / 2)
    };
  }

  let board, current, next, score, lines, level, dropCounter, dropInterval;
  let paused, gameOver, lastTime, rafId;

  function resetGame() {
    board = makeEmptyBoard();
    bag = [];
    current = newPiece(nextType());
    next = newPiece(nextType());
    score = 0;
    lines = 0;
    level = 1;
    dropCounter = 0;
    dropInterval = 1000;
    paused = false;
    gameOver = false;
    lastTime = 0;
    updateStats();
    hideOverlay();
  }

  function updateStats() {
    scoreEl.textContent = score;
    linesEl.textContent = lines;
    levelEl.textContent = level;
  }

  function collides(matrix, row, col) {
    for (let r = 0; r < matrix.length; r++) {
      for (let c = 0; c < matrix[r].length; c++) {
        if (!matrix[r][c]) continue;
        const br = row + r;
        const bc = col + c;
        if (bc < 0 || bc >= COLS || br >= ROWS) return true;
        if (br >= 0 && board[br][bc]) return true;
      }
    }
    return false;
  }

  function lockPiece() {
    for (let r = 0; r < current.matrix.length; r++) {
      for (let c = 0; c < current.matrix[r].length; c++) {
        if (current.matrix[r][c]) {
          const br = current.row + r;
          const bc = current.col + c;
          if (br >= 0 && br < ROWS && bc >= 0 && bc < COLS) {
            board[br][bc] = COLORS[current.type];
          }
        }
      }
    }
    clearLines();
    current = next;
    next = newPiece(nextType());
    if (collides(current.matrix, current.row, current.col)) {
      triggerGameOver();
    }
  }

  function clearLines() {
    let cleared = 0;
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r].every(cell => cell !== null)) {
        board.splice(r, 1);
        board.unshift(new Array(COLS).fill(null));
        cleared++;
        r++;
      }
    }
    if (cleared > 0) {
      const lineScores = [0, 100, 300, 500, 800];
      score += (lineScores[cleared] || 800) * level;
      lines += cleared;
      const newLevel = Math.floor(lines / 10) + 1;
      if (newLevel !== level) {
        level = newLevel;
        dropInterval = Math.max(100, 1000 - (level - 1) * 80);
      }
      updateStats();
    }
  }

  function move(dCol) {
    if (paused || gameOver) return;
    if (!collides(current.matrix, current.row, current.col + dCol)) {
      current.col += dCol;
      draw();
    }
  }

  function softDrop() {
    if (paused || gameOver) return;
    if (!collides(current.matrix, current.row + 1, current.col)) {
      current.row += 1;
      score += 1;
      updateStats();
      dropCounter = 0;
      draw();
    } else {
      lockPiece();
      draw();
    }
  }

  function hardDrop() {
    if (paused || gameOver) return;
    let dist = 0;
    while (!collides(current.matrix, current.row + 1, current.col)) {
      current.row += 1;
      dist++;
    }
    score += dist * 2;
    updateStats();
    lockPiece();
    dropCounter = 0;
    draw();
  }

  function rotate(dir) {
    if (paused || gameOver) return;
    const rotated = dir === 1 ? rotateCW(current.matrix) : rotateCCW(current.matrix);
    const kicks = [0, -1, 1, -2, 2];
    for (const k of kicks) {
      if (!collides(rotated, current.row, current.col + k)) {
        current.matrix = rotated;
        current.col += k;
        draw();
        return;
      }
    }
  }

  function triggerGameOver() {
    gameOver = true;
    overlayTitle.textContent = 'GAME OVER';
    overlayText.textContent = 'Score: ' + score;
    overlayBtn.style.display = 'inline-block';
    overlay.classList.add('show');
  }

  function showPauseOverlay() {
    overlayTitle.textContent = 'PAUSED';
    overlayText.textContent = 'Press P to resume';
    overlayBtn.style.display = 'none';
    overlay.classList.add('show');
  }

  function hideOverlay() {
    overlay.classList.remove('show');
  }

  function togglePause() {
    if (gameOver) return;
    paused = !paused;
    if (paused) {
      showPauseOverlay();
    } else {
      hideOverlay();
      lastTime = performance.now();
    }
  }

  function drawCell(c, ctxRef, x, y, size, color) {
    ctxRef.fillStyle = color;
    ctxRef.fillRect(x, y, size, size);
    ctxRef.strokeStyle = 'rgba(0,0,0,0.35)';
    ctxRef.lineWidth = 2;
    ctxRef.strokeRect(x + 1, y + 1, size - 2, size - 2);
    ctxRef.strokeStyle = 'rgba(255,255,255,0.15)';
    ctxRef.lineWidth = 1;
    ctxRef.strokeRect(x + 2, y + 2, size - 4, size - 4);
  }

  function draw() {
    ctx.clearRect(0, 0, boardCanvas.width, boardCanvas.height);

    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let c = 0; c <= COLS; c++) {
      ctx.beginPath();
      ctx.moveTo(c * BLOCK, 0);
      ctx.lineTo(c * BLOCK, ROWS * BLOCK);
      ctx.stroke();
    }
    for (let r = 0; r <= ROWS; r++) {
      ctx.beginPath();
      ctx.moveTo(0, r * BLOCK);
      ctx.lineTo(COLS * BLOCK, r * BLOCK);
      ctx.stroke();
    }

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        if (board[r][c]) {
          drawCell(null, ctx, c * BLOCK, r * BLOCK, BLOCK, board[r][c]);
        }
      }
    }

    if (current && !gameOver) {
      for (let r = 0; r < current.matrix.length; r++) {
        for (let c = 0; c < current.matrix[r].length; c++) {
          if (current.matrix[r][c]) {
            const br = current.row + r;
            const bc = current.col + c;
            if (br >= 0) {
              drawCell(null, ctx, bc * BLOCK, br * BLOCK, BLOCK, COLORS[current.type]);
            }
          }
        }
      }
    }

    nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
    if (next) {
      const m = next.matrix;
      const n = m.length;
      const size = 20;
      const offsetX = (nextCanvas.width - n * size) / 2;
      const offsetY = (nextCanvas.height - n * size) / 2;
      for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
          if (m[r][c]) {
            drawCell(null, nextCtx, offsetX + c * size, offsetY + r * size, size, COLORS[next.type]);
          }
        }
      }
    }
  }

  function update(time) {
    if (!lastTime) lastTime = time;
    const delta = time - lastTime;
    lastTime = time;

    if (!paused && !gameOver) {
      dropCounter += delta;
      if (dropCounter > dropInterval) {
        if (!collides(current.matrix, current.row + 1, current.col)) {
          current.row += 1;
        } else {
          lockPiece();
        }
        dropCounter = 0;
        draw();
      }
    }
    rafId = requestAnimationFrame(update);
  }

  document.addEventListener('keydown', (e) => {
    switch (e.code) {
      case 'ArrowLeft':
        e.preventDefault();
        move(-1);
        break;
      case 'ArrowRight':
        e.preventDefault();
        move(1);
        break;
      case 'ArrowDown':
        e.preventDefault();
        softDrop();
        break;
      case 'ArrowUp':
      case 'KeyX':
        e.preventDefault();
        rotate(1);
        break;
      case 'KeyZ':
        e.preventDefault();
        rotate(-1);
        break;
      case 'Space':
        e.preventDefault();
        hardDrop();
        break;
      case 'KeyP':
        e.preventDefault();
        togglePause();
        break;
      case 'KeyR':
        e.preventDefault();
        resetGame();
        draw();
        break;
    }
  });

  overlayBtn.addEventListener('click', () => {
    resetGame();
    draw();
  });

  resetGame();
  draw();
  rafId = requestAnimationFrame(update);
})();
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)