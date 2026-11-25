# Turntable Studio

Turn a text prompt or a picture into an original 3D character and a scroll-driven 360° turntable web page, with one command and no paid APIs.

> **Status:** in development. Numbers marked _TBD_ get filled in from real runs at v0.1.

## Progress

- [x] M0: project setup
- [x] M1: scroll player
- [x] M2: 360° renderer
- [ ] M3: AI stages (image → 3D)
- [ ] M4: gallery, measurements, v0.1.0

Details for each milestone: [docs/scope.md](docs/scope.md#milestones).

## Why

Scroll-to-rotate pages are striking, but each one needs a 3D artist to model, light and render hundreds of frames. So most demos reuse someone else's frames; my own 2023 version did (see [Cyberfiction](https://github.com/KunalwritesCode/cyberfiction), archived). Turntable Studio generates the character, the 3D model and the frames itself, on free tiers, then ships a page that loads fast.

## Demo

_TBD: GIF of scrolling through a generated character._

Live gallery: _TBD (GitHub Pages link)_

## Results

| Metric | Target | Measured |
|---|---|---|
| Payload, 150 frames at 1280 px | ≤ 6 MB | _TBD_ |
| Time to first frame (throttled, median of 5) | ≤ 1.5 s | _TBD_ |
| Cost per character | $0 | _TBD_ |
| Wall time per character (excluding queue) | ≤ 10 min | _TBD_ |
| Model calls on an identical re-run | 0 | _TBD_ |

For comparison, the 2023 Cyberfiction page shipped 299 PNG frames totalling 63 MB.

**Quality notes:** _TBD: up to 10 turntables, each scored 0–2 on front fidelity, back plausibility and visible artefacts._

## Quickstart

```bash
git clone https://github.com/KunalwritesCode/turntable-studio && cd turntable-studio
pip install -e . && playwright install chromium
cp .env.example .env            # add your free Hugging Face token as HF_TOKEN
turntable make --prompt "cyberpunk courier, silver jacket, short white hair"
python -m http.server -d dist   # open http://localhost:8000
```

Already have a character picture? Use `--image picture.png` instead of `--prompt`; it skips the image step and saves GPU quota.

_TBD: verify these exact commands from a clean clone before v0.1._

## How it works

```text
prompt/picture → [image] → [3D model] → [render 360°] → [encode WebP] → [scroll page]
```

1. **Image:** FLUX.2 [klein] 4B generates a front-facing character on a plain background, through a Hugging Face Space. Skipped if you pass `--image`.
2. **3D:** TRELLIS.2 converts the image to a textured `.glb` through the `microsoft/TRELLIS.2` Space.
3. **Render:** a three.js scene in headless Chrome orbits the model and saves transparent frames. The camera auto-fits the model.
4. **Encode:** frames become WebP, and a `manifest.json` describes them.
5. **Page:** a small player draws frame 1 at once, loads every 8th frame, then fills the gaps, and scrubs frames with GSAP ScrollTrigger.

Every stage caches its output by content hash in `runs/`, so re-running an input never spends GPU quota twice. `turntable doctor` checks the Spaces are up and their APIs haven't changed.

**Free-tier note:** a free Hugging Face account gets a few ZeroGPU minutes a day, which is enough for only a few 3D generations. Everything after the 3D step runs locally and uses no quota.

Design notes and trade-offs: [docs/scope.md](docs/scope.md).

## Evaluation and tests

- **Unit tests (pytest):** cache keys, manifest schema, frame naming, with the Spaces mocked.
- **Smoke test (Playwright):** the page loads, the first frame appears and the frame changes on scroll.
- **CI** runs lint, unit tests and the smoke test on every push. It never calls a Space, so it needs no token.

## Limitations and next steps

- Image-to-3D models have to invent the unseen side of a character, so backs can look wrong. _TBD: examples from the quality notes._
- Community Spaces can change or go offline. _TBD: the Spaces and dates this release was tested with._
- Rendering without a GPU is slow (software WebGL). It's a one-off cost per character.
- Next: a live three.js mode, and a benchmark of how consistent different image-to-3D models stay all the way round.

## Credits and licence

- Image-to-3D: [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) by Microsoft Research (MIT).
- Image generation: FLUX.2 [klein] 4B by Black Forest Labs (Apache 2.0).
- Hosting for both models: Hugging Face Spaces and ZeroGPU.
- Scroll animation: [GSAP](https://gsap.com) ScrollTrigger.
- Test model: [Duck](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Duck) by Sony Computer Entertainment America, SCEA Shared Source License 1.0.
- Project licence: MIT.
