#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise the patched video menu and upstream navigation at both native sizes."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
upstream = root / 'upstream/yquake2'
name = 'src/client/menu/videomenu.c'
harness = r'''
#include <assert.h>
#include <strings.h>
viddef_t viddef;
cvar_t *vid_renderer, *vid_fullscreen, *scr_viewsize;
static cvar_t variables[64];
static int variable_count, mode_writes, fullscreen_writes, restarts;
cvar_t *Cvar_Get(const char *name, const char *value, int flags) {
    for (int i = 0; i < variable_count; ++i)
        if (!strcmp(variables[i].name, name)) return &variables[i];
    assert(variable_count < 64);
    cvar_t *v = &variables[variable_count++];
    v->name = (char *)name; v->string = (char *)value;
    v->value = atof(value); v->flags = flags;
    return v;
}
cvar_t *Cvar_Set(const char *name, const char *value) {
    cvar_t *v = Cvar_Get(name, value, 0);
    v->string = (char *)value; v->value = atof(value);
    return v;
}
void Cvar_SetValue(const char *name, float value) {
    mode_writes += !strcmp(name, "r_mode");
    fullscreen_writes += !strcmp(name, "vid_fullscreen");
    Cvar_Get(name, "0", 0)->value = value;
}
const char *Cvar_VariableString(const char *name) { return Cvar_Get(name, "", 0)->string; }
float Cvar_VariableValue(const char *name) { return Cvar_Get(name, "0", 0)->value; }
int Q_stricmp(const char *a, const char *b) { return strcasecmp(a, b); }
qboolean VID_HasRenderer(const char *name) { return !strcmp(name, "gl3"); }
float SCR_GetMenuScale(void) { return 1; }
int Key_GetMenuKey(int key) { return key; }
void M_ForceMenuOff(void) {}
void M_PopMenu(void) {}
void Cbuf_AddText(char *text) { assert(!strcmp(text, "vid_restart\n")); ++restarts; }

int main(void) {
    vid_renderer = Cvar_Get("vid_renderer", "gl3", 0);
    vid_fullscreen = Cvar_Get("vid_fullscreen", "1", 0);
    Cvar_Get("r_mode", "21", 0);
    for (int i = 0; i < 2; ++i) {
        viddef.width = i ? 3840 : 1920; viddef.height = i ? 2160 : 1080;
        VID_MenuInit();
#ifdef YQ2_PS5
        char expected[32];
        snprintf(expected, sizeof(expected), "%dx%d (fixed)", viddef.width, viddef.height);
        assert(s_mode_list.generic.flags & QMF_INACTIVE);
        assert(!strcmp(s_mode_list.itemnames[0], expected) && s_mode_list.itemnames[1] == NULL);
        assert(s_fs_box.generic.flags & QMF_INACTIVE);
        s_opengl_menu.cursor = 1;
        VID_MenuKey(K_RIGHTARROW); VID_MenuKey(K_LEFTARROW); VID_MenuKey(K_ENTER);
        assert(s_mode_list.curvalue == 0);
        Menu_AdjustCursor(&s_opengl_menu, 1);
        assert(Menu_ItemAtCursor(&s_opengl_menu) != &s_mode_list);
        s_opengl_menu.cursor = 1;
        Menu_AdjustCursor(&s_opengl_menu, -1);
        assert(Menu_ItemAtCursor(&s_opengl_menu) != &s_mode_list);
        ApplyChanges(NULL);
        assert(!mode_writes && !fullscreen_writes && !restarts);
        ResetDefaults(NULL);
        assert(!strcmp(s_mode_list.itemnames[0], expected));
#else
        assert(!(s_mode_list.generic.flags & QMF_INACTIVE));
        s_mode_list.curvalue = GetModePos(29);
        ApplyChanges(NULL);
        assert(Cvar_Get("r_mode", "0", 0)->value == 29 && restarts == i + 1);
#endif
    }
    puts("PASS: actual menu initialization, navigation, Apply and reset");
}
'''
with tempfile.TemporaryDirectory() as folder:
    work = Path(folder)
    source = work / name
    source.parent.mkdir(parents=True)
    shutil.copyfile(upstream / name, source)
    subprocess.run(['git', 'apply', '--include=' + name,
                    str(root / 'patches/0001-ps5-static-gl3-lifecycle.patch')], cwd=work, check=True)
    code = re.sub(r'#include "([^"]+)"', lambda match:
                  '#include "' + str((upstream / name).parent.joinpath(match[1]).resolve()) + '"',
                  source.read_text())
    source.write_text(code + harness)
    for flags in ([], ['-DYQ2_PS5']):
        executable = work / 'video-menu'
        subprocess.run(['cc', '-std=gnu11', '-O1', '-ffunction-sections', '-fdata-sections',
                        '-DYQ2OSTYPE="test"', '-DYQ2ARCH="x86_64"',
                        '-fsanitize=address,undefined', '-Wl,--gc-sections', *flags,
                        str(source), str(upstream / 'src/client/menu/qmenu.c'),
                        '-lm', '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
