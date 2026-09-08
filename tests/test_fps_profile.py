#!/usr/bin/env python3
"""Check the actual native FPS overlay and per-call timing wrappers offline."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
relative = Path('src/client/cl_screen.c')
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)
    source = path / relative
    source.parent.mkdir(parents=True)
    source.write_bytes((root / 'upstream/yquake2' / relative).read_bytes())
    source.chmod(0o644)
    subprocess.run(['git', 'apply', f'--include={relative.as_posix()}',
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=folder, check=True)
    screen = source.read_text()
    body = screen.split('SCR_Framecounter(void)\n{\n#ifdef YQ2_PS5\n', 1)[1].split('#else', 1)[0]
    assert screen.index('SCR_Framecounter();') < screen.rindex('R_EndFrame();')
    gl3 = (root / 'src/ps5/ps5_gl3.c').read_text()
    profile = gl3[gl3.index('static struct {'):gl3.index('#define PS5_REQUIRED_GL_FUNCTIONS')]
    harness = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <glad/glad.h>
static long long clock_us = 1;
static long long Sys_Microseconds(void) { return clock_us; }
static struct { float value; } enabled = {1}, *cl_showfps = &enabled;
static float SCR_GetConsoleScale(void) { return 2; }
#define CHAR_SIZE 8
static char label[32];
static void DrawStringScaled(int x, int y, const char *text, float scale) {
    assert(x == 16 && y == 16 && scale == 2);
    snprintf(label, sizeof(label), "%s", text);
}
static void SCR_AddDirtyPoint(int x, int y) { assert(x >= 16 && y >= 16); }
'''
    harness += 'static void overlay(void) {\n' + body + '}\n' + profile
    harness += r'''
static void APIENTRY draw_arrays(GLenum m, GLint f, GLsizei c) { clock_us += 2000; }
static void APIENTRY draw_elements(GLenum m, GLsizei c, GLenum t, const void *p) { clock_us += 3000; }
static void APIENTRY draw_instances(GLenum m, GLint f, GLsizei c, GLsizei n) { clock_us += 6000; }
static const void *uploads[8];
static unsigned upload_count;
static void APIENTRY buffer_data(GLenum t, GLsizeiptr n, const void *p, GLenum u) {
    uploads[upload_count++] = p; clock_us += 4000;
}
static void APIENTRY clear(GLbitfield mask) { clock_us += 5000; }
int main(void) {
    overlay(); assert(!strcmp(label, "FPS: 0.0"));
    clock_us += 250000; overlay();
    clock_us += 250000; overlay(); assert(!strcmp(label, "FPS: 4.0"));
    clock_us += 2000000; overlay(); assert(!strcmp(label, "FPS: 0.5"));
    enabled.value = 0; strcpy(label, "unchanged"); overlay(); assert(!strcmp(label, "unchanged"));
    native_draw_arrays = draw_arrays; native_draw_elements = draw_elements;
    native_buffer_data = buffer_data; native_clear = clear;
    profile_draw_arrays(0,0,3); profile_draw_elements(0,3,0,0);
    profile_buffer_data(0,16,0,0); profile_clear(0);
    assert(profile.draws == 2 && profile.draw_us == 5000);
    assert(profile.buffer_us == 4000 && profile.clear_us == 5000);
    PS5_RenderStage(0);
    for(unsigned i=1;i<=4;++i) { clock_us+=i*100; PS5_RenderStage(i); }
    assert(profile.stage_us[0]==100 && profile.stage_us[1]==200);
    assert(profile.stage_us[2]==300 && profile.stage_us[3]==400);
    profile_frame(1000);
    assert(!profile.draws && !profile.draw_us && !profile.buffer_us && !profile.clear_us);
    for(unsigned i=0;i<4;++i) assert(profile.stage_us[i]==0);
    int vertices[4] = {1,2,3,4};
    upload_count = 0;
    profile_buffer_data(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STREAM_DRAW);
    profile_buffer_data(GL_UNIFORM_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW);
    assert(upload_count == 4 && uploads[0] == NULL && uploads[1] == vertices);
    assert(uploads[2] == NULL && uploads[3] == vertices);
    profile_buffer_data(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    assert(upload_count == 5 && uploads[4] == vertices);
    profile_buffer_data(GL_ARRAY_BUFFER, 0, vertices, GL_STREAM_DRAW);
    assert(upload_count == 6 && uploads[5] == vertices);
    assert(profile.buffer_us == 24000);
    native_draw_arrays_instanced=draw_instances;
    profile_draw_arrays_instanced(GL_TRIANGLES,0,6,25);
    assert(profile.draws==1 && profile.draw_us==6000);
}
'''
    (path / 'test.c').write_text(harness)
    subprocess.run(['clang', '-std=gnu11', '-O2', '-fsanitize=address,undefined',
                    '-I', str(root / 'upstream/yquake2/src/client/refresh/gl3/glad/include'),
                    str(path / 'test.c'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
print('PASS: FPS overlay, timing, streaming uploads orphan before writing, static/empty uploads unchanged')
