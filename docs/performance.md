<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# 1080p performance

Hardware evidence is scoped to one firmware-6.02 console, the Quake II 3.14
demo, and bounded sessions. The final interactive test was reported as stable
60 FPS during movement and firing. An every-60-frames trace contained 66
gameplay samples: median 16,735 microseconds and 95th percentile 33,499
microseconds. This sampling is not a full frame-time distribution.

## Changes that made the game playable

| Area | Change |
| --- | --- |
| Native startup | Static engine/GL3 integration, required imports, checked heap and writable save paths |
| Input | A 4 ms SDL input worker preserves queued button edges across slow render frames |
| Sound | Clear consumed PCM ring regions, preventing stale audio from repeating |
| Menu | Batch up to 1,024 glyphs instead of submitting each character |
| Geometry | Explicit triangle lists and buffer orphaning for streamed geometry |
| World | Batch compatible world surfaces, then group opaque materials within bounded runs; preserve special-surface ordering barriers |
| Particles | Instanced six-vertex quads replace the expensive particle path |
| Allocation | Reserve the shared render arena for buffers; textures use the existing direct allocation path |
| Texture coherency | Reuse CPU texture flushes within a pending draw batch, retaining hazard drains and resource retirement |

Observed gameplay progressed from below 1 FPS to 5–7, 12–20, 30–60 and finally
the reported stable 60 FPS as these changes accumulated. These are interactive
observations, not controlled comparative benchmarks. Particle work in one
profile fell from roughly 26–30 ms to 0.14 ms; world work after the texture
cache change fell from roughly 10–12 ms to 2–3 ms.

Single-mip texture filtering is the default performance tradeoff. Enabling
`gl3_mipmaps 1` followed by `vid_restart` increases image quality at a substantial
performance cost. The top-left FPS overlay uses wall-clock frame intervals.

## Boundaries

The frozen game SDK is an adaptation of PS5 OpenGL source
`cef6c1b869ba3f0c8acaab5b171bbb33eca07f03`; its archive identity is recorded in
`dependencies.json`. Focused regressions are included. It is not a general
graphics SDK qualification or a new full CTS campaign.

A 3840×2160 experiment rendered around 30–60 FPS depending on view, with sampled
median frame time 33,233 microseconds. The release remains 1920×1080.
Long sessions, every level, multiplayer, suspend/resume, device loss and other
firmwares need separate validation. Fresh shell music playback is also pending.
