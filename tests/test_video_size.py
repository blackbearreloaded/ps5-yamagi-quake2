#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise the actual native adapter with 1080p/4K and failed size queries."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
code = (root / 'src/ps5/ps5_video.c').read_text().replace(
    '#include "../../upstream/yquake2/src/client/vid/header/ref.h"', '')
stub = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
typedef bool qboolean;
typedef struct { float value; } cvar_t;
typedef struct { int width, height; } viddef_t;
typedef struct {
    int (*PrepareForWindow)(void);
    qboolean (*InitContext)(void *);
    void (*GetDrawableSize)(int *, int *);
    void (*ShutdownContext)(void);
} refexport_t;
#define CVAR_ARCHIVE 1
static cvar_t rate = {29};
static cvar_t *Cvar_Get(const char *a, const char *b, int c) {
    (void)a; (void)b; (void)c; return &rate;
}
static void Cvar_SetValue(const char *name, float value) { (void)name; rate.value = value; }
static void Com_Printf(const char *format, ...) { (void)format; }
void GLimp_ShutdownGraphics(void);
'''
test = r'''
static int actual_width, actual_height, starts, stops, prepare_result;
static qboolean init_result = true;
static int prepare(void) { return prepare_result; }
static qboolean init(void *window) {
    assert(window); const int *size = window;
    assert((size[0]==1920 && size[1]==1080) || (size[0]==2560 && size[1]==1440) || (size[0]==3840 && size[1]==2160));
    ++starts; return init_result;
}
static void size(int *w, int *h) { *w = actual_width; *h = actual_height; }
static void stop(void) { ++stops; }
refexport_t re = {prepare, init, size, stop};
viddef_t viddef;
int main(void) {
    int w, h;
    assert(GLimp_Init());
    assert(GLimp_GetRefreshRate() == PS5_OPENGL_NATIVE_FPS);
    rate.value = 75;
    assert(GLimp_GetRefreshRate() == PS5_OPENGL_NATIVE_FPS);
    assert(GLimp_Init() && rate.value == 29);
    assert(GLimp_GetDesktopMode(&w, &h));
    assert(w == PS5_OPENGL_NATIVE_WIDTH && h == PS5_OPENGL_NATIVE_HEIGHT);
    assert(!GLimp_InitGraphics(1, NULL, &h) && starts == 0);
    const int widths[] = {1920,2560,3840}, heights[] = {1080,1440,2160};
    for (int mode = 0; mode < 3; ++mode) {
        actual_width = w = widths[mode];
        actual_height = h = heights[mode];
        assert(GLimp_InitGraphics(1, &w, &h));
        assert(w == actual_width && h == actual_height);
        assert(viddef.width == w && viddef.height == h);
        int count = starts;
        assert(GLimp_InitGraphics(1, &w, &h) && starts == count);
        assert(GLimp_GetDesktopMode(&w, &h));
        assert(w == actual_width && h == actual_height);
        GLimp_ShutdownGraphics();
    }
    w=640; h=480;
    assert(!GLimp_InitGraphics(1, &w, &h) && starts==3);
    w=1920; h=1080;
    actual_width = 0;
    assert(!GLimp_InitGraphics(1, &w, &h) && stops == 4);
    GLimp_ShutdownGraphics();
    assert(stops == 4);
    w=1920; h=1080;
    prepare_result = -1;
    int count = starts;
    assert(!GLimp_InitGraphics(1, &w, &h) && starts == count);
    prepare_result = 0;
    init_result = false;
    assert(!GLimp_InitGraphics(1, &w, &h));
    return 0;
}
'''
with tempfile.TemporaryDirectory() as temp:
    source = Path(temp) / 'video.c'
    output = Path(temp) / 'video'
    source.write_text(stub + code + test)
    for width, height, fps in ((1920, 1080, 120), (2560, 1440, 120), (3840, 2160, 120)):
        (Path(temp) / 'ps5_opengl_display.h').write_text(
            f'#define PS5_OPENGL_NATIVE_WIDTH {width}\n'
            f'#define PS5_OPENGL_NATIVE_HEIGHT {height}\n'
            f'#define PS5_OPENGL_NATIVE_FPS {fps}\n')
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', str(source), '-o', str(output)], check=True)
        subprocess.run([str(output)], check=True)
print('PASS: requested 1080p/1440p/2160p reaches context and engine, fixed 120 Hz, repeat init, unsupported modes and failures')
