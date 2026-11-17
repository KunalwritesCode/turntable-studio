# Turntable Studio: scope

**Status:** in development, started 7 Nov 2026 · **Money budget:** $0

## Problem

Scroll-driven 360° "turntable" pages look great. Think of Apple's product pages or the Cyberfiction site: as you scroll, a character or product rotates. The catch is that each page needs a 3D artist to model, light and render hundreds of frames. So most people who build one borrow someone else's frames. My 2023 Cyberfiction clone did exactly that: 299 PNGs of another studio's character (63 MB).

Turntable Studio removes the artist step. Give it a prompt or a picture and it:

1. generates an original character image (or uses yours),
2. turns it into a 3D model,
3. renders a 360° turntable as frames,
4. builds a fast scroll page that plays them.

It runs entirely on free tiers.

## Who it's for

- Front-end developers and designers who want the scroll-turntable effect with original assets and no budget.
- Me: an end-to-end AI pipeline I own, from model calls to the web performance of the result.

## Success criteria for v0.1

| # | Criterion | How it's measured |
|---|---|---|
| 1 | One command builds a site: `turntable make --prompt "..."` or `--image picture.png` writes a static site to `dist/` with no manual steps | Run from a clean clone |
| 2 | 150 frames at 1280 px weigh **≤ 6 MB** (Cyberfiction: 63 MB for 299 frames) | Sum of files in `dist/frames/`. Baseline: WebP at quality 75 averaged 32 KB a frame on the old frames, about 4.9 MB for 150 |
| 3 | First frame drawn in **≤ 1.5 s** on a throttled connection | Playwright with network throttling, median of 5 cold loads |
| 4 | **$0 per character**, and **≤ 10 min** of wall time per character, not counting queue time | Logged per run in `runs/<hash>/meta.json` |
| 5 | An identical re-run makes **zero** model calls, so it uses no GPU quota | Content-hash cache; the second run's log shows no Space calls |
| 6 | CI is green: lint, unit tests and a Playwright smoke test that loads the page, sees the first frame and sees the frame change on scroll | GitHub Actions |
| 7 | README shows a demo GIF, a live gallery of 3 characters and the measured numbers above | README review against the template |

## Non-goals for v0.1

- **No hosted app that runs models for visitors.** It's a CLI that outputs static files.
- No paid backends. The 3D stage sits behind a small interface, so one could be added later, but v0.1 ships free backends only.
- No rigging, animation or mesh editing.
- No live three.js viewer; that's a stretch goal (see Decisions).
- No multi-character "switch" sequence; that's a stretch goal.

## Architecture

Each stage reads and writes files in `runs/<hash>/`, so any stage can be re-run on its own and cached results are reused. Only stages 1 and 2 use GPU quota; everything else runs locally.

```text
prompt ──► [1 image] ──► character.png ─┐
picture ────────────────────────────────┤
                                        ▼
                                  [2 model 3D] ──► model.glb
                                                     │
                                                     ▼
                                  [3 render] ──► frames/0001.png … 0150.png
                                                     │
                                                     ▼
                                  [4 encode] ──► frames/*.webp + manifest.json
                                                     │
                                                     ▼
                                  [5 site]   ──► dist/  ──► GitHub Pages
```

| Stage | Tool | Cost | Notes |
|---|---|---|---|
| 1 Image | FLUX.2 [klein] 4B (Apache 2.0) through a Hugging Face Space, or skipped with `--image` | Free (uses ZeroGPU quota, or none on a CPU Space) | The Space ID lives in config, not code, because community Spaces come and go. A fixed prompt template asks for a front view, head and shoulders, plain background and even light, which are the inputs image-to-3D handles best |
| 2 3D | TRELLIS.2 (Microsoft, MIT) through the `microsoft/TRELLIS.2` Space, via `gradio_client` and your HF token | Free (uses ZeroGPU quota) | The heaviest call. Logged-in accounts get more quota than anonymous ones, so the token matters |
| 3 Render | three.js in headless Chrome, driven by Playwright | Free, local | Camera auto-fits the model's bounding box. Fixed lights, transparent background, 120–180 frames over 360° |
| 4 Encode | Pillow → WebP (quality 75) | Free, local | `manifest.json` holds frame count, size, format and credits |
| 5 Site | Player template: GSAP ScrollTrigger on native scroll (Locomotive dropped) | Free, local | Progressive loading: draw frame 1, load every 8th frame, then fill the gaps |

### Working within the free quota

A free Hugging Face account gets about 5 ZeroGPU minutes a day, and forum reports suggest a cap on runs per day too. So expect only a few 3D generations a day. The plan is built around that:

- **M1 and M2 use no quota.** The player is built on synthetic fixture frames and the renderer on a sample `.glb`.
- **Every model call is cached** by content hash, so nothing is ever generated twice.
- **`--image` is a first-class path.** Make the character image in any free tool, or photograph a figurine, and only the 3D step uses quota.
- **Gallery generation is spread over a few days** in M4.

## Repository layout

```text
turntable-studio/
├── README.md
├── LICENSE                 # MIT
├── pyproject.toml
├── turntable.toml          # Space IDs and render defaults
├── .env.example            # HF_TOKEN=  (real .env is gitignored)
├── docs/scope.md
├── turntable/              # Python package
│   ├── cli.py              # commands: make, image, model, render, build, doctor
│   ├── cache.py
│   └── stages/
│       ├── image.py
│       ├── model3d.py
│       ├── render.py
│       ├── encode.py
│       └── site.py
├── renderer/               # three.js page that Playwright drives to render frames
│   ├── index.html
│   └── render.js
├── player/                 # scroll player copied into dist/
│   ├── index.html
│   ├── player.js
│   └── style.css
├── tests/
└── .github/workflows/
    ├── ci.yml              # ruff, pytest, Playwright smoke test (never calls any Space)
    └── pages.yml           # deploys the gallery
```

## Milestones

Each milestone gets a GitHub issue and a git tag when done.

### M0 Setup and retire the clone

- Cyberfiction repo: README that credits Cyberfiction's artwork, bug fixes, then archive it.
- New `turntable-studio` repo with MIT licence, `.gitignore` covering `.env` and `runs/`, this scope and the README skeleton.
- **Done when:** both repos are public and Cyberfiction is archived.

### M1 Player

- Reads `manifest.json`, draws frame 1 immediately, loads progressively.
- Sizes the canvas for devicePixelRatio, handles resize, respects `prefers-reduced-motion`.
- Test frames come from a small fixture script (a numbered, rotating arrow), so frame-order bugs are visible.
- **Done when:** the Playwright smoke test passes on the fixture frames.

### M2 Renderer

- `turntable render model.glb --frames 150` writes transparent PNG frames and a manifest.
- Test model: a sample glTF model with a clear licence (check the licence of the specific model used).
- **Done when:** the player shows a turntable rendered from a real `.glb`.

### M3 AI stages

- Image stage (FLUX.2 [klein] Space, or `--image`) and 3D stage (TRELLIS.2 Space), each isolated in one module.
- Content-hash cache in `runs/`. The token comes from `.env` only; tests mock the Spaces.
- `turntable doctor` checks that each Space is up and its API still has the endpoints the code expects, since Space owners can change them.
- **Done when:** `turntable make --prompt "..."` works end to end and a second identical run makes no Space calls.

### M4 Ship v0.1

- CI green; Pages deploys a gallery of 3 characters.
- Measure criteria 2–5 and put the numbers in the README.
- Quality notes: score up to 10 turntables 0–2 on front fidelity, back plausibility and visible artefacts. These notes are the seed of a later benchmark of how consistent image-to-3D models stay all the way round.
- Demo GIF and tag `v0.1.0`.
- **Done when:** the README passes the project template and the quickstart works from a clean clone.

## Decisions

1. **Repository:** a new `turntable-studio` repo; Cyberfiction is archived with credits.
2. **Backends and budget:** free only, $0. Hugging Face Spaces for both model stages.
3. **Output:** pre-rendered frames for v0.1. They keep the scroll-sequence look, look identical on every device and need no WebGL on a visitor's phone. A live three.js mode (one `.glb`, draggable, but quality depends on the visitor's GPU) is a stretch goal.

## Risks

| Risk | Mitigation |
|---|---|
| Daily ZeroGPU quota runs out | Cache everything; use `--image` to skip stage 1; spread gallery runs over days; build M1–M2 without the Spaces |
| A Space changes its API or goes offline | Each Space is isolated in one module with its ID in config; `turntable doctor` detects breakage; record the working Space and date in the README |
| The model invents the character's back, which can look wrong | Prompts that favour simple backs; document it under Limitations |
| Headless WebGL without a GPU renders slowly | Render at 1280 px. It's a one-off per character |
| Licences on generated outputs | TRELLIS.2 is MIT and FLUX.2 [klein] 4B is Apache 2.0. Note any terms of the specific Spaces used |
| Leaked token | `HF_TOKEN` lives only in a gitignored `.env`. CI never calls a Space, so it needs no token |
| Scope creep | No web UI and no paid backends in v0.1. Stretch goals wait for v0.2 |
