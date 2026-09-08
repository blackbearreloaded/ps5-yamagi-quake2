/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "ps5_egl.h"

#include <EGL/eglext.h>

#include <stdio.h>

static void
ps5_egl_log_error(const char *operation)
{
	fprintf(stderr, "[ps5-egl] %s failed: 0x%04x\n", operation,
		(unsigned)eglGetError());
}

static void
ps5_egl_reset(ps5_egl_state_t *state)
{
	*state = (ps5_egl_state_t){
		.display = EGL_NO_DISPLAY,
		.surface = EGL_NO_SURFACE,
		.context = EGL_NO_CONTEXT,
		.requested_swap_interval = -1,
		.accepted_swap_interval = -1,
	};
}

int
ps5_egl_open(ps5_egl_state_t *state, int swap_interval)
{
	static const EGLint config_attributes[] = {
		EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
		EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
		EGL_RED_SIZE, 8,
		EGL_GREEN_SIZE, 8,
		EGL_BLUE_SIZE, 8,
		EGL_ALPHA_SIZE, 8,
		EGL_DEPTH_SIZE, 24,
		EGL_STENCIL_SIZE, 8,
		EGL_NONE,
	};
	static const EGLint context_attributes[] = {
		EGL_CONTEXT_MAJOR_VERSION_KHR, 3,
		EGL_CONTEXT_MINOR_VERSION_KHR, 3,
		EGL_CONTEXT_OPENGL_PROFILE_MASK_KHR,
		EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR,
		EGL_NONE,
	};
	EGLConfig config = NULL;
	EGLint major = 0;
	EGLint minor = 0;
	EGLint count = 0;

	if (state == NULL || (swap_interval != 0 && swap_interval != 1))
		return 0;

	ps5_egl_reset(state);
	state->requested_swap_interval = swap_interval;
	state->display = eglGetDisplay(EGL_DEFAULT_DISPLAY);
	if (state->display == EGL_NO_DISPLAY)
	{
		ps5_egl_log_error("eglGetDisplay");
		goto fail;
	}
	if (!eglInitialize(state->display, &major, &minor))
	{
		ps5_egl_log_error("eglInitialize");
		goto fail;
	}
	if (!eglBindAPI(EGL_OPENGL_API))
	{
		ps5_egl_log_error("eglBindAPI");
		goto fail;
	}
	if (!eglChooseConfig(state->display, config_attributes, &config, 1, &count) ||
		count != 1)
	{
		ps5_egl_log_error("eglChooseConfig");
		goto fail;
	}

	/* The frozen PS5 backend owns the window; handle 0 and NULL attributes are required. */
	state->surface = eglCreateWindowSurface(state->display, config,
		(EGLNativeWindowType)0, NULL);
	if (state->surface == EGL_NO_SURFACE)
	{
		ps5_egl_log_error("eglCreateWindowSurface");
		goto fail;
	}
	state->context = eglCreateContext(state->display, config, EGL_NO_CONTEXT,
		context_attributes);
	if (state->context == EGL_NO_CONTEXT)
	{
		ps5_egl_log_error("eglCreateContext");
		goto fail;
	}
	if (!eglMakeCurrent(state->display, state->surface, state->surface,
		state->context))
	{
		ps5_egl_log_error("eglMakeCurrent");
		goto fail;
	}
	if (!ps5_egl_query_size(state, &state->width, &state->height))
		goto fail;
	if (!ps5_egl_set_swap_interval(state, swap_interval))
		goto fail;

	fprintf(stdout, "[ps5-egl] EGL %d.%d, surface %dx%d, swap interval %d\n",
		major, minor, state->width, state->height,
		state->accepted_swap_interval);
	return 1;

fail:
	ps5_egl_close(state);
	return 0;
}

int
ps5_egl_set_swap_interval(ps5_egl_state_t *state, int swap_interval)
{
	if (state == NULL || state->display == EGL_NO_DISPLAY ||
		state->surface == EGL_NO_SURFACE ||
		(swap_interval != 0 && swap_interval != 1))
		return 0;
	if (!eglSwapInterval(state->display, swap_interval))
	{
		ps5_egl_log_error("eglSwapInterval");
		return 0;
	}
	state->requested_swap_interval = swap_interval;
	state->accepted_swap_interval = swap_interval;
	return 1;
}

int
ps5_egl_query_size(const ps5_egl_state_t *state, int *width, int *height)
{
	if (state == NULL || width == NULL || height == NULL ||
		state->display == EGL_NO_DISPLAY || state->surface == EGL_NO_SURFACE ||
		!eglQuerySurface(state->display, state->surface, EGL_WIDTH, width) ||
		!eglQuerySurface(state->display, state->surface, EGL_HEIGHT, height) ||
		*width <= 0 || *height <= 0)
	{
		ps5_egl_log_error("eglQuerySurface");
		return 0;
	}
	return 1;
}

int
ps5_egl_swap(ps5_egl_state_t *state)
{
	if (state == NULL || state->display == EGL_NO_DISPLAY ||
		state->surface == EGL_NO_SURFACE ||
		!eglSwapBuffers(state->display, state->surface))
	{
		ps5_egl_log_error("eglSwapBuffers");
		return 0;
	}
	return 1;
}

void *
ps5_egl_get_proc_address(const char *name)
{
	return (void *)eglGetProcAddress(name);
}

int
ps5_egl_close(ps5_egl_state_t *state)
{
	int ok = 1;

	if (state == NULL)
		return 0;
	if (state->display != EGL_NO_DISPLAY && state->context != EGL_NO_CONTEXT &&
		!eglMakeCurrent(state->display, EGL_NO_SURFACE, EGL_NO_SURFACE,
		EGL_NO_CONTEXT))
	{
		ps5_egl_log_error("eglMakeCurrent(shutdown)");
		ok = 0;
	}
	if (state->display != EGL_NO_DISPLAY && state->context != EGL_NO_CONTEXT &&
		!eglDestroyContext(state->display, state->context))
	{
		ps5_egl_log_error("eglDestroyContext");
		ok = 0;
	}
	if (state->display != EGL_NO_DISPLAY && state->surface != EGL_NO_SURFACE &&
		!eglDestroySurface(state->display, state->surface))
	{
		ps5_egl_log_error("eglDestroySurface");
		ok = 0;
	}
	if (state->display != EGL_NO_DISPLAY && !eglTerminate(state->display))
	{
		ps5_egl_log_error("eglTerminate");
		ok = 0;
	}
	ps5_egl_reset(state);
	return ok;
}
