<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Performance at 120 Hz

## Current results

The optimized 4K candidate reached **owner-reported 120 FPS throughout the
tested areas**, including the initially stationary opening, underwater and
previously slow views. Evidence is scoped to the Quake II 3.14 demo, bounded
sessions and **one PS5 running firmware 6.02**.

The final selectable-resolution SDK completed a separate 90-second automated
opening-scene test on September 11, 2026: 3,961 rendered frames and six mode
changes, cycling 2160p → 1080p → 1440p → 2160p twice. All seven native video
initializations succeeded, and the previous graphics owner closed before
each restart. The final configuration saved 2160p and a 120 FPS limit.

The table covers steady 120-frame windows, excluding mode-restart time. It
is a bounded scene sample, not a complete frame-time distribution.

| Render resolution | Sample windows | Minimum FPS | Median FPS | Maximum FPS |
| --- | ---: | ---: | ---: | ---: |
| 1920 × 1080 | 6 | 119.88 | 119.88 | 119.88 |
| 2560 × 1440 | 6 | 119.86 | 119.89 | 119.90 |
| 3840 × 2160 | 7 | 116.96 | 118.87 | 119.88 |

The subsequent normal menu build measured 119.88 FPS and reloaded the saved
2160p setting. Release builds open the normal menu and have no benchmark
timer or automatic resolution changes. CI builds the app independently;
release validation receipts identify the downloadable executable and checks.

## Changes since the 1080p60 release

| Area | Change |
| --- | --- |
| Depth clear | Clear only the active target; use the GPU path at all three supported sizes |
| Water | Batch subdivisions while preserving surface order |
| World and brush models | Group compatible materials and batch inline brush geometry |
| Command allocation | Reuse retired command-pool allocations |
| CPU cache work | Use the Mesa CPU cache helpers and reduce unnecessary scanout-range flushing |
| Presentation | Overlap GPU presentation with preparation of the next frame |
| Frame pacing | Shorter bounded marker polls, less hot-path logging and separate terminal-command retirement remove the observed 60 FPS stalls |
| Resolution changes | Fully terminate EGL/VideoOut, then reset GL3 caches before creating the next renderer |

Draw resources still wait for every original draw marker before release.
The terminal command allocation is retired separately and checked before
GPU reuse or shutdown. The scanout allocation reserves enough capacity for
4K even when the active render size is lower.

## Earlier work retained

The first playable version progressed from below 1 FPS to owner-reported
stable 60 FPS at 1080p through these changes:

- Static native engine/GL3 integration, checked heap and writable save paths.
- A 4 ms SDL input worker that preserves button edges across slow frames.
- Clearing consumed PCM ring regions to prevent stale audio from repeating.
- Menu glyph batches, triangle lists, streamed buffer orphaning and instanced particles.
- Bounded world/material batches with special-surface ordering barriers.
- Buffer arena allocation and CPU texture-flush reuse with hazard checks.

Those were interactive observations across successive builds, not a
controlled comparative benchmark.

## Display settings and limits

**Video → Video mode → Apply** selects 1080p, 1440p or 2160p and saves the
choice before the renderer restarts. The HDMI signal remains managed by the
console; a TV may report 4K/120 Hz while the game renders at 1080p or 1440p.
The FPS overlay measures wall-clock rendering intervals, independently of
the HDMI status. A 120 Hz output target does not guarantee 120 rendered
frames in every scene.

Single-mip texture filtering remains the default performance tradeoff and
can shimmer at distance. `gl3_mipmaps 1` followed by `vid_restart` enables
mipmaps at a substantial performance cost.

The frozen SDK is based on PS5 OpenGL
`32ca4d4e16c0f29d75b4ae82b74c2df6e1e067bf` plus the included game runtime
patches. Exact archive identities are in `dependencies.json`. Focused game
regressions do not constitute a new full graphics CTS campaign.

Every level, retail campaigns, expansions, multiplayer, long sessions,
suspend/resume, device loss and other firmwares remain unqualified.
Selection music passed format validation and independent decoding;
fresh shell playback on TV remains unrecorded.
