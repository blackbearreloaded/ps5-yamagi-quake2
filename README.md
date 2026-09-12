<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

> **Original game credits:** Quake II was created by **id Software**.
> Thanks to the original development team for the game and its
> [official open-source engine release](https://github.com/id-Software/Quake-2).
> This PS5 port builds on [Yamagi Quake II](https://github.com/yquake2/yquake2);
> credit and thanks also go to the Yamagi developers and contributors for their
> continued maintenance and improvements.

> **PS5 port and maintainer:** [BlackBearReloaded](https://github.com/blackbearreloaded).
> Native PS5 integration, renderer optimizations, controller/audio integration,
> build tools, packaging and port-specific tests. Upstream developers retain
> credit for their original work; see [third-party notices](THIRD_PARTY_NOTICES.md).

<p align="center"><img src="sce_sys/icon0.png" width="128" alt="Yamagi Quake II icon"></p>
<h1 align="center">Yamagi Quake II for PS5</h1>
<p align="center"><strong>Quake II, running natively on PlayStation 5 homebrew.</strong><br>1080p, 1440p or 4K OpenGL rendering at a 120 FPS target, with DualSense controls, sound and local saves.</p>
<p align="center">
  <img src="https://img.shields.io/badge/platform-PlayStation%205-003791" alt="PlayStation 5">
  <img src="https://img.shields.io/badge/renderer-OpenGL%203.3-5586A4" alt="OpenGL 3.3">
  <img src="https://img.shields.io/badge/target-4K120-5DDFA4" alt="4K120 target">
  <img src="https://img.shields.io/badge/status-alpha-EF8354" alt="Alpha">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-GPL--3.0--or--later-blue" alt="GPL-3.0-or-later"></a>
</p>

Demo available by clicking the image below.

[![Yamagi Quake II gameplay on PS5 with the FPS overlay](docs/images/quake2-gameplay.png)](https://i.imgur.com/LSRzui3.mp4)

## Highlights

- Based on Yamagi Quake II 8.70, with a native PS5 lifecycle and static GL3 renderer.
- Powered by [PS5 OpenGL](https://github.com/blackbearreloaded/ps5-opengl), using a frozen optimized game SDK with complete sources and the game-specific runtime patches.
- Choose **1920 × 1080**, **2560 × 1440** or **3840 × 2160**, all targeting **120 FPS**, with an FPS overlay at the top left.
- Change resolution from the Video menu and keep your selection across launches. A fresh configuration defaults to 4K.
- DualSense input is sampled independently of rendering, preserving short button presses.
- Stereo sound, controller defaults, writable saves and configuration.
- Custom shell icon, selection/launch backgrounds and looping selection music.
- Includes the renderer patches and host regressions used to resolve startup, input, audio and performance problems.
- The optimized 4K candidate reached owner-reported 120 FPS throughout a bounded gameplay check, including the previously slow opening and underwater areas.

This app requires an already configured, compatible PS5 homebrew environment.
It contains no exploit, proprietary Sony SDK or firmware modules.
**Current app downloads include the verified Quake II 3.14 demo and are ready
to launch.** Retail game data is separate. Game assets are downloaded during
packaging and remain outside Git; their original license and readme accompany them.

## Install

1. Download `PPSA99007.zip` and its accompanying `.sha256` file from the
   [release page](https://github.com/blackbearreloaded/ps5-yamagi-quake2/releases).
   Verify the ZIP's SHA-256 before extracting it.
2. Extract the archive. Demo data is already present in `PPSA99007/assets/baseq2/`.
   To use your own retail game, see [game data setup](docs/game-data.md).
3. Copy the complete `PPSA99007` folder into your loader's homebrew directory,
   normally `/data/homebrew/`, producing `/data/homebrew/PPSA99007/eboot.bin`.
4. Refresh or restart the loader, then launch **Yamagi Quake II**. Updated shell
   artwork/music may require a full loader restart to refresh cached presentation assets.

```text
PPSA99007/
├── eboot.bin
├── assets/baseq2/
│   ├── yq2.cfg             supplied controller/audio defaults
│   ├── pak0.pak            verified demo data
│   ├── players/            demo player assets
│   └── DEMO-LICENSE.txt    original demo terms
├── sce_module/libc.prx     clean-room application runtime
└── sce_sys/                metadata, artwork and selection music
```

Use the extracted folder from `PPSA99007.zip`. FFPFSC downloads were withdrawn
after the owner reported that the compressed image failed to start; Actions
publishes only the folder ZIP and checksum.
Version `0.1.0-alpha.1` omitted game data and cannot launch by itself; replace
that package with the current demo build.
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

## Resolution and refresh rate

Open **Video → Video mode**, choose **1080p**, **1440p** or **2160p**, then
select **Apply**. The renderer restarts at that resolution and saves the
selection immediately. All three modes use a **120 Hz presentation target**.

This setting changes the game's render resolution. The console manages the
HDMI output separately, so a TV can continue to report **4K / 120 Hz** at every
setting: lower-resolution frames are scaled for that output. This is expected.
Use the in-game FPS overlay to judge actual rendering speed; the TV's HDMI
status reports the signal format. A compatible display and console output
configuration are needed to display 120 Hz.

## Performance and current limits

The optimized 4K candidate achieved **user-reported 120 FPS throughout the
tested areas**, including the opening and underwater, on **one PS5 running
firmware 6.02**. A separate automated test completed six resolution switches;
steady 120-frame windows measured about 119.9 FPS at 1080p and 1440p and
117–120 FPS at 2160p. See [performance notes](docs/performance.md) for scope.

The release combines draw batching, texture and buffer reuse, GPU depth clears,
and presentation/CPU overlap. Its focused game regressions do not constitute
a full graphics CTS campaign or a guarantee for every scene or console.

Retail campaigns, expansion packs, multiplayer, long sessions, suspend/resume
and device-loss recovery remain unqualified. Single-mip textures are the fast
default and can shimmer at distance. Selection music passed format validation
and independent decoding; fresh shell playback has not been checked on TV.

## Build

Use Ubuntu 24.04 or WSL with Python 3.12 and Clang 18:

```bash
sudo apt update
sudo apt install build-essential clang clang-18 lld-18 llvm-18 make python3 python3-venv git gh \
  pkg-config wget unzip libssl-dev libsdl2-dev libegl1-mesa-dev \
  libgl1-mesa-dri glslang-tools

gh auth login                    # authenticated GitHub release downloads
make deps
make package
```

Outputs: `dist/PPSA99007/`, `dist/PPSA99007.zip` and its checksum file.
Packaging downloads the official demo from Yamagi's mirror, checks its pinned
SHA-256, and includes unchanged game assets and original notices. It also restores pinned
Yamagi and native-app sources, the public homebrew toolchain, PacBrew SDL2 and
the [frozen game SDK](https://github.com/blackbearreloaded/ps5-yamagi-quake2/releases/tag/v0.2.0-alpha.1)
built from PS5 OpenGL. Graphics binaries are release dependencies, not Git blobs.
See [dependencies and source reproduction](docs/building.md).

For host checks only:

```bash
python3 tools/bootstrap.py --host-only
make test
```

The [Build workflow](.github/workflows/build.yml) runs host regressions on pushes
and pull requests. Manual dispatch builds and uploads the native folder ZIP
and its checksum using the frozen SDK release asset. Set the optional
`release_tag` input to an existing release to publish the ZIP and checksum;
leave it blank for CI artifacts only. Existing release files are not overwritten.
Console testing is manual and separate.

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

This project was developed with assistance from OpenAI Codex, including some original interface artwork. Project maintainers reviewed and validated the resulting code, tests, documentation, dependencies, and generated assets.
