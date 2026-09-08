#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Assemble the native app with the verified official demo and original notices."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from check_game_data import validate

ROOT = Path(__file__).resolve().parents[1]
FILES = ('eboot.bin', 'sce_module/libc.prx', 'sce_sys/param.json',
         'sce_sys/icon0.png', 'sce_sys/pic0.dds', 'sce_sys/pic1.dds',
         'sce_sys/snd0.at9', 'assets/baseq2/yq2.cfg')


def package(stage, demo=None):
    destination = ROOT / 'dist/PPSA99007'
    destination.mkdir(parents=True, exist_ok=True)
    allowed = set(FILES) | {'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'}
    notices = [path.relative_to(ROOT).as_posix() for path in (ROOT / 'LICENSES').glob('*.txt')]
    allowed.update(notices)
    demo_files = []
    if demo is not None:
        validate(demo)
        if hashlib.sha256((demo / 'pak0.pak').read_bytes()).hexdigest() != 'cae257182f34d3913f3d663e1d7cf865d668feda6af393d4ecf3e9e408b48d09':
            raise ValueError('release requires the pinned demo PAK')
        records = json.loads((demo / 'asset-provenance.json').read_text())['files']
        for record in records:
            name = record['path']
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
                raise ValueError('unsafe demo provenance path')
            if name not in ('pak0.pak', 'DEMO-LICENSE.txt', 'DEMO-README.txt') and not name.startswith('players/'):
                raise ValueError('unexpected demo file')
            if hashlib.sha256((demo / name).read_bytes()).hexdigest() != record['sha256']:
                raise ValueError(f'demo file hash mismatch: {name}')
            demo_files.append(name)
        if not {'pak0.pak', 'DEMO-LICENSE.txt', 'DEMO-README.txt'} <= set(demo_files):
            raise ValueError('demo data or original notices missing')
        demo_files.append('asset-provenance.json')
        allowed.update('assets/baseq2/' + name for name in demo_files)
    for path in destination.rglob('*'):
        if path.is_file() and path.relative_to(destination).as_posix() not in allowed:
            raise ValueError(f'Unexpected file in release folder: {path}; move the folder aside first')
    for name in FILES:
        source = stage / name
        if not source.is_file() or not source.stat().st_size:
            raise ValueError(f'Missing or empty app file: {source}')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
    for name in ['README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', *notices]:
        (destination / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination / name)
    for name in demo_files:
        target = destination / 'assets/baseq2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(demo / name, target)
    archive = ROOT / 'dist/PPSA99007.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name in sorted(allowed):
            output.write(destination / name, 'PPSA99007/' + name)
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        assert set(output.namelist()) == {'PPSA99007/' + name for name in allowed}
    with archive.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    (ROOT / 'dist/PPSA99007.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'PASS: archive: {archive} ({archive.stat().st_size} bytes); demo files={len(demo_files)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, default=ROOT / 'dist/PPSA99007')
    parser.add_argument('--demo', type=Path, default=ROOT / '.deps/demo-baseq2')
    args = parser.parse_args()
    package(args.stage.resolve(), args.demo.resolve())
