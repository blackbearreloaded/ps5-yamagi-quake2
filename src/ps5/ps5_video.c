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

#define PS5_GL3_PLATFORM_VERSION 1
#define PS5_NATIVE_WIDTH 1920
#define PS5_NATIVE_HEIGHT 1080

extern refexport_t re;
extern viddef_t viddef;

float glimp_refreshRate = -1.0f;

static cvar_t *vid_displayrefreshrate;
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
	vid_displayrefreshrate = Cvar_Get("vid_displayrefreshrate", "-1", CVAR_ARCHIVE);
	Com_Printf("PS5 video: native fullscreen surface\n");
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
	*width = PS5_NATIVE_WIDTH;
	*height = PS5_NATIVE_HEIGHT;
	if (initialized)
	{
		re.GetDrawableSize(width, height);
		return *width > 0 && *height > 0;
	}
	if (re.PrepareForWindow() < 0 || !re.InitContext((void *)1))
		return false;
	re.GetDrawableSize(width, height);
	initialized = *width > 0 && *height > 0;
	if (!initialized)
	{
		Com_Printf("PS5: invalid drawable size %dx%d\n", *width, *height);
		re.ShutdownContext();
	}
	else
	{
		viddef.width = *width;
		viddef.height = *height;
		Com_Printf("PS5 video: drawable %dx%d\n", *width, *height);
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
	return vid_displayrefreshrate != NULL ? vid_displayrefreshrate->value : -1.0f;
}

qboolean
GLimp_GetDesktopMode(int *width, int *height)
{
	if (width == NULL || height == NULL)
		return false;
	*width = PS5_NATIVE_WIDTH;
	*height = PS5_NATIVE_HEIGHT;
	if (initialized)
		re.GetDrawableSize(width, height);
	return true;
}

int
GLimp_GetFrameworkVersion(void)
{
	return PS5_GL3_PLATFORM_VERSION;
}
