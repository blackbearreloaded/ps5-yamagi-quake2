> **Disclaimer:** This is an AI-assisted project developed using OpenAI Codex.

<p align="center"><img src="sce_sys/icon0.png" width="128" alt="Yamagi Quake II icon"></p>
<h1 align="center">Yamagi Quake II for PS5</h1>
<p align="center"><strong>Quake II, running natively on PlayStation 5 homebrew.</strong><br>1080p OpenGL rendering, DualSense controls, sound and local saves.</p>
<p align="center">
  <img src="https://img.shields.io/badge/platform-PlayStation%205-003791" alt="PlayStation 5">
  <img src="https://img.shields.io/badge/renderer-OpenGL%203.3-5586A4" alt="OpenGL 3.3">
  <img src="https://img.shields.io/badge/target-1080p60-5DDFA4" alt="1080p60 target">
  <img src="https://img.shields.io/badge/status-alpha-EF8354" alt="Alpha">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-blue" alt="GPL-3.0-or-later"></a>
</p>

## Highlights

- Based on Yamagi Quake II 8.70, with a native PS5 lifecycle and static GL3 renderer.
- Powered by [PS5 OpenGL](https://github.com/blackbearreloaded/ps5-opengl), consumed from its pinned GitHub SDK release with the game's two performance adaptations.
- Renders at **1920 × 1080**, targeting 60 FPS, with an FPS overlay at the top left.
- DualSense input is sampled independently of rendering, preserving short button presses.
- Stereo sound, controller defaults, writable saves and configuration.
- Custom shell icon, selection/launch backgrounds and looping selection music.
- Includes the renderer patches and host regressions used to resolve startup, input, audio and performance problems.

This app requires an already configured, compatible PS5 homebrew environment.
It contains no exploit, proprietary Sony SDK or firmware modules.
**Quake II game data is required and is not included in the repository or app download.**

## Install

1. Download `PPSA99007.zip` and verify it against `SHA256SUMS` from the
   [release page](https://github.com/blackbearreloaded/ps5-yamagi-quake2/releases).
2. Extract the archive and add your game data to `PPSA99007/assets/baseq2/`.
   The supported 3.14 demo is the tested baseline; see [game data setup](docs/game-data.md).
3. Copy the complete `PPSA99007` folder into your loader's homebrew directory,
   normally `/data/homebrew/`, producing `/data/homebrew/PPSA99007/eboot.bin`.
4. Refresh or restart the loader, then launch **Yamagi Quake II**. Updated shell
   artwork/music may require a full loader restart to refresh cached presentation assets.

```text
PPSA99007/
├── eboot.bin
├── assets/baseq2/
│   ├── yq2.cfg             supplied controller/audio defaults
│   ├── pak0.pak            add separately
│   └── players/            add with the demo data
├── sce_module/libc.prx     clean-room application runtime
└── sce_sys/                metadata, artwork and selection music
```

The release ZIP is deliberately a folder package so game data can be added
before the app is mounted. It will not start correctly without that data.
Save games and user configuration live under `/download0/yamagi/baseq2/`.
Back up that directory before replacing an existing installation.

## Controls

| Input | Action |
| --- | --- |
| Left stick / right stick | Move / look |
| D-pad in menus | Navigate |
| Cross / Circle in menus | Confirm / back |
| Options | Pause / menu |
| R2 | Fire |
| Cross / Circle in game | Jump / crouch |
| L1 / R1 | Previous / next weapon |
| L3 | Speed modifier |
| Triangle / Square | Inventory / use selected item |
| D-pad up / down in game | Previous / next inventory item |
| Touchpad press | Help / objectives |

Defaults are in [yq2.cfg](assets/baseq2/yq2.cfg). Existing user `config.cfg`
and `autoexec.cfg` load afterward and can override them.

## Performance and current limits

The final 1080p candidate achieved **user-reported stable 60 FPS** while moving
and firing in a bounded demo-level test on **one PS5 running firmware 6.02**.
This is an alpha result, not a guarantee for every scene or console. Sampled
timings still include occasional frames around 33 ms. See [performance notes](docs/performance.md).

The release uses a frozen, game-specific OpenGL runtime with buffer allocation
and texture-flush optimizations. It does not inherit a full CTS qualification
from an older runtime. A separate 2160p experiment ran around 30–60 FPS and is
not the release build.

Retail campaigns, expansion packs, multiplayer, long sessions, suspend/resume
and device-loss recovery remain unqualified. Single-mip textures are the fast
default and can shimmer at distance. Selection music passed format validation
and independent decoding; fresh shell playback has not been checked on TV.

## Build

Use Ubuntu 24.04 or WSL with Python 3.12 and Clang 18:

```bash
sudo apt update
sudo apt install build-essential clang clang-18 lld-18 llvm-18 make python3 git gh \
  pkg-config wget unzip libssl-dev libsdl2-dev libegl1-mesa-dev \
  libgl1-mesa-dri glslang-tools

gh auth login                    # account with access while this repo is private
make deps
make package
```

Outputs: `dist/PPSA99007/`, `dist/PPSA99007.zip` and its checksum file.
The build never downloads or packages Quake II game data. It restores pinned
Yamagi and native-app sources, the public homebrew toolchain, PacBrew SDL2 and
the [PS5 OpenGL GitHub SDK](https://github.com/blackbearreloaded/ps5-opengl/releases/tag/v0.1.0-perf20260907-sampled),
plus a small hash-pinned game runtime overlay. Graphics binaries are release dependencies, not Git blobs.
See [dependencies and source reproduction](docs/building.md).

For host checks only:

```bash
python3 tools/bootstrap.py --host-only
make test
```

The [Build workflow](.github/workflows/build.yml) runs host regressions on pushes
and pull requests. Manual dispatch also builds and uploads the native folder
ZIP using the frozen SDK release asset. Console testing is manual and separate.

## Project layout

```text
src/ps5/          Native entry, EGL/video, input, lifecycle and compatibility code
patches/          Yamagi renderer/platform changes and OpenGL texture-cache delta
assets/baseq2/    Controller, audio and FPS defaults; no game data
sce_sys/          PS5 metadata, converted artwork and selection music
tooling/native/  Heap/runtime helpers, link stubs and linker configuration
tools/           Dependency restoration, build, demo preparation and packaging
tests/           Host regressions, shader checks and game-data validation
docs/            Installation, build, performance and artwork sources
upstream/        Pinned Yamagi checkout restored here; ignored by Git
.deps/           Downloaded build dependencies; ignored by Git
```

## Credits and license

Thanks to **id Software**, the **Yamagi Quake II** contributors,
**ps5-payload-dev**, **PacBrew**, **SDL**, **Mesa**, **OpenGNM**, and contributors
to [PS5 OpenGL](https://github.com/blackbearreloaded/ps5-opengl) and the
[native-app boilerplate](https://github.com/blackbearreloaded/ps5-native-app-boilerplate).
The repository organization follows [ProsperoAI](https://github.com/blackbearreloaded/ProsperoAI).

Project code is GPL-3.0-or-later; upstream components retain their own licenses.
See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md).
Quake II game data and trademarks belong to their respective owners. This is
an unofficial port and is not affiliated with id Software, Bethesda or Sony.
