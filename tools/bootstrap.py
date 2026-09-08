#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Restore immutable source pins and the release's frozen 1080p SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def checkout(url, revision, destination):
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        run('git', 'clone', '--no-checkout', url, str(destination))
        run('git', '-C', str(destination), 'checkout', '--detach', revision)
    head = subprocess.check_output(['git', '-C', str(destination), 'rev-parse', 'HEAD'], text=True).strip()
    if head != revision:
        raise SystemExit(f'{destination}: wrong revision; preserve it and move it aside before retrying')
    run('git', '-C', str(destination), 'diff', '--exit-code', 'HEAD', '--')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-only', action='store_true')
    args = parser.parse_args()
    pins = json.loads((ROOT / 'dependencies.json').read_text())
    for name in ('yamagi',) if args.host_only else ('yamagi', 'native_app'):
        pin = pins[name]
        checkout(pin['url'], pin['revision'], ROOT / pin['directory'])
    if args.host_only:
        return
    sdk = pins['game_sdk']
    cache = ROOT / '.deps'
    destination = cache / 'game-sdk'
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix='opengl-', dir=cache) as folder:
            work = Path(folder)
            for pin in (pins['opengl'], sdk):
                archive = cache / pin['asset']
                if not archive.exists():
                    run('gh', 'release', 'download', pin['tag'], '--repo', pin['repository'],
                        '--pattern', pin['asset'], '--dir', str(cache))
                with archive.open('rb') as file:
                    digest = hashlib.file_digest(file, 'sha256').hexdigest()
                if digest != pin['sha256']:
                    raise SystemExit(f'{archive}: SHA-256 mismatch; refusing extraction')
                with tarfile.open(archive) as source:
                    source.extractall(work, filter='data')
            base = work / pins['opengl']['directory']
            run('sha256sum', '--check', '--strict', '--quiet', 'manifest.sha256', cwd=base / 'sdk')
            shutil.copytree(base / 'sdk', work / 'game-sdk')
            shutil.copytree(work / 'game-overlay', work / 'game-sdk', dirs_exist_ok=True)
            run('sha256sum', '--check', '--strict', '--quiet', 'manifest.sha256', cwd=work / 'game-sdk')
            (work / 'game-sdk').rename(destination)
            # Preserve upstream sources and notices alongside the consumer SDK.
            source_cache = cache / pins['opengl']['directory']
            if not source_cache.exists():
                base.rename(source_cache)
    run('bash', str(ROOT / 'tools/check.sh'))
    template = ROOT / pins['native_app']['directory']
    run('bash', str(template / 'tools/setup-native-dependencies.sh'))
    pacbrew = cache / 'pacbrew'
    if not pacbrew.exists():
        run('bash', str(template / 'tools/setup-pacbrew-dependencies.sh'), '--resolve', 'sdl2')
        pacbrew.symlink_to(template / '.deps/pacbrew', target_is_directory=True)


if __name__ == '__main__':
    main()
