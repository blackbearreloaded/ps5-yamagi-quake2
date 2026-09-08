#!/usr/bin/env python3
"""Check the actual native triangulation, UI quad and texture quality switch."""
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
paths = [f'src/client/refresh/gl3/gl3_{name}.c' for name in ('main', 'draw', 'image', 'surf')]
with tempfile.TemporaryDirectory() as folder:
    for path in paths:
        target = Path(folder) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / 'upstream/yquake2' / path, target)
        target.chmod(0o644)
    subprocess.run(['git', 'apply', *['--include=' + p for p in paths],
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=folder, check=True)
    main, draw, image, surf = [(Path(folder) / p).read_text() for p in paths]

def function(source, name):
    start = source.index(name + '(')
    return source[start:source.index('\n}', start) + 2]

# The earlier comment mentions this function too; start at its definition.
main = main[main.index('void\nGL3_BufferAndDraw3D'):]
code = r'''
#define YQ2_PS5 1
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>
typedef unsigned GLenum, GLbitfield;
typedef unsigned GLuint;
typedef float GLfloat;
typedef unsigned char byte;
typedef int qboolean;
#define false 0
#define true 1
#define ARRLEN(a) (sizeof(a)/sizeof((a)[0]))
enum { GL_TRIANGLES, GL_TRIANGLE_FAN, GL_TRIANGLE_STRIP, GL_ARRAY_BUFFER,
 GL_STREAM_DRAW, GL_MAP_WRITE_BIT=8, GL_MAP_INVALIDATE_RANGE_BIT=16,
 GL_MAP_UNSYNCHRONIZED_BIT=32, GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL,
 GL_RGBA, GL_UNSIGNED_BYTE, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
 GL_TEXTURE_MAX_ANISOTROPY_EXT, CVAR_ARCHIVE };
#define Q_max(a,b) ((a) > (b) ? (a) : (b))
typedef struct { float attributes[9]; unsigned lightFlags; } gl3_3D_vtx_t;
static struct { int useBigVBO, anisotropic; } gl3config;
static struct { int vbo3Dsize, vbo3DcurOffset; } gl3state;
static int vao2D, vbo2D;
#define GL3_BindVAO(x) ((void)(x))
#define GL3_BindVBO(x) ((void)(x))
static unsigned char uploaded[sizeof(gl3_3D_vtx_t)*192];
static size_t uploaded_size;
static unsigned draw_count, vertices;
static gl3_3D_vtx_t original[132];
static int test_mode, ui;
static void glBufferData(int target, size_t size, const void *data, int usage) {
 assert(target == GL_ARRAY_BUFFER && size <= sizeof(uploaded));
 memcpy(uploaded, data, size); uploaded_size=size;
}
static void glDrawArrays(GLenum mode, int first, int count) {
 assert(mode == GL_TRIANGLES && first == 0 && count > 0 && count%3 == 0);
 if (ui) {
  const float expected[] = {10,60,0,1, 10,20,0,0, 40,60,1,1,
                            40,60,1,1, 10,20,0,0, 40,20,1,0};
  assert(count==6 && uploaded_size==sizeof(expected));
  assert(memcmp(uploaded,expected,sizeof(expected))==0);
 } else {
  assert(uploaded_size==(size_t)count*sizeof(gl3_3D_vtx_t));
  for (int k=0;k<count;++k) {
   int i=(vertices+k)/3+2, corner=(vertices+k)%3;
   int a=test_mode==GL_TRIANGLE_FAN ? 0 : i-2+(i&1);
   int b=test_mode==GL_TRIANGLE_FAN ? i-1 : i-1-(i&1);
   int index=corner==0 ? a : corner==1 ? b : i;
   assert(memcmp(uploaded+k*sizeof(gl3_3D_vtx_t), &original[index], sizeof(original[0]))==0);
  }
 }
 vertices+=count; ++draw_count;
}
static void *glMapBufferRange(int target,int offset,int size,GLbitfield flags) { assert(0); return NULL; }
static void glUnmapBuffer(int target) { assert(0); }
static int gl3_tex_solid_format=GL_RGBA, gl3_tex_alpha_format=GL_RGBA;
static int gl3_solid_format=3, gl3_alpha_format=4, gl_filter_min=99, gl_filter_max=98;
static struct cvar { float value; } quality, anisotropy, *gl_anisotropic=&anisotropy;
static struct cvar *getvar(const char *name,const char *def,int flags) {
 assert(strcmp(name,"gl3_mipmaps")==0 && strcmp(def,"0")==0); return &quality;
}
static struct { struct cvar *(*Cvar_Get)(const char *,const char *,int); } ri={getvar};
static int max_level, generated, uploads;
static void glTexParameteri(int target,int name,int value) {
 if(name==GL_TEXTURE_MAX_LEVEL) max_level=value;
}
static void glTexImage2D(int t,int level,int comp,int w,int h,int border,int fmt,int type,const void *data) {
 assert(level==0 && comp==GL_RGBA && fmt==GL_RGBA && type==GL_UNSIGNED_BYTE); ++uploads;
}
static void glGenerateMipmap(int target) { ++generated; }
typedef int entity_t;
typedef struct { GLuint texnum; } gl3image_t;
typedef struct { int flags; gl3image_t *image; } texinfo_t;
typedef struct { int numverts; gl3_3D_vtx_t vertices[5]; } glpoly_t;
typedef struct surface {
 int flags, lightmaptexturenum;
 byte styles[4];
 texinfo_t *texinfo;
 glpoly_t *polys;
 struct surface *texturechain;
} msurface_t;
enum { SURF_DRAWTURB=1, SURF_FLOWING=2, SURF_TRANS33=4, SURF_TRANS66=8, SURF_SKY=16, SURF_WARP=32 };
static int c_brush_polys, surface_draws, surface_vertices;
static gl3image_t *R_TextureAnimation(entity_t *entity, texinfo_t *info) { return info->image; }
static void SetLightFlags(msurface_t *s) {
 for(int i=0;i<s->polys->numverts;++i) s->polys->vertices[i].lightFlags=(unsigned)s->polys->vertices[i].attributes[0];
}
static void RenderBrushPoly(entity_t *entity,msurface_t *s,const gl3_3D_vtx_t *v,int count) {
 assert(count>0 && count<=4095 && count%3==0);
 int k=0;
 for(;k<count;s=s->texturechain) {
  assert(s && !(s->flags&SURF_DRAWTURB));
  for(int i=2;i<s->polys->numverts;++i) {
   assert(memcmp(&v[k++],&s->polys->vertices[0],sizeof(v[0]))==0);
   assert(memcmp(&v[k++],&s->polys->vertices[i-1],sizeof(v[0]))==0);
   assert(memcmp(&v[k++],&s->polys->vertices[i],sizeof(v[0]))==0);
  }
 }
 assert(k==count); ++c_brush_polys; ++surface_draws; surface_vertices+=count;
}
''' + '\nvoid\n' + function(main, 'GL3_BufferAndDraw3D') + '\nstatic void\n' + function(draw, 'drawTexturedRectangle') + '\nstatic qboolean\n' + function(image, 'GL3_Upload32') + '\n' + surf[surf.index('typedef struct {\n\tmsurface_t *surface;'):surf.index('/* Merge only adjacent')] + '\nstatic qboolean\n' + function(surf, 'BatchTextureChain') + r'''
int main(void) {
 for(unsigned i=0;i<ARRLEN(original);++i) {
  for(unsigned j=0;j<9;++j) original[i].attributes[j]=(float)(i*10+j);
  original[i].lightFlags=0xff000000u+i;
 }
 for(test_mode=GL_TRIANGLE_FAN;test_mode<=GL_TRIANGLE_STRIP;++test_mode)
  for(int n=0;n<=132;++n) {
   vertices=draw_count=0;
   GL3_BufferAndDraw3D(original,n,test_mode);
   unsigned expected=n<3 ? 0 : (n-2)*3;
   assert(vertices==expected && draw_count==(expected+191)/192);
  }
 ui=1; drawTexturedRectangle(10,20,30,40,0,0,1,1);
 unsigned pixels[]={0xffffffffu,0x00ffffffu};
 quality.value=0; max_level=-1; generated=uploads=0;
 assert(GL3_Upload32(pixels,2,1,1)==1);
 assert(max_level==0 && generated==0 && uploads==1);
 quality.value=1; max_level=-1; generated=uploads=0;
 assert(GL3_Upload32(pixels,1,1,1)==0);
 assert(max_level==-1 && generated==1 && uploads==1);
 static msurface_t surfaces[700]; static glpoly_t polygons[700];
 gl3image_t images[2]={{1},{2}};
 texinfo_t info[2]={{0,&images[0]},{0,&images[0]}};
 for(int i=0;i<700;++i) {
  polygons[i].numverts=4;
  for(int j=0;j<4;++j) polygons[i].vertices[j]=original[(i+j)%132];
  surfaces[i].polys=&polygons[i]; surfaces[i].texinfo=&info[0];
  surfaces[i].texturechain=i==699 ? NULL : &surfaces[i+1];
 }
 for(msurface_t *s=surfaces;s;s=s->texturechain) assert(BatchTextureChain(NULL,&s));
 assert(surface_draws==2 && c_brush_polys==700 && surface_vertices==4200);
 surfaces[1].texinfo=&info[1];
 for(int boundary=0;boundary<5;++boundary) {
  surfaces[1].lightmaptexturenum=0; surfaces[1].styles[0]=0;
  info[1].flags=0; info[1].image=&images[0]; surfaces[1].flags=0;
  if(boundary==0) surfaces[1].lightmaptexturenum=1;
  if(boundary==1) surfaces[1].styles[0]=1;
  if(boundary==2) info[1].flags=SURF_FLOWING;
  if(boundary==3) info[1].image=&images[1];
  if(boundary==4) surfaces[1].flags=SURF_DRAWTURB;
  msurface_t *s=surfaces; int before=surface_vertices;
  assert(BatchTextureChain(NULL,&s) && s==surfaces && surface_vertices==before+6);
 }
 msurface_t *s=surfaces;
 info[0].flags=SURF_TRANS33; assert(!BatchTextureChain(NULL,&s) && s==surfaces);
 info[0].flags=0; polygons[0].numverts=2000; assert(!BatchTextureChain(NULL,&s));
 for(int i=0;i<700;++i) {
  surfaces[i].flags=0; surfaces[i].texinfo=&info[0]; polygons[i].numverts=4;
  surfaces[i].lightmaptexturenum=i%3; surfaces[i].styles[0]=i%2;
  surfaces[i].texturechain=i==699 ? NULL : &surfaces[i+1];
 }
 s=surfaces; SortTextureChain(NULL,&s);
 unsigned seen[700]={0}; int previous[6]={-1,-1,-1,-1,-1,-1};
 for(msurface_t *p=s;p;p=p->texturechain) {
  int index=(int)(p-surfaces), key=p->lightmaptexturenum*2+p->styles[0];
  assert(index>=0 && index<700 && !seen[index]++ && previous[key]<index);
  previous[key]=index;
 }
 surface_draws=surface_vertices=c_brush_polys=0;
 for(;s;s=s->texturechain) assert(BatchTextureChain(NULL,&s));
 assert(surface_draws==6 && c_brush_polys==700 && surface_vertices==4200);
 for(int i=0;i<700;++i) surfaces[i].texturechain=i==699 ? NULL : &surfaces[i+1];
 surfaces[350].flags=SURF_DRAWTURB; s=surfaces; SortTextureChain(NULL,&s);
 int order=0;
 for(;s;s=s->texturechain,++order) {
  if(order<350) assert(s<surfaces+350);
  else if(order==350) assert(s==surfaces+350);
  else assert(s>surfaces+350);
 }
 assert(order==700);
 static msurface_t large[1100]; unsigned large_seen[1100]={0};
 for(int i=0;i<1100;++i) {
  large[i]=surfaces[0]; large[i].lightmaptexturenum=i%3; large[i].styles[0]=i%2;
  large[i].texturechain=i==1099 ? NULL : &large[i+1];
 }
 s=large; SortTextureChain(NULL,&s); order=0;
 for(;s;s=s->texturechain,++order) {
  int index=(int)(s-large); assert(index>=0 && index<1100 && !large_seen[index]++);
  assert((order<1024)==(index<1024));
 }
 assert(order==1100);
 puts("PASS: fan/strip winding and attributes, bounded chunks, UI quad, optional mipmaps");
 puts("PASS: 700 world faces in two bounded batches; material, lighting and special-surface boundaries");
 puts("PASS: interleaved materials become six draws; stable order, no lost faces, water ordering retained");
}
'''
with tempfile.TemporaryDirectory() as folder:
    source = Path(folder) / 'triangles.c'
    executable = Path(folder) / 'triangles'
    source.write_text(code)
    subprocess.run([shutil.which('clang-18') or 'cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-parameter', '-Wno-sign-compare', '-fsanitize=address,undefined',
                    str(source), '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
