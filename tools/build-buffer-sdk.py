#!/usr/bin/env python3
"""Build an isolated, pinned G7 experiment; never modify the SDK control.

Usage: python3 tools/build-buffer-sdk.py /path/to/ps5-opengl [--texture-flush] [--4k60]
Then: PS5_OPENGL_PREFIX="$PWD/.deps/ps5-opengl-buffer-pool" make native
"""
import hashlib
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]).resolve()
base = root / '.deps/ps5-opengl-core33-g7-60fps'
assert sys.argv[2:] in ([], ['--texture-flush'], ['--texture-flush', '--4k60'])
texture_flush = '--texture-flush' in sys.argv[2:]
four_k = '--4k60' in sys.argv[2:]
suffix = '-texture-flush' if texture_flush else ''
suffix += '-4k60' if four_k else ''
output = root / ('.deps/ps5-opengl-buffer-pool' + suffix)
work = root / ('build/buffer-sdk' + suffix)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


original = source / 'src/gallium/ps5/ps5_screen.c'
assert digest(original) == '04a41802334798d6dc05eb7fd429496ad70790063a8b593901e19c3a3f033721'
assert digest(base / 'manifest.sha256') == '03e535ec8853475385034759e7bc7e63b37ef275591912e3391669b027bd09fc'
subprocess.run(['sha256sum', '--check', '--strict', '--quiet', 'manifest.sha256'], cwd=base, check=True)
assert not output.exists(), 'Keep previous experiment intact; choose a fresh output before rebuilding'
work.mkdir(parents=True, exist_ok=True)
old = 'if (PS5_ENABLE_SHARED_RENDER_POOL_CANDIDATE && ps5->render_pool &&\n       !(templ->bind & PIPE_BIND_DISPLAY_TARGET)'
new = 'if (PS5_ENABLE_SHARED_RENDER_POOL_CANDIDATE && ps5->render_pool &&\n       templ->target == PIPE_BUFFER &&\n       !(templ->bind & PIPE_BIND_DISPLAY_TARGET)'
code = original.read_text()
assert code.count(old) == 1
patched = work / 'ps5_screen.c'
patched.write_text(code.replace(old, new))
if texture_flush:
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i',
                    str(root / 'patches/0002-g7-batch-texture-flush.patch')], cwd=work, check=True)
config = (source / 'build/core33-native-runtime/runtime-config.txt').read_text().splitlines()
assert len(config) == 5
if four_k:
    assert config[4].count('-DPS5_SCANOUT_HEIGHT=1080') == 1
    assert '-DPS5_SCANOUT_FPS=60' in config[4]
    config[4] = config[4].replace('-DPS5_SCANOUT_HEIGHT=1080', '-DPS5_SCANOUT_HEIGHT=2160')
command = [config[0]] + shlex.split(' '.join(config[1:]))
command += ['-I' + str(source / 'src/platform'), '-c', str(patched), '-o', str(work / 'ps5_screen.o')]
(work / 'compile-command.txt').write_text(shlex.join(command) + '\n')
subprocess.run(command, check=True)
objects = [work / 'ps5_screen.o']
if four_k:
    # These three objects share the scanout layout; rebuild them together.
    inputs = {
        'src/egl/ps5_egl.c': 'a1bbcbec10e864af7a13cf5a3438ce66e54c5a84be4ce935fe089c652665580b',
        'src/platform/ps5_agc_runtime_backend.c': '0514fc7de0d5f457ec3709de1654f618fad15eee5d5a277c63a631985e2195ca',
        'src/platform/ps5_agc_native_runtime.c': 'a25251ee53db7540e49b9db3ce716cdab11b6956d15bf63efd138667efbe04c7',
    }
    for name, expected in inputs.items():
        assert digest(source / name) == expected, name
    common = [config[0]] + shlex.split(config[1]) + shlex.split(config[4])
    recipes = {
        'src/egl/ps5_egl.c': ['-DHAVE_PTHREAD=1', '-DHAVE_STRUCT_TIMESPEC=1',
            '-DPS5_ENABLE_COMPRESSED_FALLBACK_CANDIDATE=1', '-DPS5_ENABLE_CORE_CONTEXT_CANDIDATE=1',
            '-Wno-error=unused-parameter', '-Wno-unreachable-code-generic-assoc',
            '-I' + str(source / 'third_party/mesa-26.2.0/src/mesa')],
        'src/platform/ps5_agc_runtime_backend.c': ['-Wno-error=unused-function',
            '-Dmain=ps5_agc_gate2_run', '-DAGC_TRIANGLE_SUBMIT=1', '-DAGC_RUNTIME_PACKAGES=1'],
    }
    for name, flags in recipes.items():
        obj = work / (Path(name).stem + '.o')
        command = common + flags + ['-c', str(source / name), '-o', str(obj)]
        (work / (obj.stem + '-command.txt')).write_text(shlex.join(command) + '\n')
        subprocess.run(command, check=True)
        objects.append(obj)
shutil.copytree(base, output)
archive = Path('lib/libps5_opengl_core33.a')
ar = shutil.which('llvm-ar-21')
assert ar
members = subprocess.check_output([ar, 't', str(base / archive)], text=True).splitlines()
assert members.count('ps5_screen.o') == 1 and len(members) == len(set(members))
subprocess.run([ar, 'r', str(output / archive), *map(str, objects)], check=True)
assert subprocess.check_output([ar, 't', str(output / archive)], text=True).splitlines() == members
for member in members:
    before = subprocess.check_output([ar, 'p', str(base / archive), member])
    after = subprocess.check_output([ar, 'p', str(output / archive), member])
    assert (before != after) == (member in {obj.name for obj in objects}), member
manifest = output / 'manifest.sha256'
manifest.write_text(manifest.read_text().replace(digest(base / archive), digest(output / archive)))
subprocess.run(['sha256sum', '--check', '--strict', '--quiet', 'manifest.sha256'], cwd=output, check=True)
(output / 'BUFFER-POOL-EXPERIMENT.txt').write_text(
    'Private G7 experiment: arena reserved for PIPE_BUFFER; textures use existing checked direct allocation.\n'
    f'Replaced objects: {", ".join(obj.name for obj in objects)}; other archive members verified unchanged.\n'
    'Not a qualified upstream SDK release. Reproduce with tools/build-buffer-sdk.py.\n'
    f'Batch texture flush reuse: {texture_flush}\n'
    f'Render mode: {"3840x2160" if four_k else "1920x1080"} at 60 Hz\n'
    f'Base source SHA256: {digest(original)}\nPatched source SHA256: {digest(patched)}\n'
    f'Runtime SHA256: {digest(output / archive)}\n')
print('Private buffer SDK built and member-checked:', output)
