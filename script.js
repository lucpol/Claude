const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const scoreEl = document.getElementById("score");
const livesEl = document.getElementById("lives");
const chocosEl = document.getElementById("chocos");

const paddleImage = new Image();
paddleImage.src = "beagle.svg";

const state = {
  score: 0,
  lives: 3,
  chocolates: 0,
  running: true,
};

const paddle = {
  width: 150,
  height: 52,
  x: canvas.width / 2 - 75,
  y: canvas.height - 65,
  speed: 9,
  moveLeft: false,
  moveRight: false,
};

const ball = {
  x: canvas.width / 2,
  y: canvas.height - 100,
  radius: 10,
  dx: 5,
  dy: -5,
};

const brickConfig = {
  rows: 6,
  cols: 11,
  width: 68,
  height: 24,
  gap: 9,
  offsetTop: 55,
  offsetLeft: 34,
};

const bricks = [];
const chocolates = [];

for (let r = 0; r < brickConfig.rows; r += 1) {
  bricks[r] = [];
  for (let c = 0; c < brickConfig.cols; c += 1) {
    bricks[r][c] = {
      x: 0,
      y: 0,
      alive: true,
      hue: 25 + (r * 20 + c * 7) % 70,
    };
  }
}

function spawnChocolate(x, y) {
  chocolates.push({
    x,
    y,
    speed: 2 + Math.random() * 1.4,
    size: 16,
  });
}

function drawBall() {
  ctx.beginPath();
  ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
  ctx.fillStyle = "#ffe59f";
  ctx.shadowColor = "#ffc857";
  ctx.shadowBlur = 12;
  ctx.fill();
  ctx.shadowBlur = 0;
}

function drawPaddle() {
  if (paddleImage.complete) {
    ctx.drawImage(paddleImage, paddle.x, paddle.y, paddle.width, paddle.height);
    return;
  }
  ctx.fillStyle = "#d1a15f";
  ctx.fillRect(paddle.x, paddle.y, paddle.width, paddle.height);
}

function drawBricks() {
  for (let r = 0; r < brickConfig.rows; r += 1) {
    for (let c = 0; c < brickConfig.cols; c += 1) {
      const brick = bricks[r][c];
      if (!brick.alive) {
        continue;
      }
      const x = c * (brickConfig.width + brickConfig.gap) + brickConfig.offsetLeft;
      const y = r * (brickConfig.height + brickConfig.gap) + brickConfig.offsetTop;
      brick.x = x;
      brick.y = y;

      ctx.fillStyle = `hsl(${brick.hue}, 80%, 56%)`;
      ctx.fillRect(x, y, brickConfig.width, brickConfig.height);
      ctx.strokeStyle = "#2b1a0f";
      ctx.strokeRect(x, y, brickConfig.width, brickConfig.height);
    }
  }
}

function drawChocolates() {
  chocolates.forEach((choco) => {
    ctx.fillStyle = "#6b3d1f";
    ctx.fillRect(choco.x, choco.y, choco.size, choco.size);
    ctx.fillStyle = "#8f5a32";
    ctx.fillRect(choco.x + 2, choco.y + 2, choco.size - 4, choco.size - 4);
    ctx.fillStyle = "#f1c78f";
    ctx.fillRect(choco.x + 4, choco.y + 4, 4, 4);
  });
}

function collideBallWithBricks() {
  for (let r = 0; r < brickConfig.rows; r += 1) {
    for (let c = 0; c < brickConfig.cols; c += 1) {
      const brick = bricks[r][c];
      if (!brick.alive) {
        continue;
      }

      const withinX = ball.x > brick.x && ball.x < brick.x + brickConfig.width;
      const withinY = ball.y > brick.y && ball.y < brick.y + brickConfig.height;

      if (withinX && withinY) {
        ball.dy = -ball.dy;
        brick.alive = false;
        state.score += 10;
        if (Math.random() < 0.45) {
          spawnChocolate(brick.x + brickConfig.width / 2 - 8, brick.y + brickConfig.height / 2);
        }
      }
    }
  }
}

function updateChocolates() {
  for (let i = chocolates.length - 1; i >= 0; i -= 1) {
    const choco = chocolates[i];
    choco.y += choco.speed;

    const catchesX = choco.x + choco.size > paddle.x && choco.x < paddle.x + paddle.width;
    const catchesY = choco.y + choco.size > paddle.y && choco.y < paddle.y + paddle.height;

    if (catchesX && catchesY) {
      chocolates.splice(i, 1);
      state.chocolates += 1;
      state.score += 25;
      continue;
    }

    if (choco.y > canvas.height) {
      chocolates.splice(i, 1);
    }
  }
}

function updateHud() {
  scoreEl.textContent = `Puntos: ${state.score}`;
  livesEl.textContent = `Vidas: ${state.lives}`;
  chocosEl.textContent = `Chocolates: ${state.chocolates}`;
}

function drawGameOver(message) {
  ctx.fillStyle = "rgb(0 0 0 / 65%)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fff";
  ctx.font = "bold 54px Segoe UI";
  ctx.textAlign = "center";
  ctx.fillText(message, canvas.width / 2, canvas.height / 2);
  ctx.font = "24px Segoe UI";
  ctx.fillText("Recarga la página para jugar otra vez", canvas.width / 2, canvas.height / 2 + 42);
}

function handleWallCollisions() {
  if (ball.x + ball.dx > canvas.width - ball.radius || ball.x + ball.dx < ball.radius) {
    ball.dx = -ball.dx;
  }

  if (ball.y + ball.dy < ball.radius) {
    ball.dy = -ball.dy;
  } else if (ball.y + ball.dy > canvas.height - ball.radius) {
    const hitsPaddle = ball.x > paddle.x && ball.x < paddle.x + paddle.width;
    if (hitsPaddle) {
      const relativeIntersect = (ball.x - (paddle.x + paddle.width / 2)) / (paddle.width / 2);
      ball.dx = relativeIntersect * 6;
      ball.dy = -Math.abs(ball.dy);
    } else {
      state.lives -= 1;
      if (state.lives <= 0) {
        state.running = false;
      } else {
        ball.x = canvas.width / 2;
        ball.y = canvas.height - 100;
        ball.dx = 4 * (Math.random() > 0.5 ? 1 : -1);
        ball.dy = -4;
        paddle.x = canvas.width / 2 - paddle.width / 2;
      }
    }
  }
}

function updatePaddle() {
  if (paddle.moveRight && paddle.x < canvas.width - paddle.width) {
    paddle.x += paddle.speed;
  }
  if (paddle.moveLeft && paddle.x > 0) {
    paddle.x -= paddle.speed;
  }
}

function checkWin() {
  const alive = bricks.flat().some((brick) => brick.alive);
  if (!alive) {
    state.running = false;
    drawGameOver("¡Ganaste!");
    return true;
  }
  return false;
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawBricks();
  drawBall();
  drawPaddle();
  drawChocolates();
}

function tick() {
  if (!state.running) {
    drawGameOver("Juego terminado");
    return;
  }

  updatePaddle();
  handleWallCollisions();
  collideBallWithBricks();
  updateChocolates();

  ball.x += ball.dx;
  ball.y += ball.dy;

  updateHud();
  render();

  if (!checkWin()) {
    requestAnimationFrame(tick);
  }
}

document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") {
    paddle.moveRight = true;
  } else if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") {
    paddle.moveLeft = true;
  }
});

document.addEventListener("keyup", (event) => {
  if (event.key === "ArrowRight" || event.key.toLowerCase() === "d") {
    paddle.moveRight = false;
  } else if (event.key === "ArrowLeft" || event.key.toLowerCase() === "a") {
    paddle.moveLeft = false;
  }
});

canvas.addEventListener("mousemove", (event) => {
  const rect = canvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  paddle.x = Math.max(0, Math.min(mouseX - paddle.width / 2, canvas.width - paddle.width));
});

updateHud();
requestAnimationFrame(tick);
