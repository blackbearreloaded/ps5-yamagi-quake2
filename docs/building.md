<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Build and dependency reproduction

The supported release uses the frozen selectable-resolution 120 Hz SDK in
`dependencies.json`. Run `make deps`, `make test`, then `make package`.
Python 3.12+, Clang, Make, SDL2 and Mesa development libraries are required;
native builds also use Clang/LLD 18 and the pinned public payload toolchain.

`make deps` downloads the complete game SDK from this repository's release,
verifies the archive and SDK checksums, and preserves its source archives and
licenses under `.deps/ps5-yamagi-sdk-120hz-v0.2.0-alpha.1/`.
This is the exact SDK used by the owner-tested current-runtime candidate;
it includes OpenGL source at `32ca4d4` plus the game-specific runtime patches,
built for 1080p, 1440p and 2160p at 120 Hz.
It contains the buffer-pool and texture-flush improvements upstream, so the
historical G7 patch is not reapplied to it.

| Dependency | Pin |
| --- | --- |
| Yamagi 8.70 | `76e81f9f3fc3ed859006d81904bfeb6cb33fb525` |
| Native app boilerplate | `722f2227a8bb6fa2229120546995b6562552c752` plus the tracked RELRO patch |
| Public payload SDK / PacBrew SDL2 | `v0.42` / `v0.40.2`, archive hashes checked |
| OpenGL source | `32ca4d4e16c0f29d75b4ae82b74c2df6e1e067bf` |
| SDK manifest | `e73d2a40c5c67bd15c6cf1805c2ec4890286e311811d0546f0656a36e267fa99` |
| Runtime archive | `f4641d706911fc5b72aa780efca52744bedf9173c6592a17815417abc90eeccf` |

Authenticate `gh` for release asset downloads. Actions uses its repository
token; no cross-repository token is
needed. Existing dependency caches with different pins must be moved aside
explicitly. Bootstrap does not silently overwrite them.

`make check` validates frozen source, SDK and native helper hashes. `make test`
runs host input/save, lifecycle, resolver, geometry, particle, audio, resolution
switching, renderer restart and package regressions. `make native` stages a
complete build under `build/ps5-native-fixed/`.
`make package` adds the hash-verified official demo and original notices to
`dist/PPSA99007.zip`, with an accompanying SHA-256 file.

GitHub Actions publishes the folder ZIP only. FFPFSC downloads were withdrawn
after a console startup failure despite passing offline round-trip checks.
The legacy local `make ffpfsc` target is experimental and is not a supported
installation method.

The SDK bundle includes full graphics/dependency sources and a rebuild guide.
`sources/game-runtime-source.tar.xz` contains the exact patched runtime and its
matching PSBC headers. `sources/game-changes/` contains the runtime patches
and focused checks. Use the bundle's README to prepare Mesa/PSBC and rebuild
the runtime with these settings:

```text
PS5_SCANOUT_HEIGHT=2160 PS5_SCANOUT_FPS=120 PS5_GPU_PRESENT_BATCH=1
PS5_DEFERRED_DRAW_BATCH=1 PS5_DRAW_PROFILE=0 PS5_COMMAND_POOL=1
PS5_BATCH_POLL_US=100 PS5_SCANOUT_RANGE_FLUSH=1 PS5_CPU_PRESENT_OVERLAP=1
PS5_DEFERRED_COMMAND_TAIL=1 PS5_DYNAMIC_SCANOUT=1
```

The SDK used Clang 21.1.8, PSBC revision
`a92a1228ea3a64e4be9f0e61c2a65a5aa7ffed92` and its matching ABI-1960 headers.
Changed compiler/debug paths may change binary hashes and need new validation.
The game uses the current 128 MiB native heap helper with all six allocator
wraps, and retains the tested PacBrew SDL2 input/audio integration.

Normal builds open the menu and allow unlimited play. Diagnostic builds are
opt-in: `YQ2_PS5_OPENING_BENCH=1` captures the opening scene for 45 seconds;
`YQ2_PS5_MODE_BENCH=1` exercises repeated resolution switches for 90 seconds.
Neither is enabled in release packages.

CI rebuilds the application independently using the same SDK; its executable
is not byte-identical to the development build and retains its own validation
scope. See the release's validation receipt for checks on the downloadable ZIP.
