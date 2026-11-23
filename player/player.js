// Turntable player: plays a sequence of frames on a canvas as the page scrolls.
// Rules and test hooks: docs/player-spec.md. Tests: tests/test_player.py.

const canvas = document.getElementById("turntable");
const ctx = canvas.getContext("2d");

/**
 * Fetch and parse manifest.json.
 * @returns {Promise<{frames: string[], width: number, height: number}>}
 */
async function loadManifest() {
  // TODO
}

/**
 * Order in which to request frames: 0, every `step`th frame, then the rest.
 * Example: loadOrder(20, 8) -> [0, 8, 16, 1, 2, ..., 7, 9, ..., 15, 17, 18, 19]
 * @param {number} count
 * @param {number} step
 * @returns {number[]}
 */
function loadOrder(count, step = 8) {
  // TODO
}

/**
 * Frame index (0..count-1) for the current scroll position.
 * @param {number} count
 * @returns {number}
 */
function frameForScroll(count) {
  // TODO
}

/**
 * Index of the loaded frame closest to `wanted`, or -1 if none has loaded.
 * @param {number} wanted
 * @param {boolean[]} loaded  loaded[i] is true once frame i has loaded
 * @returns {number}
 */
function nearestLoaded(wanted, loaded) {
  // TODO
}

/**
 * Size the canvas for its CSS size x devicePixelRatio, then redraw.
 */
function resizeCanvas() {
  // TODO
}

/**
 * Draw `image` fitted inside the canvas (contain, centred) and record
 * `index` in canvas.dataset.frame.
 * @param {HTMLImageElement} image
 * @param {number} index
 */
function drawFrame(image, index) {
  // TODO
}

async function main() {
  // TODO: load the manifest, start loading frames in loadOrder(),
  // keep canvas.dataset.loaded up to date, draw frame 0 when it arrives,
  // and redraw on scroll and resize (at most once per animation frame).
}

main();
