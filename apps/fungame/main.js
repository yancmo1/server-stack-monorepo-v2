// main.js - Glasslight Drift
// A compact Phaser 3 game: guide a glowing Glassfly to collect Petals and avoid Moths.

const WIDTH = window.innerWidth;
const HEIGHT = window.innerHeight;

const config = {
  type: Phaser.AUTO,
  width: Math.max(800, WIDTH * 0.95),
  height: Math.max(600, HEIGHT * 0.85),
  parent: 'game-container',
  backgroundColor: 0x071019,
  physics: {
    default: 'arcade',
    arcade: { debug: false }
  },
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  scene: {
    preload: preload,
    create: create,
    update: update
  }
};

const game = new Phaser.Game(config);

let player, cursors, pointer;
let petals, moths, particles, bgStars;
let score = 0, scoreText, energy = 100, energyBar;
let gameOver = false, startText, music;
let lastPetalTime = 0;

let audioCtx = null;
let musicNodes = null;
function ensureAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}
function playBeep(freq = 440, type = 'sine', duration = 0.12, volume = 0.06) {
  try {
    ensureAudio();
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.value = volume;
    o.connect(g);
    g.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    o.start(now);
    g.gain.setValueAtTime(volume, now);
    g.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    o.stop(now + duration + 0.02);
  } catch (e) {
    // ignore if AudioContext unavailable
  }
}
function startMusic() {
  try {
    ensureAudio();
    if (musicNodes) return;
    const g = audioCtx.createGain(); g.gain.value = 0.03; g.connect(audioCtx.destination);
    const o = audioCtx.createOscillator(); o.type = 'sine'; o.frequency.value = 55; o.connect(g); o.start();
    musicNodes = { gain: g, osc: o };
  } catch (e) {}
}
function stopMusic() {
  try {
    if (!musicNodes) return;
    musicNodes.osc.stop(); musicNodes.gain.disconnect(); musicNodes = null;
  } catch (e) {}
}

function preload() {
  // No external image/audio preloads to avoid local CORS/data-URI issues.
  // All textures are generated at runtime in create().
}

function create() {
  // Generate textures on the fly to avoid loading external data URIs (which fail on file://)
  const cam = this.cameras.main;

  // helper canvas texture creators
  function createCircleCanvas(size, colorInner, colorOuter) {
    const c = document.createElement('canvas'); c.width = size; c.height = size; const ctx = c.getContext('2d');
    const grad = ctx.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2);
    grad.addColorStop(0, colorInner); grad.addColorStop(1, colorOuter);
    ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(size/2, size/2, size/2 - 0.5, 0, Math.PI*2); ctx.fill();
    return c;
  }
  function createPetalCanvas(size, colorInner, colorOuter) {
    const s = size; const c = document.createElement('canvas'); c.width = s; c.height = s; const ctx = c.getContext('2d');
    ctx.translate(s/2, s/2); ctx.rotate(-0.6);
    const grad = ctx.createLinearGradient(-s/2, -s/2, s/2, s/2); grad.addColorStop(0, colorInner); grad.addColorStop(1, colorOuter);
    ctx.fillStyle = grad; ctx.beginPath(); ctx.moveTo(0,-s*0.45); ctx.bezierCurveTo(s*0.3,-s*0.1, s*0.2,s*0.3, 0,s*0.45); ctx.bezierCurveTo(-s*0.2,s*0.3, -s*0.3,-s*0.1, 0,-s*0.45); ctx.fill();
    return c;
  }
  function createMothCanvas(size, color1, color2) {
    const s = size; const c = document.createElement('canvas'); c.width = s; c.height = s; const ctx = c.getContext('2d');
    ctx.translate(s/2, s/2);
    const grad = ctx.createLinearGradient(-s/2, -s/2, s/2, s/2); grad.addColorStop(0, color1); grad.addColorStop(1, color2);
    ctx.fillStyle = grad; ctx.beginPath();
    ctx.moveTo(-s*0.4,0); ctx.quadraticCurveTo(-s*0.5,-s*0.25, -s*0.15,-s*0.35);
    ctx.quadraticCurveTo(-s*0.05,-s*0.38, 0,-s*0.25);
    ctx.quadraticCurveTo(s*0.05,-s*0.38, s*0.15,-s*0.35);
    ctx.quadraticCurveTo(s*0.5,-s*0.25, s*0.4,0);
    ctx.quadraticCurveTo(s*0.25,s*0.15, 0,s*0.45);
    ctx.quadraticCurveTo(-s*0.25,s*0.15, -s*0.4,0);
    ctx.fill();
    return c;
  }

  // Add textures
  this.textures.addCanvas('player', createCircleCanvas(48, '#bde6ff', '#6fc8ff'));
  this.textures.addCanvas('petal', createPetalCanvas(28, '#ffd7ff', '#ff9ad6'));
  this.textures.addCanvas('moth', createMothCanvas(64, '#13293d', '#0b2a3a'));
  this.textures.addCanvas('star', createCircleCanvas(6, '#cfeeff', '#9ad1ff'));
  this.textures.addCanvas('glow', createCircleCanvas(20, '#ffffff', '#9ad1ff'));

  // Background gradient using a generated canvas texture
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(800, cam.width);
  canvas.height = Math.max(600, cam.height);
  const ctx = canvas.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
  g.addColorStop(0, '#071019'); g.addColorStop(0.5, '#0f2233'); g.addColorStop(1, '#14293b');
  ctx.fillStyle = g; ctx.fillRect(0, 0, canvas.width, canvas.height);
  this.textures.addCanvas('bgGrad', canvas);
  this.add.image(cam.width/2, cam.height/2, 'bgGrad').setDisplaySize(cam.width, cam.height).setScrollFactor(0);

  // Stars background
  bgStars = this.add.particles('star');
  bgStars.createEmitter({ x: { min: 0, max: cam.width }, y: { min: 0, max: cam.height }, alpha: { start: 0.9, end: 0 }, scale: { start: 0.4, end: 0.1 }, lifespan: 6000, quantity: 2, frequency: 200 });

  // Player
  player = this.physics.add.image(cam.width/2, cam.height*0.6, 'player');
  player.setCollideWorldBounds(true);
  player.setDamping(true);
  player.setDrag(0.95);
  player.setMaxVelocity(400);
  player.speed = 280;

  // Petals group
  petals = this.physics.add.group();

  // Moths group
  moths = this.physics.add.group();

  // Particles for collection
  particles = this.add.particles('glow');

  // UI: Score & Energy
  scoreText = this.add.text(16, 16, 'Score: 0', { fontSize: '22px', fill: '#e6f7ff' });
  energyBar = this.add.graphics();
  drawEnergyBar(this, energyBar, energy);

  // Colliders
  this.physics.add.overlap(player, petals, collectPetal, null, this);
  this.physics.add.overlap(player, moths, hitMoth, null, this);

  // Input
  cursors = this.input.keyboard.createCursorKeys();
  this.input.keyboard.on('keydown-SPACE', () => { if (gameOver) restartScene.call(this); });
  this.input.on('pointerdown', () => { if (gameOver) restartScene.call(this); });

  // Start text
  startText = this.add.text(cam.width/2, cam.height/2, 'Click or press Space to start', { fontSize: '24px', fill: '#dff3ff' }).setOrigin(0.5);
  startText.setAlpha(0.9);

  // NOTE: Do NOT start timers or pause the scene here. Timers are created when the player starts.
  gameOver = true; // waiting to start
}

function startGame(scene) {
  // scene is 'this'
  const s = scene || this;
  // reset values
  score = 0; energy = 100; gameOver = false; lastPetalTime = s.time.now || 0;
  // hide start text
  if (startText) startText.setAlpha(0);
  // clear any existing groups
  if (petals) petals.clear(true, true);
  if (moths) moths.clear(true, true);
  // start music
  startMusic();
  // start timers
  s.petTimer = s.time.addEvent({ delay: 900, callback: spawnPetal, callbackScope: s, loop: true });
  s.mothTimer = s.time.addEvent({ delay: 1800, callback: spawnMoth, callbackScope: s, loop: true });
}

function update(time, delta) {
  if (!player || !player.body) return;

  if (gameOver) return;

  // Movement: follow pointer smoothly or use keyboard
  pointer = this.input.activePointer;
  const toX = pointer.isDown ? pointer.worldX : (cursors.left.isDown || cursors.right.isDown ? player.x + (cursors.right.isDown ? 5 : (cursors.left.isDown ? -5 : 0)) : player.x);
  const toY = pointer.isDown ? pointer.worldY : (cursors.up.isDown || cursors.down.isDown ? player.y + (cursors.down.isDown ? 5 : (cursors.up.isDown ? -5 : 0)) : player.y);

  if (pointer.isDown) {
    this.physics.moveTo(player, toX, toY, player.speed);
  } else if (cursors.left.isDown || cursors.right.isDown || cursors.up.isDown || cursors.down.isDown) {
    const vx = (cursors.right.isDown ? 1 : 0) + (cursors.left.isDown ? -1 : 0);
    const vy = (cursors.down.isDown ? 1 : 0) + (cursors.up.isDown ? -1 : 0);
    player.setVelocity(vx * player.speed, vy * player.speed);
  } else {
    player.setAcceleration(0);
    player.setVelocity(player.body.velocity.x * 0.96, player.body.velocity.y * 0.96);
  }

  // Rotate player slightly for motion effect
  player.rotation = Math.atan2(player.body.velocity.y, player.body.velocity.x) + Math.PI/2;

  // Keep things moving: increase difficulty slowly
  if (time - lastPetalTime > 10000) {
    lastPetalTime = time;
    this.mothTimer.delay = Math.max(600, this.mothTimer.delay * 0.92);
    this.petTimer.delay = Math.max(350, this.petTimer.delay * 0.96);
  }

  // Energy drain
  energy -= delta * 0.004; // drains slowly
  if (energy <= 0) {
    endGame.call(this);
  }
  drawEnergyBar(this, energyBar, energy);

  // Update score text
  scoreText.setText('Score: ' + score);
}

// Utility: draw energy bar
function drawEnergyBar(scene, gfx, value) {
  const cam = scene.cameras.main;
  const x = cam.width - 220, y = 18, w = 200, h = 16;
  gfx.clear();
  gfx.fillStyle(0x0b1320, 1);
  gfx.fillRoundedRect(x, y, w, h, 8);
  const pct = Phaser.Math.Clamp(value / 100, 0, 1);
  const color = Phaser.Display.Color.Interpolate.ColorWithColor(new Phaser.Display.Color(255, 80, 110), new Phaser.Display.Color(154, 209, 255), 100, pct * 100);
  const col = Phaser.Display.Color.GetColor(color.r, color.g, color.b);
  gfx.fillStyle(col, 1);
  gfx.fillRoundedRect(x + 4, y + 4, (w - 8) * pct, h - 8, 6);
}

function spawnPetal() {
  const cam = this.cameras.main;
  const x = Phaser.Math.Between(40, cam.width - 40);
  const y = Phaser.Math.Between(40, cam.height - 40);
  const p = petals.create(x, y, 'petal');
  p.setAlpha(0.95);
  p.setScale(Phaser.Math.FloatBetween(0.7, 1.1));
  p.setBounce(0.6);
  p.setVelocity(Phaser.Math.Between(-40,40), Phaser.Math.Between(-40,40));
  p.setCollideWorldBounds(true);
  p.setCircle(p.width*0.45);
  // subtle bob animation
  this.tweens.add({ targets: p, y: p.y + Phaser.Math.Between(-10,10), duration: 1200, yoyo: true, repeat: -1, ease: 'Sine.easeInOut' });
}

function spawnMoth() {
  const cam = this.cameras.main;
  // spawn from edges
  const side = Phaser.Math.Between(0,3);
  let x = 0, y = 0, vx = 0, vy = 0;
  const speed = Phaser.Math.Between(80, 160);
  if (side === 0) { x = -40; y = Phaser.Math.Between(20, cam.height-20); vx = speed; vy = Phaser.Math.Between(-40,40); }
  if (side === 1) { x = cam.width + 40; y = Phaser.Math.Between(20, cam.height-20); vx = -speed; vy = Phaser.Math.Between(-40,40); }
  if (side === 2) { x = Phaser.Math.Between(20, cam.width-20); y = -40; vx = Phaser.Math.Between(-40,40); vy = speed; }
  if (side === 3) { x = Phaser.Math.Between(20, cam.width-20); y = cam.height + 40; vx = Phaser.Math.Between(-40,40); vy = -speed; }
  const m = moths.create(x, y, 'moth');
  m.setAlpha(0.9);
  m.setScale(Phaser.Math.FloatBetween(0.9,1.4));
  m.setVelocity(vx, vy);
  m.setAngularVelocity(Phaser.Math.Between(-30,30));
  m.damage = Phaser.Math.Between(8, 16);
  m.setCircle(m.width*0.45);
  m.setCollideWorldBounds(false);
  // small life
  this.time.addEvent({ delay: 10000, callback: () => { if (m && m.destroy) m.destroy(); } });
}

function collectPetal(playerObj, petal) {
  if (!petal.active) return;
  petal.destroy();
  score += 10;
  energy = Math.min(100, energy + 12);
  // particle burst
  particles.createEmitter({ x: petal.x, y: petal.y, speed: { min: -120, max: 120 }, angle: { min: 0, max: 360 }, scale: { start: 0.6, end: 0 }, lifespan: 600, blendMode: 'ADD', quantity: 12 }).explode(12, petal.x, petal.y);
  try { playBeep(880, 'sine', 0.08, 0.06); } catch(e) {}
}

function hitMoth(playerObj, moth) {
  if (!moth.active) return;
  // small knockback
  const dx = player.x - moth.x; const dy = player.y - moth.y;
  const angle = Math.atan2(dy, dx);
  player.setVelocity(Math.cos(angle) * 240, Math.sin(angle) * 240);
  energy -= moth.damage;
  moth.destroy();
  try { playBeep(160, 'sawtooth', 0.18, 0.08); } catch(e) {}
}

function endGame() {
  gameOver = true;
  // remove timers so new game restarts cleanly
  try { if (this.petTimer) { this.petTimer.remove(false); this.petTimer = null; } } catch(e) {}
  try { if (this.mothTimer) { this.mothTimer.remove(false); this.mothTimer = null; } } catch(e) {}
  startText.setText('Game Over — Click or press Space to restart');
  startText.setAlpha(1);
  stopMusic();
}

function restartScene() {
  // Reset
  score = 0; energy = 100;
  if (petals) petals.clear(true, true);
  if (moths) moths.clear(true, true);
  // start the game
  startGame(this);
}

// Ensure input starts the game even if it's the first time
// Attach start handlers at top-level so clicks and Space start correctly
window.addEventListener('click', () => { if (gameOver) restartScene.call(game.scene.keys.default); });
window.addEventListener('keydown', (e) => { if (gameOver && e.code === 'Space') restartScene.call(game.scene.keys.default); });
