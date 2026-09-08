#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Extract only the supported official demo's game assets; never run its installer."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from check_game_data import validate

URL = "https://deponie.yamagi.org/quake2/idstuff/q2-314-demo-x86.exe"
MD5 = "4d1cd4618e80a38db59304132ea0856c"
SHA256 = "7ace5a43983f10d6bdc9d9b6e17a1032ba6223118d389bd170df89b945a04a1e"


def prepare(archive, destination):
    content = archive.read_bytes()
    if hashlib.sha256(content).hexdigest() != SHA256:
        raise ValueError("archive does not match the pinned official-demo SHA-256")
    destination.mkdir(parents=True, exist_ok=True)
    selected = {}
    prefix = "Install/Data/baseq2/"
    with zipfile.ZipFile(archive) as source:
        selected['DEMO-LICENSE.txt'] = source.read('license.txt')
        selected['DEMO-README.txt'] = source.read('readme.txt')
        for info in source.infolist():
            if not info.filename.startswith(prefix) or info.is_dir():
                continue
            name = info.filename[len(prefix):]
            path = PurePosixPath(name)
            if name != "pak0.pak" and not name.startswith("players/"):
                continue
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or name in selected:
                raise ValueError(f"unsafe or duplicate archive member: {name}")
            selected[name] = source.read(info)
    if "pak0.pak" not in selected or hashlib.md5(selected["pak0.pak"]).hexdigest() != "27d77240466ec4f3253256832b54db8a":
        raise ValueError("demo pak0 differs from upstream hash")
    existing = {p.relative_to(destination).as_posix(): p for p in destination.rglob('*')
                if p.is_file() and p.name not in ('README.md', 'asset-provenance.json')}
    if existing:
        if set(existing) != set(selected) or any(existing[n].read_bytes() != data for n, data in selected.items()):
            raise ValueError('destination contains different data; refusing to overwrite or mix game versions')
        validate(destination)
        print('PASS: existing demo files and original notices match the pinned archive')
        return
    with tempfile.TemporaryDirectory(prefix="yamagi-demo-") as temporary:
        staged = Path(temporary)
        (staged / "pak0.pak").write_bytes(selected["pak0.pak"])
        count, textures = validate(staged)
    records = []
    for name, data in sorted(selected.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(data)
        records.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    provenance = {"source": URL, "archive_md5": MD5, "archive_sha256": hashlib.sha256(content).hexdigest(),
                  "archive_bytes": len(content), "startup_map": "demo1", "demo": "q2demo1", "files": records}
    with (destination / "asset-provenance.json").open("x") as output:
        json.dump(provenance, output, indent=2)
        output.write("\n")
    print(f"PASS: extracted {len(records)} files; {count} PAK entries; {textures} startup-map textures")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, nargs='?', default=ROOT / '.deps/q2-314-demo-x86.exe', help=f"archive downloaded from {URL}")
    parser.add_argument('--download', action='store_true', help='download the pinned archive if missing')
    parser.add_argument("--destination", type=Path, default=ROOT / "data/baseq2")
    args = parser.parse_args()
    try:
        if args.download and not args.archive.exists():
            args.archive.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.archive.with_suffix('.download')
            with urllib.request.urlopen(URL, timeout=60) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != SHA256:
                raise ValueError('download SHA-256 mismatch')
            temporary.rename(args.archive)
        prepare(args.archive, args.destination)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"FAIL: demo preparation: {error}\n")
