#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise the actual three-mode menu, navigation and renderer restart requests."""
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
static int variable_count, mode_writes, fullscreen_writes, restarts, config_writes, saved_mode;
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
void CL_WriteConfiguration(void) { ++config_writes; saved_mode = Cvar_VariableValue("r_mode"); }
void Cbuf_AddText(char *text) { assert(!strcmp(text, "vid_restart\n")); ++restarts; }

int main(void) {
    vid_renderer = Cvar_Get("vid_renderer", "gl3", 0);
    vid_fullscreen = Cvar_Get("vid_fullscreen", "1", 0);
    Cvar_Get("r_mode", "21", 0);
    const int widths[] = {1920,2560,3840}, heights[] = {1080,1440,2160}, native_modes[] = {21,25,29};
    for (int i = 0; i < 3; ++i) {
        viddef.width = widths[i]; viddef.height = heights[i];
        Cvar_SetValue("r_mode", native_modes[i]);
        VID_MenuInit();
#ifdef YQ2_PS5
        char expected[32];
        snprintf(expected, sizeof(expected), "%dx%d (120Hz)", viddef.width, viddef.height);
        assert(!(s_mode_list.generic.flags & QMF_INACTIVE));
        assert(!strcmp(s_mode_list.itemnames[i], expected) && s_mode_list.itemnames[3] == NULL);
        assert(s_mode_list.curvalue == i);
        assert(s_fs_box.generic.flags & QMF_INACTIVE);
        s_opengl_menu.cursor = 1;
        s_mode_list.curvalue = 0;
        VID_MenuKey(K_RIGHTARROW); assert(s_mode_list.curvalue == 1);
        VID_MenuKey(K_LEFTARROW); assert(s_mode_list.curvalue == 0);
        s_mode_list.curvalue = i;
        Menu_AdjustCursor(&s_opengl_menu, 1);
        assert(Menu_ItemAtCursor(&s_opengl_menu) == &s_mode_list);
        Menu_AdjustCursor(&s_opengl_menu, -1);
        assert(Menu_ItemAtCursor(&s_opengl_menu) == &s_mode_list);
        int writes = mode_writes, previous_restarts = restarts;
        int previous_saves = config_writes;
        ApplyChanges(NULL);
        assert(mode_writes == writes && !fullscreen_writes && restarts == previous_restarts);
        assert(config_writes == previous_saves);
        s_mode_list.curvalue = (i + 1) % 3;
        ApplyChanges(NULL);
        assert(mode_writes == writes + 1 && restarts == previous_restarts + 1);
        assert(Cvar_Get("r_mode", "0", 0)->value == native_modes[(i + 1) % 3]);
        assert(config_writes == previous_saves + 1 && saved_mode == native_modes[(i + 1) % 3]);
        s_mode_list.curvalue = 3;
        ApplyChanges(NULL);
        assert(mode_writes == writes + 1 && restarts == previous_restarts + 1);
        assert(config_writes == previous_saves + 1);
        ResetDefaults(NULL);
        assert(s_mode_list.curvalue == i && !strcmp(s_mode_list.itemnames[i], expected));
#else
        assert(!(s_mode_list.generic.flags & QMF_INACTIVE));
        s_mode_list.curvalue = GetModePos(29);
        ApplyChanges(NULL);
        assert(Cvar_Get("r_mode", "0", 0)->value == 29 && restarts == i + 1);
        assert(!config_writes);
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
