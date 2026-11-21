---
name: agent-browser-headless-webgl
description: This skill should be used when running `agent-browser --headed` on headless Linux (Xvfb / remote workstation without a physical GPU display) against WebGL2, MapLibre GL JS, Three.js, or Cesium applications, or when encountering X11 GLX `GPUInitializationError` / blank map canvases.
---

# Headless Linux Xvfb + WebGL2 (`agent-browser --headed`)

On headless Linux workstations where `agent-browser --headed` automatically spawns an `Xvfb` virtual display, Chromium's default X11 GLX backend can fail WebGL2 context creation (`GPUInitializationError` / blank MapLibre GL JS or Three.js canvases).

## Required Invocation Pattern

Pass `--webgpu` alongside `--headed` so Chromium routes ANGLE over Vulkan 1.3 instead of X11 GLX:

```bash
SESSION="$(agent-browser session id --scope worktree --prefix qa)"
agent-browser --session "$SESSION" --headed --webgpu open http://localhost:PORT
```

When connecting to local HTTPS servers with self-signed certificates, combine `--headed`, `--webgpu`, and `--ignore-https-errors`:

```bash
agent-browser --session "$SESSION" --headed --webgpu --ignore-https-errors open https://localhost:PORT
agent-browser --session "$SESSION" set viewport 1920 1080
```

## Cleanup

Always close the isolated session when finished so background Chromium and `Xvfb` processes exit cleanly:

```bash
agent-browser --session "$SESSION" close
```
