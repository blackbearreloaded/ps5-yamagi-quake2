#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Run actual inline-model batching and desktop fallback against the same faces."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
name = 'src/client/refresh/gl3/gl3_surf.c'
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder)
    path = work / name
    path.parent.mkdir(parents=True)
    path.write_bytes((root / 'upstream/yquake2' / name).read_bytes())
    subprocess.run(['git', 'apply', '--include='+name,
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=work, check=True)
    source = path.read_text()
    def function(name):
        start = source.index(name + '(')
        return source[start:source.index('\n}', start)+2]
    batches = source[source.index('typedef struct {\n\tmsurface_t *surface;'):source.index('/* Merge only adjacent')]
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define ARRLEN(a) (sizeof(a)/sizeof((a)[0]))
#define DotProduct(a,b) ((a)[0]*(b)[0]+(a)[1]*(b)[1]+(a)[2]*(b)[2])
#define BACKFACE_EPSILON .01f
typedef bool qboolean;
typedef unsigned GLuint;
enum { SURF_DRAWTURB=1, SURF_FLOWING=2, SURF_TRANS33=4, SURF_TRANS66=8,
       SURF_SKY=16, SURF_WARP=32, SURF_PLANEBACK=64, RF_TRANSLUCENT=128, GL_BLEND=1 };
typedef struct { float attributes[9]; unsigned lightFlags; } gl3_3D_vtx_t;
typedef struct { GLuint texnum; } gl3image_t;
typedef struct { int flags; gl3image_t *image; } texinfo_t;
typedef struct { int numverts; gl3_3D_vtx_t vertices[4]; } glpoly_t;
typedef struct { float normal[3], dist; } cplane_t;
typedef struct surface { int flags, lightmaptexturenum; unsigned char styles[4];
    texinfo_t *texinfo; glpoly_t *polys; cplane_t *plane; struct surface *texturechain;
} msurface_t;
typedef struct { unsigned flags; int frame; } entity_t;
typedef struct { msurface_t *surfaces; int firstmodelsurface, nummodelsurfaces, *nodes, firstnode; } gl3model_t;
typedef int dlight_t;
static struct { dlight_t dlights[1]; int num_dlights; } r_newrefdef = {{1},1};
static float modelorg[3];
static int r_dlightframecount=7, marks, c_brush_polys, draws, blend, blend_calls;
static msurface_t *gl3_alpha_surfaces;
static unsigned seen[700], sequence[700], count;
static void GL3_MarkSurfaceLights(void) {}
static void R_MarkLights(dlight_t *lt,int mask,int *node,int frame,void (*callback)(void)) {
    assert(lt == r_newrefdef.dlights && mask == 1 && *node == 23 && frame == 7);
    assert(callback == GL3_MarkSurfaceLights); ++marks;
}
static void glEnable(int what) { assert(what == GL_BLEND && !blend); blend=1; ++blend_calls; }
static void glDisable(int what) { assert(what == GL_BLEND && blend); blend=0; }
static gl3image_t *R_TextureAnimation(entity_t *e,texinfo_t *info) {
    assert(e && e->frame == 17); return info->image;
}
static void SetLightFlags(msurface_t *s) {
    for(int i=0;i<s->polys->numverts;++i) s->polys->vertices[i].lightFlags=1;
}
static void SetAllLightFlags(msurface_t *s) {
    for(int i=0;i<s->polys->numverts;++i) s->polys->vertices[i].lightFlags=~0u;
}
static void face(unsigned id) {
    assert(id < 700 && !seen[id]++ && count < 700); sequence[count++]=id;
}
static void RenderLightmappedPoly(entity_t *e,msurface_t *s) {
    assert(blend == !!(e->flags & RF_TRANSLUCENT) && !(s->flags & SURF_DRAWTURB));
    for(int i=0;i<4;++i) assert(s->polys->vertices[i].lightFlags == ~0u);
    face((unsigned)s->polys->vertices[0].attributes[0]); ++draws; ++c_brush_polys;
}
static void RenderBrushPoly(entity_t *e,msurface_t *s,const gl3_3D_vtx_t *v,int n) {
    assert(blend == !!(e->flags & RF_TRANSLUCENT));
    if (!v) {
        assert(s->flags & SURF_DRAWTURB); face((unsigned)s->polys->vertices[0].attributes[0]);
    } else {
        assert(!blend && n > 0 && n <= 4095 && n%6 == 0);
        const unsigned corners[]={0,1,2,0,2,3};
        for(int k=0;k<n;k+=6) {
            unsigned id=(unsigned)v[k].attributes[0]; face(id);
            for(int j=0;j<6;++j) {
                assert(v[k+j].attributes[0] == id && v[k+j].attributes[1] == corners[j]);
                for(int a=2;a<9;++a) assert(v[k+j].attributes[a] == (float)(id*100+corners[j]*10+a));
                assert(v[k+j].lightFlags == ~0u);
            }
        }
    }
    ++draws; ++c_brush_polys;
}
''' + '\n#ifdef YQ2_PS5\n' + batches + '\nstatic qboolean\n' + function('BatchTextureChain') + '\n#endif\nstatic void\n' + function('DrawInlineBModel') + r'''
int main(void) {
    static msurface_t surfaces[704]; static glpoly_t polys[704];
    cplane_t front={{1,0,0},-1}, back={{1,0,0},1};
    gl3image_t images[]={{1},{2}};
    texinfo_t textures[]={{0,&images[0]},{0,&images[1]},
                         {SURF_FLOWING,&images[0]},{SURF_TRANS33,&images[0]}};
    entity_t entity={0,17}; int node=23;
    gl3model_t model={surfaces,2,700,&node,0};
    for(int scenario=0;scenario<5;++scenario) {
        memset(seen,0,sizeof(seen)); count=draws=c_brush_polys=marks=blend_calls=0;
        for(unsigned i=0;i<704;++i) {
            polys[i].numverts=4;
            surfaces[i]=(msurface_t){.polys=&polys[i],.plane=&front,
                .texinfo=&textures[scenario == 1 ? i%2 : 0]};
            for(unsigned j=0;j<4;++j) {
                unsigned id=i>=2 ? i-2 : 999;
                polys[i].vertices[j].attributes[0]=(float)id;
                polys[i].vertices[j].attributes[1]=(float)j;
                for(int a=2;a<9;++a) polys[i].vertices[j].attributes[a]=(float)(id*100+j*10+a);
                polys[i].vertices[j].lightFlags=0x123;
            }
        }
        if (scenario == 2 || scenario == 3) {
            surfaces[52].texinfo=&textures[2]; /* Flowing face retains its position. */
            surfaces[102].flags=SURF_DRAWTURB;
            surfaces[152].texinfo=&textures[3]; /* Alpha chain must remain separate. */
            surfaces[202].plane=&back; surfaces[203].flags=SURF_PLANEBACK;
            surfaces[204].flags=SURF_PLANEBACK; surfaces[204].plane=&back;
        }
        entity.flags=scenario == 3 ? RF_TRANSLUCENT : 0;
        model.nummodelsurfaces=scenario == 4 ? 0 : 700;
        msurface_t sentinel={0}; gl3_alpha_surfaces=&sentinel;
        DrawInlineBModel(&entity,&model);
        unsigned expected=scenario == 4 ? 0 : scenario >= 2 ? 697 : 700;
        assert(count == expected && (unsigned)c_brush_polys == expected && marks == 1 && !blend);
        assert(blend_calls == (scenario == 3));
        for(unsigned i=0;i<700;++i)
            assert(seen[i] == (scenario == 4 ? 0u : scenario >= 2 && (i==150 || i==200 || i==201) ? 0u : 1u));
        if (scenario == 2 || scenario == 3) {
            assert(gl3_alpha_surfaces == &surfaces[152] && surfaces[152].texturechain == &sentinel);
            for(unsigned i=0;i<50;++i) assert(sequence[i] < 50);
            assert(sequence[50] == 50 && sequence[100] == 100);
        } else assert(gl3_alpha_surfaces == &sentinel);
#ifdef YQ2_PS5
        if (scenario < 2) assert(draws == 2);
        if (scenario == 3) assert((unsigned)draws == expected);
#else
        assert((unsigned)draws == expected);
#endif
    }
    puts("PASS: inline brush batches preserve all faces/attributes, full dynamic-light flags, culling, alpha/flow/water order and translucent fallback");
}
'''
    (work / 'brush.c').write_text(harness)
    for native in (False, True):
        flags = ['-DYQ2_PS5'] if native else []
        executable = str(work / ('brush-native' if native else 'brush-desktop'))
        subprocess.run([shutil.which('clang-18') or 'cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', '-fsanitize=address,undefined', *flags,
                        str(work / 'brush.c'), '-o', executable], check=True)
        subprocess.run([executable], check=True)
