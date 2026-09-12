/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * PS5 contributions: Copyright (C) 2026 BlackBearReloaded.
 * Upstream copyright and license notices are retained below.
 * Adapted from Yamagi Quake II: src/client/vid/glimp_sdl2.c.
 */

/*
 * Copyright (C) 2010 Yamagi Burmeister
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

#include "../../upstream/yquake2/src/client/vid/header/ref.h"

#include <stdio.h>

#include "ps5_opengl_display.h"

#define PS5_GL3_PLATFORM_VERSION 1
#define PS5_NATIVE_WIDTH PS5_OPENGL_NATIVE_WIDTH
#define PS5_NATIVE_HEIGHT PS5_OPENGL_NATIVE_HEIGHT

extern refexport_t re;
extern viddef_t viddef;

float glimp_refreshRate = -1.0f;

static qboolean initialized;
static const char *display_indices[] = { "0", NULL };

const char **
GLimp_GetDisplayIndices(void)
{
	return display_indices;
}

int
GLimp_GetWindowDisplayIndex(void)
{
	return 0;
}

int
GLimp_GetNumVideoDisplays(void)
{
	return 1;
}

qboolean
GLimp_Init(void)
{
	cvar_t *mode = Cvar_Get("r_mode", "29", CVAR_ARCHIVE);
	if (mode->value != 21 && mode->value != 25 && mode->value != 29)
		Cvar_SetValue("r_mode", 29);
	Com_Printf("PS5 video: 1080p, 1440p or 2160p at %d Hz\n", PS5_OPENGL_NATIVE_FPS);
	return true;
}

void
GLimp_Shutdown(void)
{
	GLimp_ShutdownGraphics();
}

qboolean
GLimp_InitGraphics(int fullscreen, int *width, int *height)
{
	(void)fullscreen;
	if (width == NULL || height == NULL)
		return false;
	const int requested[2] = { *width, *height };
	if (!((requested[0] == 1920 && requested[1] == 1080) ||
		(requested[0] == 2560 && requested[1] == 1440) ||
		(requested[0] == 3840 && requested[1] == 2160)))
		return false;
	if (initialized)
	{
		re.GetDrawableSize(width, height);
		if (*width != requested[0] || *height != requested[1])
			return false;
		viddef.width = *width;
		viddef.height = *height;
		return true;
	}
	if (re.PrepareForWindow() < 0 || !re.InitContext((void *)requested))
		return false;
	re.GetDrawableSize(width, height);
	initialized = *width == requested[0] && *height == requested[1];
	if (!initialized)
	{
		Com_Printf("PS5: invalid drawable size %dx%d\n", *width, *height);
		re.ShutdownContext();
	}
	else
	{
		viddef.width = *width;
		viddef.height = *height;
	}
	return initialized;
}

void
GLimp_ShutdownGraphics(void)
{
	if (initialized)
		re.ShutdownContext();
	initialized = false;
}

void
GLimp_GrabInput(qboolean grab)
{
	(void)grab;
}

float
GLimp_GetRefreshRate(void)
{
	return PS5_OPENGL_NATIVE_FPS;
}

qboolean
GLimp_GetDesktopMode(int *width, int *height)
{
	if (width == NULL || height == NULL)
		return false;
	*width = PS5_NATIVE_WIDTH;
	*height = PS5_NATIVE_HEIGHT;
	if (initialized)
	{
		re.GetDrawableSize(width, height);
		return *width > 0 && *height > 0;
	}
	return true;
}

int
GLimp_GetFrameworkVersion(void)
{
	return PS5_GL3_PLATFORM_VERSION;
}
