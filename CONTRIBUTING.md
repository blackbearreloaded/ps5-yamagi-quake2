<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Contributing

Run `python3 tools/bootstrap.py --host-only` and `make test` before proposing a
change. Native builds additionally require `make deps` and `make package`.
Keep PS5 adapters in `src/ps5/` and changes to pinned upstream sources in
`patches/0001-ps5-static-gl3-lifecycle.patch`; do not edit the ignored upstream
checkout in place. Preserve upstream notices when importing code.

Keep project copyright and SPDX headers on original files. For upstream
adaptations, retain the original notices and identify the PS5 contributions
separately. Use an adjacent `.license` file for JSON metadata; do not add
project ownership notices to dependencies or game data.

Describe the observed problem, the resulting behavior and the checks actually
run. Separate host checks from console evidence. Record firmware, resolution,
runtime identity, data version and test duration for hardware results. Coordinate
exclusive console access through your environment's lock protocol and release
the lock whenever console work stops.

Do not commit game data, saves, logs containing personal information, toolchain
archives, proprietary SDKs/modules, keys or credentials. Freeze a runtime before
a hardware campaign; do not silently replace its dependency pin between tests.
