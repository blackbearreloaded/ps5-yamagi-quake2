#!/usr/bin/env python3
"""Exercise the actual native adapter with 1080p/4K and failed size queries."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
code = (root / 'src/ps5/ps5_video.c').read_text().split('\n', 1)[1]
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
static cvar_t rate = {-1};
static cvar_t *Cvar_Get(const char *a, const char *b, int c) {
    (void)a; (void)b; (void)c; return &rate;
}
static void Com_Printf(const char *format, ...) { (void)format; }
void GLimp_ShutdownGraphics(void);
'''
test = r'''
static int actual_width, actual_height, starts, stops, prepare_result;
static qboolean init_result = true;
static int prepare(void) { return prepare_result; }
static qboolean init(void *window) { assert(window); ++starts; return init_result; }
static void size(int *w, int *h) { *w = actual_width; *h = actual_height; }
static void stop(void) { ++stops; }
refexport_t re = {prepare, init, size, stop};
viddef_t viddef;
int main(void) {
    int w, h;
    assert(GLimp_Init());
    assert(!GLimp_InitGraphics(1, NULL, &h) && starts == 0);
    for (int mode = 0; mode < 2; ++mode) {
        actual_width = mode ? 3840 : 1920;
        actual_height = mode ? 2160 : 1080;
        assert(GLimp_InitGraphics(1, &w, &h));
        assert(w == actual_width && h == actual_height);
        assert(viddef.width == w && viddef.height == h);
        int count = starts;
        assert(GLimp_InitGraphics(1, &w, &h) && starts == count);
        assert(GLimp_GetDesktopMode(&w, &h));
        assert(w == actual_width && h == actual_height);
        GLimp_ShutdownGraphics();
    }
    actual_width = 0;
    assert(!GLimp_InitGraphics(1, &w, &h) && stops == 3);
    GLimp_ShutdownGraphics();
    assert(stops == 3);
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
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(source), '-o', str(output)], check=True)
    subprocess.run([str(output)], check=True)
print('PASS: actual drawable size reaches engine at 1080p/4K; repeat init and failures remain bounded')
