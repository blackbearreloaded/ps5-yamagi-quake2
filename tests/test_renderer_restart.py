#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check actual context cleanup invalidates the static renderer's binding cache."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'src/ps5/ps5_gl3.c').read_text()
start = source.index('GL3_ShutdownContext(void)')
shutdown = source[start:source.index('\n}', start) + 2]
header = (root / 'upstream/yquake2/src/client/refresh/gl3/header/local.h').read_text()
start = header.index('GL3_BindEBO(GLuint ebo)')
bind = header[start:header.index('\n}', start) + 2]
code = r'''
#include <assert.h>
#include <stdbool.h>
#include <string.h>
typedef unsigned GLuint;
static struct { GLuint currentEBO, currentVAO, currentVBO, ppFBO; } gl3state;
static int egl_state, close_ok=1, failures, closes, bound, bindings;
static bool vsync_active;
#define GL_ELEMENT_ARRAY_BUFFER 1
#define Com_Printf(...) ((void)0)
static int ps5_egl_close(int *state) { assert(state==&egl_state); ++closes; bound=0; return close_ok; }
static void ps5_record_failure(void) { ++failures; }
static void glBindBuffer(int target, GLuint buffer) { assert(target==1); bound=buffer; ++bindings; }
''' + 'void ' + shutdown + '\nvoid ' + bind + r'''
int main(void) {
    for (unsigned cycle=0; cycle<6; ++cycle) {
        // The new context reuses the same GL object name after each restart.
        GL3_BindEBO(7);
        assert(bound==7 && bindings==(int)cycle+1);
        gl3state.currentVAO=3; gl3state.currentVBO=5; gl3state.ppFBO=9;
        vsync_active=true;
        GL3_ShutdownContext();
        assert(!gl3state.currentEBO && !gl3state.currentVAO && !gl3state.currentVBO && !gl3state.ppFBO);
        assert(!bound && !vsync_active && !failures && closes==(int)cycle+1);
    }
    close_ok=0; gl3state.currentEBO=7;
    GL3_ShutdownContext();
    assert(failures==1 && gl3state.currentEBO==7);
}
'''
with tempfile.TemporaryDirectory() as folder:
    c, exe = Path(folder)/'restart.c', Path(folder)/'restart'
    c.write_text(code)
    subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('PASS: six static-renderer restarts rebind reused GL object names; cleanup errors remain visible')
