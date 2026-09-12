#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual native startup arguments; normal builds still open the menu."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'src/ps5/ps5_main.c').read_text()
args = source[source.index('    char *args[]'):source.index('    const char *save_dir')]
code = r'''
#include <assert.h>
#include <string.h>
#define PS5_STRINGIFY_INNER(x) #x
#define PS5_STRINGIFY(x) PS5_STRINGIFY_INNER(x)
#define PS5_OPENGL_NATIVE_FPS 120
int main(void) {
''' + args + r'''
    unsigned menu=0, game=0, coop=0, deathmatch=0, mode=0;
    for (unsigned i=0; args[i]; ++i) {
        menu += !strcmp(args[i], "+menu_main");
        if (!strcmp(args[i], "+map")) { assert(!strcmp(args[i+1], "demo1")); ++game; }
        if (!strcmp(args[i], "coop")) { assert(!strcmp(args[i+1], "0")); ++coop; }
        if (!strcmp(args[i], "deathmatch")) { assert(!strcmp(args[i+1], "0")); ++deathmatch; }
        if (!strcmp(args[i], "r_mode")) { assert(!strcmp(args[i+1], "29")); ++mode; }
    }
#ifdef YQ2_PS5_OPENING_BENCH
    assert(!menu && game==1 && coop==1 && deathmatch==1);
#else
    assert(menu==1 && !game && !coop && !deathmatch);
#endif
#ifdef YQ2_PS5_MODE_BENCH
    assert(mode == 1);
#else
    assert(!mode);
#endif
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c, exe = Path(tmp) / 'start.c', Path(tmp) / 'start'
    c.write_text(code)
    for flags in ([], ['-DYQ2_PS5_OPENING_BENCH=1'], ['-DYQ2_PS5_OPENING_BENCH=1', '-DYQ2_PS5_MODE_BENCH=1']):
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', *flags, str(c), '-o', str(exe)], check=True)
        subprocess.run([str(exe)], check=True)
build = (root / 'tools/build-ps5.sh').read_text()
assert "0) app_definitions='YQ2_PS5 NO_SDL_GYRO'" in build
assert 'YQ2_PS5_OPENING_BENCH=1 YQ2_PS5_RUN_SECONDS=45' in build
assert 'YQ2_PS5_MODE_BENCH=1 YQ2_PS5_RUN_SECONDS=90' in build
print('PASS: normal menu startup and opt-in bounded opening/mode benchmarks')
