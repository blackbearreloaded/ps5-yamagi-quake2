#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Check the actual private runtime cache with and without batch reuse.

Usage: python3 tests/test_batch_texture_flush.py /path/to/ps5-opengl
"""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]) / 'src/gallium/ps5/ps5_screen.c'
with tempfile.TemporaryDirectory() as temp:
    work = Path(temp)
    target = work / 'ps5_screen.c'
    target.write_bytes(source.read_bytes())
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i',
                    str(root / 'patches/0002-g7-batch-texture-flush.patch')], cwd=work, check=True)
    code = target.read_text()
    start = code.index('struct ps5_batch_flush_cache {')
    end = code.index('\n}\n', code.index('ps5_flush_batch_backing(', start)) + 3
    helper = code[start:end]
    # The cache is only passed to eligible, retained batches and cleared on drain.
    assert 'bool hazard = !base || base->target != PIPE_BUFFER;' in code
    assert 'memset(&ps5_deferred, 0, sizeof(ps5_deferred));' in code
    assert 'slot == 1 && !merged_geometry ? flush_cache : NULL, 2 + unit' in code
    assert 'context->sampler_views[1][unit]->texture);' in code
    harness = r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define PS5_MAX_TEXTURE_UNITS 16
static unsigned flushes;
static void ps5_flush_gpu_data(const void *data, size_t bytes) {
    (void)data; (void)bytes; ++flushes;
}
''' + helper + r'''
int main(void) {
    char textures[PS5_MAX_TEXTURE_UNITS][64] = {{0}};
    struct ps5_batch_flush_cache cache = {0};
    for (unsigned draw = 0; draw < 200; ++draw)
        for (unsigned unit = 0; unit < PS5_MAX_TEXTURE_UNITS; ++unit)
            ps5_flush_batch_backing(&cache, 2 + unit, textures[unit], 64);
#ifdef PS5_GPU_PRESENT_BATCH
    assert(flushes == PS5_MAX_TEXTURE_UNITS);
#else
    assert(flushes == 200 * PS5_MAX_TEXTURE_UNITS);
#endif
    unsigned before = flushes;
    /* Changed size/backing, depth planes, and a fresh batch must flush. */
    ps5_flush_batch_backing(&cache, 2, textures[0], 32);
    ps5_flush_batch_backing(&cache, 2, textures[1], 32);
    ps5_flush_batch_backing(&cache, 0, textures[0], 64);
    ps5_flush_batch_backing(&cache, 1, textures[0], 64);
    memset(&cache, 0, sizeof(cache));
    ps5_flush_batch_backing(&cache, 2, textures[1], 32);
    ps5_flush_batch_backing(NULL, 2, textures[1], 32);
    ps5_flush_batch_backing(NULL, 2, textures[1], 32);
    assert(flushes == before + 7);
    return 0;
}
'''
    test = work / 'cache.c'
    test.write_text(harness)
    for defines in ([], ['-DPS5_GPU_PRESENT_BATCH=1']):
        executable = work / ('test-' + str(len(defines)))
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', *defines, str(test),
                        '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
print('Batch texture flush: repetition, replacement, depth isolation, drain reset and uncached paths passed')
