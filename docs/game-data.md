<!--
PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
Copyright (C) 2026 BlackBearReloaded
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Game data

The engine is open source; the original game assets are separate. Do not put
PAK files, player models, music from the original game, or saves into Git.

Current release ZIPs and FFPFSC images already include the official 3.14 demo,
with its original notices. No data preparation is needed to play the demo.
The steps below are for manual preparation or replacing it with your retail data.

## Tested demo

Download the [Quake II 3.14 demo](https://deponie.yamagi.org/quake2/idstuff/q2-314-demo-x86.exe)
linked by the [pinned Yamagi installation guide](https://github.com/yquake2/yquake2/blob/76e81f9f3fc3ed859006d81904bfeb6cb33fb525/doc/020_installation.md).
The following reads its ZIP payload; it does not run the Windows installer:

```bash
python3 tools/prepare-demo.py /path/to/q2-314-demo-x86.exe --destination build/demo-data
python3 tests/check_game_data.py build/demo-data
cp -a build/demo-data/. /path/to/PPSA99007/assets/baseq2/
```

Use a new destination for extraction. Preserve the supplied `yq2.cfg` in the
app folder. The extractor verifies the archive and PAK hashes, rejects unsafe
paths and refuses to overwrite existing data. It extracts `pak0.pak` and
`players/` only, plus a provenance record.

- Archive SHA-256: `7ace5a43983f10d6bdc9d9b6e17a1032ba6223118d389bd170df89b945a04a1e`
- PAK SHA-256: `cae257182f34d3913f3d663e1d7cf865d668feda6af393d4ecf3e9e408b48d09`
- Demo start map: `demo1`; the retail start map `base1` is absent.

The validator checks PACK bounds, required images/configuration, the startup
BSP and its referenced textures. It does not validate every map.

## Retail data

Use data from your own classic Quake II installation and follow Yamagi's
installation guide. Do not mix demo and retail PAKs. Copy the complete required
`baseq2` data into the app's `assets/baseq2/`, preserving this port's `yq2.cfg`.
The 2023 remaster data is not the tested baseline. Retail/expansion campaigns
have not been qualified on this PS5 port.

```bash
python3 tests/check_game_data.py /path/to/PPSA99007/assets/baseq2 --map base1
```
