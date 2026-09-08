#!/usr/bin/env python3
"""Assemble only explicitly allowed, game-data-free release files."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('eboot.bin', 'sce_module/libc.prx', 'sce_sys/param.json',
         'sce_sys/icon0.png', 'sce_sys/pic0.dds', 'sce_sys/pic1.dds',
         'sce_sys/snd0.at9', 'assets/baseq2/yq2.cfg')


def package(stage):
    destination = ROOT / 'dist/PPSA99007'
    destination.mkdir(parents=True, exist_ok=True)
    allowed = set(FILES) | {'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'}
    notices = [path.relative_to(ROOT).as_posix() for path in (ROOT / 'LICENSES').glob('*.txt')]
    allowed.update(notices)
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
    print(f'PASS: game-data-free archive: {archive} ({archive.stat().st_size} bytes)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, default=ROOT / 'dist/PPSA99007')
    package(parser.parse_args().stage.resolve())
