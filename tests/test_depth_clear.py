#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Execute the actual clear routine and frame/target call sites with GL sinks."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
name = 'src/client/refresh/gl3/gl3_main.c'
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder)
    source = work / name
    source.parent.mkdir(parents=True)
    source.write_bytes((root / 'upstream/yquake2' / name).read_bytes())
    subprocess.run(['git', 'apply', '--include=' + name,
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=work, check=True)
    code = source.read_text()
    start = code.index('GL3_Clear(void)\n{')
    clear = code[start:code.index('\n}', start) + 2]
    start = code.index('\t/* clear screen if desired */')
    begin = code[start:code.index('\n}', start)]
    start = code.index('\telse // rendering directly (not to FBO for postprocessing)')
    direct = code[code.index('{', start) + 1:code.index('\n\t}', start)]
    fbo = 'GL3_Clear(); // clear the FBO that\'s bound now'
    assert code.count(fbo) == 1
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
typedef unsigned GLbitfield;
enum { GL_COLOR_BUFFER_BIT=1, GL_DEPTH_BUFFER_BIT=2, GL_STENCIL_BUFFER_BIT=4, GL_LEQUAL=7 };
static struct { bool ppFBObound; } gl3state;
static struct { bool stencil; } gl3config;
static struct { float value; } clear_setting, shadows, zfix;
#define r_clear (&clear_setting)
#define gl_shadows (&shadows)
#define gl_zfix (&zfix)
static float gl3depthmin, gl3depthmax;
static unsigned calls[2][3];
static void glClear(unsigned mask) {
    for (int bit=0; bit<3; ++bit) calls[gl3state.ppFBObound][bit] += !!(mask & (1u<<bit));
}
static void glDepthFunc(unsigned mode) { assert(mode == GL_LEQUAL); }
static void glDepthRange(double a, double b) { assert(a == 0 && b == 1); }
static void glPolygonOffset(float a, float b) { assert(a == 0.05f && b == 1); }
static void glClearStencil(int value) { assert(value == 1); }
static void glViewport(int x, int y, int w, int h) { (void)x; (void)y; (void)w; (void)h; }
''' + '\nstatic void\n' + clear + '\nstatic void begin(void) {\n' + begin + '\n}\n'
    harness += '\nstatic void target(bool offscreen) { int x=0,y2=0,w=3840,h=2160; if (offscreen) {\n' + fbo + '\n} else {\n' + direct + '\n} }\n'
    harness += r'''
int main(void) {
    for (unsigned color=0; color<2; ++color) for (unsigned offscreen=0; offscreen<2; ++offscreen)
    for (unsigned stencil=0; stencil<2; ++stencil) {
        for (int a=0; a<2; ++a) for (int b=0; b<3; ++b) calls[a][b]=0;
        gl3state.ppFBObound=false; r_clear->value=color;
        gl_shadows->value=stencil; gl3config.stencil=true; gl_zfix->value=1;
        begin();
#ifdef YQ2_PS5
        assert(calls[0][0] == color && calls[0][1] == 0 && calls[0][2] == 0);
#endif
        gl3state.ppFBObound=offscreen; target(offscreen);
#ifdef YQ2_PS5
        assert(calls[0][1] + calls[1][1] == 1);
        assert(calls[offscreen][1] == 1 && calls[offscreen][2] == stencil);
        assert(calls[0][0] == color && calls[1][0] == color * offscreen);
#else
        assert(calls[0][1] == 1 && calls[1][1] == offscreen);
#endif
        assert(gl3depthmin == 0 && gl3depthmax == 1);
    }
    puts("PASS: native clears depth once on its selected target; color/stencil and desktop behavior retained");
}
'''
    (work / 'clear.c').write_text(harness)
    for flags in ([], ['-DYQ2_PS5']):
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Wno-unused-function',
                        '-fsanitize=address,undefined', *flags, str(work / 'clear.c'),
                        '-o', str(work / 'clear')], check=True)
        subprocess.run([str(work / 'clear')], check=True)
