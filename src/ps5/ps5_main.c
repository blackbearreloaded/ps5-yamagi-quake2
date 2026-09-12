/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * PS5 contributions: Copyright (C) 2026 BlackBearReloaded.
 * Upstream copyright and license notices are retained below.
 * Adapted from Yamagi Quake II: src/backends/unix/main.c.
 */

/*
 * Copyright (C) 1997-2001 Id Software, Inc.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 *
 */

/* Native application entry. Desktop CLI/terminal setup stays in upstream main. */
#define _POSIX_C_SOURCE 200809L
#include "../../upstream/yquake2/src/common/header/common.h"
#include "ps5_lifecycle.h"
#include "ps5_opengl_display.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

extern qboolean stdin_active;
#define PS5_STRINGIFY_INNER(value) #value
#define PS5_STRINGIFY(value) PS5_STRINGIFY_INNER(value)
void setCustomCfgDir(const char *dir);
int sceSystemServiceLoadExec(const char *path, const char **args);
_Noreturn void catchReturnFromMain(int status);

_Noreturn void ps5_exit(int status)
{
    /* The SDL PS5 entry uses this public native quit path. libc exit() is a
     * payload ABI import and produced SIGSYS in the observed game shutdown. */
    fflush(NULL);
    int error = sceSystemServiceLoadExec("exit", NULL);
    printf("[yamagi-ps5] native exit returned status=%d error=%x\n", status, error);
    catchReturnFromMain(status ? status : 1);
}

int main(void)
{
    char *args[] = { "yquake2", "+set", "vid_renderer", "gl3",
        "+set", "vid_fullscreen", "1", "+set", "r_vsync", "1",
        "+set", "vid_maxfps", PS5_STRINGIFY(PS5_OPENGL_NATIVE_FPS),
#ifdef YQ2_PS5_OPENING_BENCH
#ifdef YQ2_PS5_MODE_BENCH
        "+set", "r_mode", "29",
#endif
        "+set", "deathmatch", "0", "+set", "coop", "0",
        "+set", "maxclients", "1", "+map", "demo1",
#else
        "+menu_main",
#endif
        NULL };
    const char *save_dir = "/download0/yamagi";
    const char *probe = "/download0/yamagi/.write-check";
    struct stat info;
    printf("[yamagi-ps5] native entry\n");
    if ((mkdir(save_dir, 0700) != 0 && errno != EEXIST) ||
        stat(save_dir, &info) != 0 || !S_ISDIR(info.st_mode) ||
        setenv("HOME", "/download0", 1) != 0 || setenv("LC_ALL", "C", 1) != 0)
    {
        perror("[yamagi-ps5] prepare app save directory");
        return 1;
    }
    FILE *file = fopen(probe, "wb");
    if (!file) { perror("[yamagi-ps5] save directory is not writable"); return 1; }
    int written = fputs("yamagi\n", file) >= 0;
    int closed = fclose(file) == 0;
    if (!written || !closed || remove(probe) != 0) return 1;
    setCustomCfgDir("yamagi");
    Q_strlcpy(datadir, "/app0/assets", sizeof(datadir));
    stdin_active = false;
    Sys_SetupFPU();
    ps5_frame_start();
    printf("[yamagi-ps5] assets=%s saves=%s renderer=gl3\n", datadir, save_dir);
    Qcommon_Init((int)(sizeof(args) / sizeof(args[0])) - 1, args);
    return 1; /* Qcommon_Init owns the engine loop and normal quit path. */
}
