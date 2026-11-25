// Turntable player: plays a sequence of frames on a canvas as the page scrolls.
// Rules and test hooks: docs/player-spec.md. Tests: tests/test_player.py.

const canvas = document.getElementById("turntable");
const ctx = canvas.getContext("2d");

let images = [];
let loaded = [];
let loadedCount = 0;
let frameCount = 0;
let lastDrawn = -1;
let reducedMotion = false;

/**
 * Fetch and parse manifest.json.
 * @returns {Promise<{frames: string[], width: number, height: number}>}
 */
async function loadManifest() {
  const response = await fetch("manifest.json");
  if (!response.ok) throw new Error(`manifest.json: HTTP ${response.status}`);
  return response.json();
}

/**
 * Order in which to request frames: 0, every `step`th frame, then the rest.
 * Example: loadOrder(20, 8) -> [0, 8, 16, 1, 2, ..., 7, 9, ..., 15, 17, 18, 19]
 * @param {number} count
 * @param {number} step
 * @returns {number[]}
 */
function loadOrder(count, step = 8) {
  const keyframes = [];
  for (let i = 0; i < count; i += step) keyframes.push(i);
  const isKeyframe = new Set(keyframes);
  const rest = [];
  for (let i = 0; i < count; i++) {
    if (!isKeyframe.has(i)) rest.push(i);
  }
  return [...keyframes, ...rest];
}

/**
 * Frame index (0..count-1) for the current scroll position.
 * @param {number} count
 * @returns {number}
 */
function frameForScroll(count) {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0;
  return Math.round(progress * (count - 1));
}

/**
 * Index of the loaded frame closest to `wanted`, or -1 if none has loaded.
 * @param {number} wanted
 * @param {boolean[]} loaded  loaded[i] is true once frame i has loaded
 * @returns {number}
 */
function nearestLoaded(wanted, loaded) {
  let best = -1;
  let bestDistance = Infinity;
  for (let i = 0; i < loaded.length; i++) {
    if (!loaded[i]) continue;
    const distance = Math.abs(i - wanted);
    if (distance < bestDistance) {
      best = i;
      bestDistance = distance;
    }
  }
  return best;
}

/**
 * Size the canvas for its CSS size x devicePixelRatio, then redraw.
 */
function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(canvas.clientWidth * dpr);
  canvas.height = Math.round(canvas.clientHeight * dpr);
  if (lastDrawn >= 0 && images[lastDrawn]) {
    drawFrame(images[lastDrawn], lastDrawn);
  }
}

/**
 * Draw `image` fitted inside the canvas (contain, centred) and record
 * `index` in canvas.dataset.frame.
 * @param {HTMLImageElement} image
 * @param {number} index
 */
function drawFrame(image, index) {
  const scale = Math.min(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight);
  const w = image.naturalWidth * scale;
  const h = image.naturalHeight * scale;
  const x = (canvas.width - w) / 2;
  const y = (canvas.height - h) / 2;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(image, x, y, w, h);
  canvas.dataset.frame = String(index);
}

/**
 * Wrap `fn` so calling it repeatedly only runs it once per animation frame.
 */
function rafThrottle(fn) {
  let scheduled = false;
  return () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      fn();
    });
  };
}

function redraw() {
  if (frameCount === 0) return;
  const wanted = reducedMotion ? 0 : frameForScroll(frameCount);
  const index = nearestLoaded(wanted, loaded);
  if (index === -1 || index === lastDrawn) return;
  lastDrawn = index;
  drawFrame(images[index], index);
}

const scheduleRedraw = rafThrottle(redraw);
const scheduleResize = rafThrottle(resizeCanvas);

async function main() {
  reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  resizeCanvas();
  window.addEventListener("resize", scheduleResize);

  const manifest = await loadManifest();
  frameCount = manifest.frames.length;
  images = new Array(frameCount);
  loaded = new Array(frameCount).fill(false);
  canvas.dataset.loaded = "0";

  if (!reducedMotion) {
    window.addEventListener("scroll", scheduleRedraw, { passive: true });
  }

  for (const index of loadOrder(frameCount)) {
    const img = new Image();
    images[index] = img;
    img.onload = () => {
      loaded[index] = true;
      loadedCount += 1;
      canvas.dataset.loaded = String(loadedCount);
      scheduleRedraw();
    };
    img.onerror = () => {
      // A frame that fails to load must not break the player: it simply
      // never becomes eligible in `loaded`, so nearestLoaded skips it.
    };
    img.src = manifest.frames[index];
  }
}

main();
