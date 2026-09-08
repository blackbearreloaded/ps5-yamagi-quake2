#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Check release completeness and reject a game-data-contaminated output folder."""
import importlib.util
from pathlib import Path
import tempfile
import zipfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package', root / 'tools/package.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as folder:
    module.ROOT = Path(folder)
    stage = module.ROOT / 'stage'
    for name in module.FILES:
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture')
    for name in ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'):
        (module.ROOT / name).write_text('fixture\n')
    module.package(stage)
    with zipfile.ZipFile(module.ROOT / 'dist/PPSA99007.zip') as archive:
        assert archive.read('PPSA99007/eboot.bin') == b'fixture'
        assert not any(name.endswith('.pak') for name in archive.namelist())
    unexpected = module.ROOT / 'dist/PPSA99007/assets/baseq2/pak0.pak'
    unexpected.write_bytes(b'not-for-release')
    try:
        module.package(stage)
    except ValueError as error:
        assert 'Unexpected file' in str(error)
    else:
        raise AssertionError('game data was allowed in release output')
    unexpected.unlink()
    (stage / 'sce_module/libc.prx').unlink()
    try:
        module.package(stage)
    except ValueError as error:
        assert 'Missing or empty' in str(error)
    else:
        raise AssertionError('incomplete runtime was packaged')
print('PASS: complete release contents; game data and missing runtime rejected')
