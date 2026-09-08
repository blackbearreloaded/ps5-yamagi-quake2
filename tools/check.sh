#!/usr/bin/env bash
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

# Read-only dependency check; does not rebuild, deploy or contact the console.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
prefix=$(realpath -- "${PS5_OPENGL_PREFIX:-$root/.deps/game-sdk}")
manifest=$(sha256sum "$prefix/manifest.sha256" | cut -d' ' -f1)
[[ $manifest == 4a3f0b68f33a051d2c2efe108c6efe10ded1b8c584e8250852c09fd5cdf6eb9e ]] || { echo "FAIL: expected the frozen 1080p SDK." >&2; exit 1; }
(cd "$prefix" && sha256sum --check --strict manifest.sha256 >/dev/null)
[[ $(git -C "$root/upstream/yquake2" rev-parse HEAD) == 76e81f9f3fc3ed859006d81904bfeb6cb33fb525 ]] || {
    echo 'FAIL: Yamagi base commit differs from the handoff.' >&2; exit 1;
}
(cd "$root/tooling/native" && sha256sum --check --strict SHA256SUMS >/dev/null)
git -C "$root/upstream/yquake2" diff --exit-code HEAD -- >/dev/null
printf '%s\n' 'PASS: frozen SDK, Yamagi base commit and copied native helper hashes.' \
    'This does not validate game patches, native packaging or console execution.'
