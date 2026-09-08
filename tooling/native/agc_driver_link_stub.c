/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Shared helper from BlackBearReloaded's PS5 OpenGL/native app projects.
 */

#include <stdint.h>

uint32_t sceAgcDriverGetWaitRenderingPacketSizeInDwords(void) { return 0; }
uint32_t sceAgcDriverWaitUntilSafeForRendering(uint32_t **command,
                                               uint32_t video_handle,
                                               uint32_t buffer_index,
                                               uint32_t generation,
                                               int mode)
{
    return command != 0 || video_handle || buffer_index || generation || mode;
}
int sceAgcDriverSubmitDcb(void *description) { return description ? -1 : 0; }
