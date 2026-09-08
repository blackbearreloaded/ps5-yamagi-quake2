<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Changelog

## 0.1.0-alpha.2 — 2026-09-08

- Fix clean-install startup by including the hash-verified official demo and
  original notices in both ZIP and FFPFSC releases.
- Unpack the finished FFPFSC in CI, compare every file and validate startup assets
  before uploading either playable package.

## 0.1.0-alpha.1 — 2026-09-08

- First packaged 1080p PS5 release of the Yamagi Quake II 8.70 port.
- Native startup, controller sampling, PCM audio, local saves and FPS overlay.
- Glyph/world batching, material grouping, instanced particles, buffer allocation
  and per-batch texture flush reuse; stable 60 FPS reported in the bounded demo test.
- Shell artwork and prepared looping selection music.
- ProsperoAI-style repository layout, pinned dependency restoration, host CI and
  game-data-free folder packaging. 4K remains experimental and is excluded.
