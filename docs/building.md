# Build and dependency reproduction

The supported app build uses the frozen 1920×1080 game SDK in
`dependencies.json`. `make deps` checks source revisions, verifies the downloaded
PS5 OpenGL GitHub release archive and the small game overlay, validates their
manifests and restores the public native toolchain. Every upstream SDK archive
except the game-adapted runtime remains byte-identical to the OpenGL release.
Native compilation then fetches hash-pinned PacBrew SDL2 if needed. These caches
are local and ignored by Git. Python 3.12 is required for safe tar extraction.

The published native-app revision is combined with
`patches/0003-native-relro-alignment.patch`, reproducing the tested local
packaging fix without relying on its unpublished commit.

The repository can remain private: `gh auth login` must authenticate an account
with access to download its runtime overlay release asset. In Actions, `GH_TOKEN` is supplied
from the repository token. The manual native job has contents-write permission
to attach requested release artifacts; the host job remains read-only.
No token is written into source or bundles.

While PS5 OpenGL is private, native CI first fetches an unchanged copy of its
release archive from this game's private release. The ordinary bootstrap still
downloads directly from `blackbearreloaded/ps5-opengl`. Both paths verify the
same upstream SHA-256 before extraction; the cache is not a different SDK build.
This avoids giving Actions a personal token with access to other repositories.

| Dependency | Pin |
| --- | --- |
| Yamagi 8.70 | `76e81f9f3fc3ed859006d81904bfeb6cb33fb525` |
| Native-app boilerplate | `722f2227a8bb6fa2229120546995b6562552c752` |
| Public PS5 Payload SDK | `v0.42`, hash checked by the pinned boilerplate |
| PacBrew | `v0.40.2`, hash checked by the pinned boilerplate |
| Game OpenGL source base | `cef6c1b869ba3f0c8acaab5b171bbb33eca07f03` |
| Frozen SDK manifest SHA-256 | `4a3f0b68f33a051d2c2efe108c6efe10ded1b8c584e8250852c09fd5cdf6eb9e` |
| Frozen runtime archive SHA-256 | `ca7298b024974bd26eb9456964c220db90b17a774eacf8d114fe3d5de4bbb888` |

`make check` verifies SDK and helper hashes. `make test` runs the host contracts,
input queue/save tests, lifecycle, native resolver, FPS, triangle/world batching,
particle GLSL rendering, glyph and PCM regressions. It needs a host SDL2 library,
Mesa EGL/GL and glslang; it does not need game data or a console.

`make native` stages a patched Yamagi checkout under `build/ps5-native-fixed/`,
builds the native executable and clean-room libc, validates the already converted
presentation assets. `make package` adds the hash-pinned official demo and its
original notices to `dist/PPSA99007.zip`. Packaging uses an explicit file allowlist
and rejects unexpected files left in the output folder, including saves or retail data.

`make ffpfsc` then compresses that same allowlisted folder with MkPFS
`6cb8313dfe0c988ac52617794553f343243d3a56`, restored through the existing
boilerplate helper. MkPFS `--verify` checks the image contents before the build
writes `PPSA99007.ffpfsc.sha256`. The image is also unpacked, compared byte-for-byte
with the source folder and checked for its required startup assets. Python venv
support is required. The resulting image includes the demo and can launch directly.

The public source archive supplied with the release includes the game repository
and the pinned Yamagi source tree. The extracted OpenGL release's `sources/`
includes Mesa, PSBC and other dependency sources. The game overlay also supplies
the exact runtime source base and changed screen source. Apply the game patch from
this repository to Yamagi; keep dependency notices with redistributed binaries.

## Rebuilding the experimental graphics SDK from source

Normal app builds consume the frozen SDK. Rebuilding that SDK is a separate
developer workflow and may produce different bytes with another compiler/path.
The OpenGL GitHub release supplies the G7 base SDK. The overlay's
`sources/game-changes/` contains the original compile flags and game delta.

Restore the OpenGL source/dependencies following its pinned `docs/building.md`,
and copy the release's `sdk/` under `.deps/ps5-opengl-core33-g7-60fps/` in this
repository. Relocate the original compile flags to your source/compiler paths in
the OpenGL checkout's `build/core33-native-runtime/runtime-config.txt`.
Then run:

```bash
python3 tools/build-buffer-sdk.py /path/to/ps5-opengl --texture-flush
```

The recipe checks base hashes, applies the buffer-only arena change and texture
flush patch, and verifies that only `ps5_screen.o` changed in the archive.
Its output is separate from `.deps/game-sdk`; do not replace the frozen SDK or
change release pins without a new validation campaign. The optional 4K recipe
is experimental and deliberately rejected by the 1080p release `make check`.
