#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Run the patched glyph batch and PCM callback with bounded host sinks."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
paths = ['src/client/refresh/gl3/gl3_draw.c', 'src/client/sound/sdl.c']
with tempfile.TemporaryDirectory() as folder:
    for path in paths:
        target = Path(folder) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / 'upstream/yquake2' / path, target)
        target.chmod(0o644)
    subprocess.run(['git', 'apply', *['--include=' + p for p in paths],
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=folder, check=True)
    draw, audio = [(Path(folder) / p).read_text() for p in paths]

def function(text, name):
    start = text.index(name + '(')
    end = text.index('\n}', start) + 2
    return text[start:end]

batch = draw[draw.index('static GLfloat charVertices'):draw.index('\n#endif', draw.index('static GLfloat charVertices'))]
glyph = r'''
#define YQ2_PS5 1
#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef float GLfloat;
enum { GL_ARRAY_BUFFER, GL_STREAM_DRAW, GL_TRIANGLES };
static int vao2D, vbo2D;
static struct { struct { int shaderProgram; } si2D; } gl3state;
static struct { int texnum; } chars, *draw_chars = &chars;
static unsigned draws, uploaded;
static GLfloat first_vertex[4];
#define GL3_UseProgram(x) ((void)(x))
#define GL3_Bind(x) ((void)(x))
#define GL3_BindVAO(x) ((void)(x))
#define GL3_BindVBO(x) ((void)(x))
static void glBufferData(int target, unsigned bytes, const void *data, int usage) {
    assert(target == GL_ARRAY_BUFFER && usage == GL_STREAM_DRAW);
    assert(bytes <= 1024 * 6 * 4 * sizeof(GLfloat));
    uploaded = bytes / (4 * sizeof(GLfloat));
    memcpy(first_vertex, data, sizeof(first_vertex));
}
static void glDrawArrays(int mode, int first, unsigned count) {
    assert(mode == GL_TRIANGLES && first == 0 && count == uploaded);
    assert(count && count % 6 == 0);
    ++draws;
}
''' + batch + '\nvoid\n' + function(draw, 'GL3_Draw_CharScaled') + r'''
int main(void) {
    GL3_Draw_CharScaled(10, 20, 32, 2);
    GL3_Draw_CharScaled(10, -9, 65, 2);
    assert(charVertexCount == 0 && draws == 0);
    for (int i=0; i<1025; ++i) GL3_Draw_CharScaled(10, 20, 65, 2);
    assert(draws == 1 && charVertexCount == 6);
    assert(first_vertex[0] == 10 && first_vertex[1] == 36);
    assert(first_vertex[2] == 0.0625f && first_vertex[3] == 0.3125f);
    GL3_FlushChars();
    assert(draws == 2 && charVertexCount == 0);
    GL3_FlushChars();
    assert(draws == 2);
    puts("PASS: 1025 glyphs in two bounded draws, coordinates and empty flush");
}
'''
pcm = r'''
#define YQ2_PS5 1
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char Uint8;
static struct { int samplebits, channels, samples; Uint8 *buffer; } sound, *backend = &sound;
static int playpos, samplesize, snd_inited=1, paintedtime, soundtime;
static uint64_t played_samples;
static void S_StopAllSounds(void) {}
''' + '\nstatic void\n' + function(audio, 'SDL_Callback') + '\nstatic void\n' + function(audio, 'SDL_UpdateSoundtime') + r'''
int main(void) {
    Uint8 ring[64], output[24];
    sound.samplebits=16; sound.channels=2; sound.samples=32; sound.buffer=ring; samplesize=64;
    memset(ring, 0x41, sizeof(ring));
    playpos=28;
    SDL_Callback(NULL, output, 24); /* Wrap across the physical end. */
    for (unsigned i=0; i<sizeof(output); ++i) assert(output[i] == 0x41);
    assert(played_samples == 12 && playpos == 8);
    for (int i=0; i<16; ++i) SDL_Callback(NULL, output, 24);
    for (unsigned i=0; i<sizeof(output); ++i) assert(output[i] == 0);
    SDL_UpdateSoundtime();
    assert(soundtime == 17 * 6); /* Count all wraps, even without mixer updates. */
    sound.samplebits=8; playpos=0; memset(ring, 0x42, sizeof(ring));
    SDL_Callback(NULL, output, 24);
    for (int i=0; i<24; ++i) assert(ring[i] == 128);
    puts("PASS: wrapped PCM is consumed once, underrun is silent, playback clock counts every sample");
}
'''
compiler = shutil.which('clang-18') or shutil.which('cc')
assert compiler, 'Host C compiler required'
with tempfile.TemporaryDirectory() as folder:
    for name, code in [('glyph', glyph), ('pcm', pcm)]:
        source = Path(folder) / (name + '.c')
        executable = Path(folder) / name
        source.write_text(code)
        subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                        '-fsanitize=address,undefined', str(source), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
