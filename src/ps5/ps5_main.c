/* Native application entry. Desktop CLI/terminal setup stays in upstream main. */
#define _POSIX_C_SOURCE 200809L
#include "../../upstream/yquake2/src/common/header/common.h"
#include "ps5_lifecycle.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

extern qboolean stdin_active;
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
        "+set", "vid_maxfps", "60", "+menu_main", NULL };
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
