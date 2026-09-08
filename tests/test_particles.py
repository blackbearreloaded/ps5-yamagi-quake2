#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Render the actual native particle shaders on a surfaceless host GL context."""
import ctypes as C
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
relative = Path('src/client/refresh/gl3/gl3_shaders.c')
with tempfile.TemporaryDirectory() as folder:
    temp = Path(folder)
    path = temp / relative
    path.parent.mkdir(parents=True)
    path.write_bytes((root / 'upstream/yquake2' / relative).read_bytes())
    path.chmod(0o644)
    subprocess.run(['git', 'apply', f'--include={relative.as_posix()}',
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=temp, check=True)
    source = path.read_text()
    names = ('vertexCommon3D', 'fragmentCommon3D', 'vertexSrcParticles',
             'fragmentSrcParticles', 'fragmentSrcParticlesSquare')
    declarations = []
    for name in names:
        start = source.index('static const char* ' + name + ' =')
        end = re.search(r'\n\s*\);', source[start:]).end() + start
        declarations.append(source[start:end])
    emitter = '#include <stdio.h>\n#define YQ2_PS5 1\n#define MULTILINE_STRING(...) #__VA_ARGS__\n'
    emitter += '\n'.join(declarations)
    emitter += '\nint main(int argc,char **argv) { puts("#version 330 core");'
    emitter += 'if(argv[1][0]==\'v\') {puts(vertexCommon3D);puts(vertexSrcParticles);}'
    emitter += 'else {puts(fragmentCommon3D);puts(argv[1][0]==\'r\' ? fragmentSrcParticles : fragmentSrcParticlesSquare);} }'
    (temp / 'emit.c').write_text(emitter)
    subprocess.run(['cc', str(temp / 'emit.c'), '-o', str(temp / 'emit')], check=True)
    sources = {kind: subprocess.check_output([str(temp / 'emit'), kind]) for kind in ('v','r','s')}
    for kind, data in sources.items():
        shader = temp / (kind + ('.vert' if kind == 'v' else '.frag'))
        shader.write_bytes(data)
        subprocess.run(['glslangValidator', str(shader)], check=True)

    egl = C.CDLL('libEGL.so.1')
    egl.eglGetProcAddress.restype = C.c_void_p
    egl.eglGetProcAddress.argtypes = [C.c_char_p]
    def proc(name, restype, *args):
        address = egl.eglGetProcAddress(name.encode())
        assert address, name
        return C.CFUNCTYPE(restype, *args)(address)
    I, U, F, P = C.c_int, C.c_uint, C.c_float, C.c_void_p
    ints = lambda *values: (I * len(values))(*values)
    display = proc('eglGetPlatformDisplayEXT', P, U, P, P)(0x31dd, None, None)
    assert display
    assert proc('eglInitialize', U, P, P, P)(display, None, None)
    surface = context = None
    try:
        assert proc('eglBindAPI', U, U)(0x30a2)
        config, count = P(), I()
        attrs = ints(0x3033,1,0x3040,8,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038)
        assert proc('eglChooseConfig', U, P, P, P, I, P)(display,attrs,C.byref(config),1,C.byref(count)) and count.value
        surface = proc('eglCreatePbufferSurface', P, P, P, P)(display,config,ints(0x3057,64,0x3056,64,0x3038))
        context = proc('eglCreateContext', P, P, P, P, P)(display,config,None,ints(0x3098,3,0x30fb,3,0x30fd,1,0x3038))
        assert surface and context
        assert proc('eglMakeCurrent', U, P, P, P, P)(display,surface,surface,context)
        def shader(kind, data):
            handle = proc('glCreateShader', U, U)(kind)
            text = C.c_char_p(data)
            proc('glShaderSource', None, U, I, P, P)(handle,1,C.byref(text),None)
            proc('glCompileShader', None, U)(handle)
            status = I()
            proc('glGetShaderiv', None, U, U, P)(handle,0x8b81,C.byref(status))
            assert status.value, data
            return handle
        genbuf = proc('glGenBuffers', None, I, P)
        bindbuf = proc('glBindBuffer', None, U, U)
        upload = proc('glBufferData', None, U, C.c_ssize_t, P, U)
        draw = proc('glDrawArraysInstanced', None, U, I, I, I)
        pixels = (C.c_ubyte * (64*64*4))()
        def pixel(x,y): return tuple(pixels[(y*64+x)*4:(y*64+x+1)*4])
        vao = U()
        proc('glGenVertexArrays', None, I, P)(1,C.byref(vao))
        proc('glBindVertexArray', None, U)(vao)
        data = (F*18)(-0.5,0,0,8,10,1,0,0,1, 0.5,0,0,8,10,0,1,0,1)
        vbo = U(); genbuf(1,C.byref(vbo)); bindbuf(0x8892,vbo); upload(0x8892,C.sizeof(data),data,0x88e4)
        for location, components, offset in ((0,3,0),(1,2,12),(2,4,20)):
            proc('glEnableVertexAttribArray', None, U)(location)
            proc('glVertexAttribPointer', None, U, I, U, U, I, P)(location,components,0x1406,0,36,P(offset))
            proc('glVertexAttribDivisor', None, U, U)(location,1)
        for mode in ('r','s'):
            program = proc('glCreateProgram', U)()
            for kind, text in ((0x8b31,sources['v']),(0x8b30,sources[mode])):
                proc('glAttachShader', None, U, U)(program,shader(kind,text))
            for index, name in enumerate((b'position',b'texCoord',b'vertColor')):
                proc('glBindAttribLocation', None, U, U, C.c_char_p)(program,index,name)
            proc('glLinkProgram', None, U)(program)
            status = I(); proc('glGetProgramiv', None, U, U, P)(program,0x8b82,C.byref(status)); assert status.value
            proc('glUseProgram', None, U)(program)
            common = (F*8)(1,1,1,0,1,1,1,1)
            matrices = (F*40)()
            for base in (0,16):
                for i in (0,5,10,15): matrices[base+i]=1
            matrices[34]=1; matrices[35]=1; matrices[36]=1.2; matrices[37]=1
            for binding,name,values in ((0,b'uniCommon',common),(1,b'uni3D',matrices)):
                block = proc('glGetUniformBlockIndex', U, U, C.c_char_p)(program,name)
                assert block != 0xffffffff
                proc('glUniformBlockBinding', None, U, U, U)(program,block,binding)
                buffer = U(); genbuf(1,C.byref(buffer)); bindbuf(0x8a11,buffer)
                upload(0x8a11,C.sizeof(values),values,0x88e4)
                proc('glBindBufferBase', None, U, U, U)(0x8a11,binding,buffer)
            location = proc('glGetUniformLocation', I, U, C.c_char_p)(program,b'particleViewport')
            assert location >= 0
            proc('glUniform2f', None, I, F, F)(location,64,64)
            proc('glViewport', None, I,I,I,I)(0,0,64,64)
            proc('glClearColor', None,F,F,F,F)(0,0,0,0)
            proc('glClear', None,U)(0x4000)
            draw(4,0,6,2)
            proc('glReadPixels',None,I,I,I,I,U,U,P)(0,0,64,64,0x1908,0x1401,pixels)
            assert pixel(16,32)==(255,0,0,255), pixel(16,32)
            assert pixel(48,32)==(0,255,0,255), pixel(48,32)
            assert pixel(11,32)==(0,0,0,0)
            if mode == 'r':
                assert pixel(12,28)==(0,0,0,0)
                assert 60 <= pixel(19,32)[3] <= 72, pixel(19,32)
            else:
                assert pixel(12,28)==(255,0,0,255), pixel(12,28)
            data[2]=2
            bindbuf(0x8892,vbo); upload(0x8892,C.sizeof(data),data,0x88e4)
            proc('glClear',None,U)(0x4000); draw(4,0,6,2)
            proc('glReadPixels',None,I,I,I,I,U,U,P)(0,0,64,64,0x1908,0x1401,pixels)
            assert pixel(16,32)==(0,0,0,0) and pixel(48,32)==(0,255,0,255)
            data[2]=0; upload(0x8892,C.sizeof(data),data,0x88e4)
            assert proc('glGetError',U)()==0
        print('PASS: actual particle shaders compile/link/render; two instances, size, color, round fade and square mode')
    finally:
        proc('eglMakeCurrent',U,P,P,P,P)(display,None,None,None)
        if context: proc('eglDestroyContext',U,P,P)(display,context)
        if surface: proc('eglDestroySurface',U,P,P)(display,surface)
        proc('eglTerminate',U,P)(display)
