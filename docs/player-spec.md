# Player spec (M1)

The player is the page that ships in `dist/`. It plays a sequence of turntable frames on a canvas as the visitor scrolls. It has no build step: `index.html`, `style.css`, `player.js`, `manifest.json` and a `frames/` folder, served as static files.

The end-to-end tests in `tests/test_player.py` check every rule below.

## Input: `manifest.json`

Served from the same folder as `index.html`.

```json
{
  "version": 1,
  "title": "Fixture turntable",
  "width": 1280,
  "height": 720,
  "frames": ["frames/0001.webp", "frames/0002.webp", "..."],
  "credits": "Synthetic test frames"
}
```

- `frames` lists every frame URL in playback order. Its length is the frame count.
- `width` and `height` are the frames' pixel size. All frames share it.
- `title` and `credits` are optional, for display.

## Behaviour

1. **Load the manifest** with `fetch("manifest.json")`.
2. **Load order.** Request frame 0 first, then every 8th frame (8, 16, 24, …), then the remaining frames in order. Each frame is requested exactly once. Keyframes spread across the whole turn arrive early, so fast scrolling always has something close to show.
3. **First paint.** Draw frame 0 as soon as it has loaded.
4. **Scroll mapping.** Scroll progress runs from 0 at the top of the page to 1 at the bottom (`scrollY / (scrollHeight - innerHeight)`, clamped to 0–1). The wanted frame is `round(progress × (count − 1))`.
5. **Missing frames.** If the wanted frame hasn't loaded, or failed to load, draw the nearest frame that has loaded. A frame that fails to load must not break the player.
6. **Drawing.** Fit the frame inside the canvas without cropping (like CSS `object-fit: contain`), centred, on a cleared canvas.
7. **Sharpness.** The canvas's pixel size is its CSS size × `devicePixelRatio`, recalculated on resize, and the current frame is redrawn after a resize.
8. **Performance.** Draw at most once per animation frame (`requestAnimationFrame`) and skip drawing when the frame to show hasn't changed.
9. **Reduced motion.** When `prefers-reduced-motion: reduce` is set, show frame 0 and don't scrub frames on scroll.
10. **No console errors** during normal use.

## Test hooks

The tests observe the player through two attributes on `<canvas id="turntable">`:

| Attribute | Meaning |
|---|---|
| `data-frame` | Index (0-based) of the frame most recently drawn. Set after every draw |
| `data-loaded` | Number of frames that have finished loading successfully |

## Dependencies

None required. A plain scroll listener with `requestAnimationFrame` meets the spec; GSAP ScrollTrigger is optional.
