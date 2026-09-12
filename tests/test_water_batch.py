#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compare actual native and desktop water draws against the ordered fan mesh."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
name = 'src/client/refresh/gl3/gl3_warp.c'
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder)
    source = work / name
    source.parent.mkdir(parents=True)
    source.write_bytes((root / 'upstream/yquake2' / name).read_bytes())
    subprocess.run(['git', 'apply', '--include=' + name,
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=work, check=True)
    code = source.read_text()
    start = code.index('static void\nEmitWaterPolys(')
    function = code[start:code.index('// ########### below: Sky-specific stuff', start)]
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define ARRLEN(a) (sizeof(a)/sizeof((a)[0]))
typedef bool qboolean;
typedef struct { float attributes[9]; unsigned lightFlags; } gl3_3D_vtx_t;
typedef struct poly { struct poly *next; int numverts; gl3_3D_vtx_t vertices[1400]; } glpoly_t;
typedef struct { bool is_lava; } image_t;
typedef struct { unsigned flags; image_t *image; } texinfo_t;
typedef struct surface { glpoly_t *polys; texinfo_t *texinfo; struct surface *texturechain; unsigned flags; } msurface_t;
enum { SURF_FLOWING=1, GL_TRIANGLES=2, GL_TRIANGLE_FAN=3, SURF_DRAWTURB=4 };
#ifdef YQ2_PS5
static int c_brush_polys;
#endif
static struct { float time; } r_newrefdef;
static struct {
 struct { float scroll, lightScaleForTurb; } uni3DData;
 struct { int shaderProgram; } si3Dturb;
 int vao3D, vbo3D;
} gl3state;
static gl3_3D_vtx_t expected[40000];
static unsigned emitted, draws, expected_count;
static void GL3_UpdateUBO3D(void) {}
static void GL3_UseProgram(int x) { (void)x; }
static void GL3_BindVAO(int x) { (void)x; }
static void GL3_BindVBO(int x) { (void)x; }
static void vertex(const gl3_3D_vtx_t *v) {
 assert(emitted < expected_count);
 assert(memcmp(v, &expected[emitted++], sizeof(*v)) == 0);
}
static void GL3_BufferAndDraw3D(const gl3_3D_vtx_t *v, int n, int mode) {
 ++draws;
#ifdef YQ2_PS5
 assert(mode == GL_TRIANGLES && n > 0 && n <= 4095 && n % 3 == 0);
 for (int i=0; i<n; ++i) vertex(&v[i]);
#else
 assert(mode == GL_TRIANGLE_FAN);
 for (int i=2; i<n; ++i) { vertex(&v[0]); vertex(&v[i-1]); vertex(&v[i]); }
#endif
}
''' + '\n' + function + r'''
int main(void) {
 static glpoly_t polys[200];
 image_t image={0}; texinfo_t info={0,&image}; msurface_t surface={.texinfo=&info};
 const unsigned sizes[]={0,1,2,3,4,64,1367,1400};
 for (unsigned scenario=0; scenario<ARRLEN(sizes); ++scenario) {
  unsigned count=scenario<4 ? 1 : scenario==5 ? 200 : 2;
  expected_count=emitted=draws=0;
  for (unsigned p=0; p<count; ++p) {
   polys[p].numverts=sizes[scenario]; polys[p].next=p+1<count ? &polys[p+1] : NULL;
   for (unsigned v=0; v<sizes[scenario]; ++v) {
    for (unsigned a=0; a<9; ++a) polys[p].vertices[v].attributes[a]=(float)(p*10000+v*10+a);
    polys[p].vertices[v].lightFlags=0xff000000u+p*1400+v;
   }
   for (int i=2; i<polys[p].numverts; ++i) {
    expected[expected_count++]=polys[p].vertices[0];
    expected[expected_count++]=polys[p].vertices[i-1];
    expected[expected_count++]=polys[p].vertices[i];
   }
  }
  for (unsigned flowing=0; flowing<2; ++flowing) for (unsigned lava=0; lava<2; ++lava) {
   emitted=draws=0; info.flags=flowing; image.is_lava=lava; r_newrefdef.time=3;
   surface.polys=polys; GL3_EmitWaterPolys(&surface);
   assert(emitted == expected_count);
#ifdef YQ2_PS5
   assert(draws == (expected_count+4094)/4095);
#else
   assert(draws == count);
#endif
   assert(gl3state.uni3DData.scroll == (flowing ? -32 : 0));
   assert(gl3state.uni3DData.lightScaleForTurb == (lava ? 1 : 0.5f));
  }
 }
 surface.polys=NULL; emitted=draws=expected_count=0; GL3_EmitWaterPolys(&surface);
 assert(draws == 0);
#ifdef YQ2_PS5
 /* Different faces and subdivisions must retain every vertex in BSP order.
  * Runs stop on texture, flags (including transparency/flow), or surface kind. */
 static msurface_t faces[200];
 image_t other_image={1}; texinfo_t other_info=info;
 for (unsigned boundary=0; boundary<5; ++boundary) {
  expected_count=emitted=draws=0; c_brush_polys=0;
  info.flags=0; image.is_lava=false; other_info=info;
  for (unsigned p=0; p<200; ++p) {
   polys[p].numverts=10; polys[p].next=NULL;
   faces[p]=(msurface_t){&polys[p], &info, p<199 ? &faces[p+1] : NULL, SURF_DRAWTURB};
   for (unsigned v=0; v<10; ++v) {
    for (unsigned a=0; a<9; ++a) polys[p].vertices[v].attributes[a]=(float)(p*10000+v*10+a);
    polys[p].vertices[v].lightFlags=p*10+v;
   }
  }
  unsigned count=boundary ? 100 : 200;
  if (boundary==1) { other_info.image=&other_image; faces[count].texinfo=&other_info; }
  if (boundary==2) { other_info.flags=SURF_FLOWING; faces[count].texinfo=&other_info; }
  if (boundary==3) faces[count].flags=0;
  if (boundary==4) { other_info.flags=8; faces[count].texinfo=&other_info; }
  for (unsigned p=0; p<count; ++p) for (int i=2; i<10; ++i) {
   expected[expected_count++]=polys[p].vertices[0];
   expected[expected_count++]=polys[p].vertices[i-1];
   expected[expected_count++]=polys[p].vertices[i];
  }
  assert(GL3_EmitWaterChain(faces) == &faces[count-1]);
  assert(c_brush_polys == (int)count-1);
  assert(emitted == expected_count && draws == (expected_count+4094)/4095);
  assert(gl3state.uni3DData.scroll==0 && gl3state.uni3DData.lightScaleForTurb==0.5f);
  /* The original single-surface entry must not follow the alpha chain. */
  emitted=draws=0; expected_count=24; GL3_EmitWaterPolys(faces);
  assert(emitted==expected_count && draws==1);
 }
#endif
 puts("PASS: water batching preserves every vertex, triangle order, flow/light state and bounded draws");
}
'''
    (work / 'water.c').write_text(harness)
    for flags in ([], ['-DYQ2_PS5']):
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', *flags, str(work / 'water.c'),
                        '-o', str(work / 'water')], check=True)
        subprocess.run([str(work / 'water')], check=True)
