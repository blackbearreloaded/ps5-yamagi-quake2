#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Real SDL queued-tap regression and native game/level save path round trips."""
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
headers = root / ".deps/pacbrew/v0.40.2/sysroot/user/homebrew/include/SDL2"
if not headers.is_dir():
    headers = Path('/usr/include/SDL2')
input_test = r'''
#include <SDL2/SDL.h>
#include <assert.h>
int ps5_input_start(void);
void ps5_input_stop(void);
static void tap(SDL_Joystick *joy) {
    assert(!SDL_JoystickSetVirtualButton(joy, 0, 1)); SDL_Delay(40);
    assert(!SDL_JoystickSetVirtualButton(joy, 0, 0)); SDL_Delay(40);
}
static int edges(void) {
    SDL_Event event; int down = 0, up = 0;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_JOYBUTTONDOWN) ++down;
        if (event.type == SDL_JOYBUTTONUP) ++up;
    }
    assert(down == up);
    return down;
}
int main(void) {
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    assert(!SDL_Init(SDL_INIT_JOYSTICK | SDL_INIT_EVENTS));
    int device = SDL_JoystickAttachVirtual(SDL_JOYSTICK_TYPE_GAMECONTROLLER, 6, 16, 1);
    assert(device >= 0);
    SDL_Joystick *joy = SDL_JoystickOpen(device); assert(joy);
    SDL_JoystickUpdate(); SDL_FlushEvents(SDL_FIRSTEVENT, SDL_LASTEVENT);
    tap(joy); assert(edges() == 0); /* Old once-per-frame polling loses the tap. */
    for (int cycle = 0; cycle < 3; ++cycle) {
        assert(ps5_input_start()); assert(ps5_input_start());
        tap(joy); ps5_input_stop(); ps5_input_stop();
        assert(edges() == 1); /* Both edges survive while the game thread waits. */
    }
    SDL_JoystickClose(joy); SDL_JoystickDetachVirtual(device); SDL_Quit();
}
'''
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)
    (path / "SDL2").symlink_to(headers)
    (path / "input.c").write_text(input_test)
    subprocess.run(["clang", "-std=gnu11", "-O2", "-I", folder,
                    str(path / "input.c"), str(root / "src/ps5/ps5_input.c"),
                    "-l:libSDL2-2.0.so.0", "-o", str(path / "input")], check=True)
    subprocess.run([str(path / "input")], check=True)

    relative = Path("src/server/sv_save.c")
    source = path / relative
    source.parent.mkdir(parents=True)
    source.write_bytes((root / "upstream/yquake2" / relative).read_bytes())
    source.chmod(0o644)
    subprocess.run(["git", "apply", f"--include={relative.as_posix()}",
                    str(root / "patches/0001-ps5-static-gl3-lifecycle.patch")], cwd=folder, check=True)
    branches = [s for s in re.findall(r"#ifdef YQ2_PS5\n(.*?)#else", source.read_text(), re.S)
                if "ge->" in s]
    assert len(branches) == 4
    harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#define Com_sprintf snprintf
static char gamedir[4096];
static const char *FS_Gamedir(void) { return gamedir; }
static struct { const char *name; } sv = { "demo1" };
static void write_file(const char *name) {
    assert(name[0] == '/' && strstr(name, gamedir) == name);
    assert(!strncmp(name + strlen(gamedir), "/save/current/", 14));
    FILE *file = fopen(name, "wb"); assert(file);
    assert(fputs("roundtrip", file) >= 0); assert(!fclose(file));
}
static void read_file(const char *name) {
    char text[32] = {0}; FILE *file = fopen(name, "rb"); assert(file);
    assert(fread(text, 1, 9, file) == 9 && !strcmp(text, "roundtrip"));
    assert(!fclose(file));
}
static void write_game(const char *name, bool autosave) { assert(autosave); write_file(name); }
static struct { void (*WriteLevel)(const char *); void (*ReadLevel)(const char *);
    void (*WriteGame)(const char *, bool); void (*ReadGame)(const char *);
} api = {write_file, read_file, write_game, read_file}, *ge = &api;
'''
    for index, branch in enumerate(branches):
        assert "Sys_GetWorkDir" not in branch and "Sys_SetWorkDir" not in branch
        harness += f"static void operation{index}(void) {{ char name[4096]; bool autosave = true;\n{branch}\n}}\n"
    harness += "int main(void) { assert(getcwd(gamedir, sizeof(gamedir))); assert(!chdir(\"/\")); operation0(); operation1(); operation2(); operation3(); }\n"
    (path / "save/current").mkdir(parents=True)
    (path / "saves.c").write_text(harness)
    subprocess.run(["clang", "-std=gnu11", "-O2", "-fsanitize=address,undefined",
                    str(path / "saves.c"), "-o", str(path / "saves")], check=True)
    subprocess.run([str(path / "saves")], cwd=folder, check=True)
print("PASS: queued short taps, repeated input start/stop, game and level save path round trips")
