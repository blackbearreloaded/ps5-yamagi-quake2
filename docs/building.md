<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Build and dependency reproduction

The supported release uses the frozen 1920x1080/60 Hz SDK in
`dependencies.json`. Run `make deps`, `make test`, then `make package`.
Python 3.12+, Clang, Make, SDL2 and Mesa development libraries are required;
native builds also use Clang/LLD 18 and the pinned public payload toolchain.

`make deps` downloads the complete game SDK from this repository's release,
verifies the archive and SDK checksums, and preserves its source archives and
licenses under `.deps/ps5-yamagi-sdk-1080p-v0.1.0-alpha.3/`.
This is the exact SDK used by the owner-tested current-runtime candidate;
it includes the optimized OpenGL source at `32ca4d4`, built for 1080p60.
It contains the buffer-pool and texture-flush improvements upstream, so the
historical G7 patch is not reapplied to it.

| Dependency | Pin |
| --- | --- |
| Yamagi 8.70 | `76e81f9f3fc3ed859006d81904bfeb6cb33fb525` |
| Native app boilerplate | `722f2227a8bb6fa2229120546995b6562552c752` plus the tracked RELRO patch |
| Public payload SDK / PacBrew SDL2 | `v0.42` / `v0.40.2`, archive hashes checked |
| OpenGL source | `32ca4d4e16c0f29d75b4ae82b74c2df6e1e067bf` |
| SDK manifest | `27fbc1ac29085a5edcb0dc60b9e63bc834284000dcdf439595ba38bf32d73f0b` |
| Runtime archive | `c4e245cc8989257b5c9617250b906091f5e463716d3ca555c2a0e5e42670cc40` |

The repository can remain private: authenticate `gh` with access to this
repository. Actions uses its repository token; no cross-repository token is
needed. Existing dependency caches with different pins must be moved aside
explicitly. Bootstrap does not silently overwrite them.

`make check` validates frozen source, SDK and native helper hashes. `make test`
runs host input/save, lifecycle, resolver, geometry, particle, audio and package
regressions. `make native` stages a complete build under `build/ps5-native-fixed/`.
`make package` adds the hash-verified official demo and original notices to
`dist/PPSA99007.zip`, with an accompanying SHA-256 file.

GitHub Actions publishes the folder ZIP only. FFPFSC downloads were withdrawn
after a console startup failure despite passing offline round-trip checks.
The legacy local `make ffpfsc` target is experimental and is not a supported
installation method.

The SDK bundle includes full graphics/dependency sources and a rebuild guide.
To reproduce the runtime, prepare the pinned OpenGL Mesa/PSBC sources and build
with `PS5_SCANOUT_HEIGHT=1080 PS5_SCANOUT_FPS=60 PS5_GPU_PRESENT_BATCH=1
PS5_DEFERRED_DRAW_BATCH=1 PS5_DRAW_PROFILE=0`. The SDK used Clang 21.1.8.
Changed compiler/debug paths may change binary hashes and need new validation.
The game uses the current 128 MiB native heap helper with all six allocator
wraps, and retains the tested PacBrew SDL2 input/audio integration.

The developer-tested candidate reached 60 FPS including underwater. CI rebuilds
the application independently using the same SDK; its new executable is not
byte-identical to the development build and retains its own validation scope.
