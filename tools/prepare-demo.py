#!/usr/bin/env python3
"""Extract only the supported official demo's game assets; never run its installer."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from check_game_data import validate

URL = "https://deponie.yamagi.org/quake2/idstuff/q2-314-demo-x86.exe"
MD5 = "4d1cd4618e80a38db59304132ea0856c"


def prepare(archive, destination):
    content = archive.read_bytes()
    if hashlib.md5(content).hexdigest() != MD5:
        raise ValueError("archive does not match the upstream official-demo MD5")
    destination.mkdir(parents=True, exist_ok=True)
    if any(path.name != "README.md" for path in destination.iterdir()):
        raise ValueError("destination contains data; refusing to overwrite or mix game versions")
    selected = {}
    prefix = "Install/Data/baseq2/"
    with zipfile.ZipFile(archive) as source:
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
    parser.add_argument("archive", type=Path, help=f"archive downloaded from {URL}")
    parser.add_argument("--destination", type=Path, default=ROOT / "data/baseq2")
    args = parser.parse_args()
    try:
        prepare(args.archive, args.destination)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f"FAIL: demo preparation: {error}\n")
