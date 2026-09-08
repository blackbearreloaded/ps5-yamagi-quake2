#!/usr/bin/env python3
"""Small regression check for PACK bounds and required startup assets."""
from pathlib import Path
import struct
import tempfile

from check_game_data import pak_entries, validate


def rejects(call):
    try:
        call()
    except (ValueError, OSError):
        return
    raise AssertionError("invalid game data accepted")


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    pak = root / "pak0.pak"
    rejects(lambda: validate(root))
    pak.write_bytes(b"PACK")
    rejects(lambda: pak_entries(pak))
    header = struct.pack("<4sii", b"PACK", 13, 64)
    entry = struct.pack("<56sii", b"test", 12, 1)
    pak.write_bytes(header + b"x" + entry)
    assert pak_entries(pak) == {"test": b"x"}
    rejects(lambda: validate(root))
    for name, start, size in ((b"test", 1000, 1), (b"test", 12, -1),
                              (b"test", 13, 1), (b"../escape", 12, 1)):
        pak.write_bytes(header + b"x" + struct.pack("<56sii", name, start, size))
        rejects(lambda: pak_entries(pak))
    pak.write_bytes(header + b"x" + struct.pack("<56sii", b"tank/../ctank/skin.pcx", 12, 1))
    assert pak_entries(pak)["tank/../ctank/skin.pcx"] == b"x"
print("PASS: missing data, PACK bounds, required assets and legitimate internal alias checks")
