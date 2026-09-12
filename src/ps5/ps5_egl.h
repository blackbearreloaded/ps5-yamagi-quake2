/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef YQ2_PS5_EGL_H
#define YQ2_PS5_EGL_H

#include <EGL/egl.h>

typedef struct
{
	EGLDisplay display;
	EGLSurface surface;
	EGLContext context;
	EGLint width;
	EGLint height;
	int requested_swap_interval;
	int accepted_swap_interval;
} ps5_egl_state_t;

int ps5_egl_open(ps5_egl_state_t *state, int swap_interval, int width, int height);
int ps5_egl_set_swap_interval(ps5_egl_state_t *state, int swap_interval);
int ps5_egl_query_size(const ps5_egl_state_t *state, int *width, int *height);
int ps5_egl_swap(ps5_egl_state_t *state);
void *ps5_egl_get_proc_address(const char *name);
int ps5_egl_close(ps5_egl_state_t *state);

#endif
