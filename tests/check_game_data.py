#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Check the selected Quake II startup assets before staging an application."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import posixpath
import struct


def pak_entries(path):
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError(f"{path}: truncated PACK header")
    magic, offset, length = struct.unpack_from("<4sii", data)
    if magic != b"PACK" or offset < 12 or length <= 0 or length % 64 or offset + length > len(data):
        raise ValueError(f"{path}: invalid PACK directory")
    entries = {}
    for pos in range(offset, offset + length, 64):
        raw, start, size = struct.unpack_from("<56sii", data, pos)
        name = raw.split(b"\0", 1)[0].decode("ascii")
        parts = PurePosixPath(name)
        normalized = posixpath.normpath(name)
        # The official demo has tank/../ctank aliases inside its PAK; these
        # names stay inside the archive and are never extracted as paths here.
        if not name or parts.is_absolute() or normalized == ".." or normalized.startswith("../") or "\\" in name or ":" in name or name in entries:
            raise ValueError(f"{path}: unsafe or duplicate entry {name!r}")
        if start < 12 or size < 0 or start + size > len(data) or (size and start < offset + length and start + size > offset):
            raise ValueError(f"{path}: entry outside payload: {name}")
        entries[name] = data[start:start + size]
    return entries


def validate(baseq2, map_name="demo1"):
    entries = pak_entries(baseq2 / "pak0.pak")
    required = ("default.cfg", "pics/colormap.pcx", "pics/conchars.pcx", f"maps/{map_name}.bsp")
    for name in required:
        if not entries.get(name):
            raise ValueError(f"missing or empty required asset: {name}")
    bsp = entries[f"maps/{map_name}.bsp"]
    if len(bsp) < 160 or struct.unpack_from("<4si", bsp) != (b"IBSP", 38):
        raise ValueError("unsupported or truncated startup BSP")
    for index in range(19):
        offset, length = struct.unpack_from("<ii", bsp, 8 + index * 8)
        if offset < 0 or length < 0 or offset + length > len(bsp):
            raise ValueError("startup BSP lump outside file")
    offset, length = struct.unpack_from("<ii", bsp, 8 + 5 * 8)
    if not length or length % 76:
        raise ValueError("invalid startup BSP texture information")
    textures = set()
    for pos in range(offset, offset + length, 76):
        texture = bsp[pos + 40:pos + 72].split(b"\0", 1)[0].decode("ascii")
        name = f"textures/{texture}.wal"
        if not entries.get(name):
            raise ValueError(f"startup map requires missing texture: {name}")
        textures.add(name)
    return len(entries), len(textures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseq2", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "data/baseq2")
    parser.add_argument("--map", default="demo1", help="startup map (official demo: demo1; retail: base1)")
    args = parser.parse_args()
    try:
        count, textures = validate(args.baseq2, args.map)
        digest = hashlib.sha256((args.baseq2 / "pak0.pak").read_bytes()).hexdigest()
        print(f"PASS: game assets: {count} PAK entries, map={args.map}, {textures} map textures; pak0.sha256={digest}")
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"FAIL: game assets: {error}\n")
