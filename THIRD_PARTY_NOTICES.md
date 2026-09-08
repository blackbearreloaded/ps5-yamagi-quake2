# Third-party notices

Project-owned code is GPL-3.0-or-later. Upstream components retain their original
per-file notices and licenses; this repository does not relicense game data.

| Component | Source / license |
| --- | --- |
| Yamagi Quake II 8.70 and id Software engine/game code | [Pinned source](https://github.com/yquake2/yquake2/tree/76e81f9f3fc3ed859006d81904bfeb6cb33fb525), GPL-2.0-or-later and bundled component notices |
| Native app boilerplate / clean-room libc | [Pinned source](https://github.com/blackbearreloaded/ps5-native-app-boilerplate/tree/722f2227a8bb6fa2229120546995b6562552c752), GPL-3.0-or-later and retained notices |
| PS5 OpenGL | [Pinned base](https://github.com/blackbearreloaded/ps5-opengl/tree/cef6c1b869ba3f0c8acaab5b171bbb33eca07f03), GPL-3.0 and dependency-specific notices; game changes supplied here |
| Mesa 26.2.0 / OpenGNM PSBC | Primarily MIT, with per-file exceptions; sources/licenses included in the SDK dependency archive |
| SDL2 / PacBrew PS5 port | [PacBrew sources](https://github.com/ps5-payload-dev/pacbrew-repo), SDL zlib license and port/component notices; pinned binary distribution v0.40.2 |
| Public PS5 Payload SDK v0.42 | [Source](https://github.com/ps5-payload-dev/sdk/tree/v0.42), component-specific licenses; separate build dependency |
| LLVM compiler runtime, libc++, libc++abi, libunwind | [LLVM](https://github.com/llvm/llvm-project), Apache-2.0 with LLVM exceptions and component notices |
| zlib 1.3.2 | [zlib](https://zlib.net/), zlib license; host packaging dependency |

Yamagi also retains notices for bundled GLAD, stb, miniz, xxHash and other
components in its source tree. The source release includes Yamagi's complete
unmodified source; apply the repository's platform patch when rebuilding.

Shell artwork and selection music are project presentation assets supplied or
commissioned by the project owner. The source MP3 and proprietary ATRAC9 encoder
are not distributed. No original Quake II game data is bundled. Quake II and
PlayStation names/trademarks remain the property of their respective owners.

Build pins and source instructions are in `dependencies.json` and
`docs/building.md`. Release dependency archives preserve their own licenses
and sources. Do not substitute proprietary console system modules for the
included clean-room application runtime.
