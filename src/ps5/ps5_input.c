/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <SDL2/SDL.h>

static SDL_Thread *input_thread;
static SDL_atomic_t input_running;

static int poll_controller(void *unused)
{
    (void)unused;
    while (SDL_AtomicGet(&input_running)) {
        /* SDL serializes joystick updates and queues events under its locks.
         * Keep short presses while the game thread waits for rendering. */
        SDL_JoystickUpdate();
        SDL_Delay(4);
    }
    return 0;
}

int ps5_input_start(void)
{
    if (input_thread) return 1;
    SDL_AtomicSet(&input_running, 1);
    input_thread = SDL_CreateThread(poll_controller, "gamepad", NULL);
    if (!input_thread) SDL_AtomicSet(&input_running, 0);
    return input_thread != NULL;
}

void ps5_input_stop(void)
{
    SDL_AtomicSet(&input_running, 0);
    if (input_thread) SDL_WaitThread(input_thread, NULL);
    input_thread = NULL;
}
