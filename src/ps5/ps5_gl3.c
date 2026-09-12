/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * PS5 contributions: Copyright (C) 2026 BlackBearReloaded.
 * Upstream copyright and license notices are retained below.
 * Adapted from Yamagi Quake II: src/client/refresh/gl3/gl3_sdl.c.
 */

/*
 * Copyright (C) 1997-2001 Id Software, Inc.
 * Copyright (C) 2016-2017 Daniel Gibson
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

#include "../../upstream/yquake2/src/client/refresh/gl3/header/local.h"
#include "ps5_egl.h"
#include "ps5_lifecycle.h"

#include <EGL/eglext.h>
#include <stdio.h>
#include <string.h>

#define PS5_GL3_PLATFORM_VERSION 1

static ps5_egl_state_t egl_state;
static qboolean vsync_active;
qboolean IsHighDPIaware = false;
extern refimport_t ri;

static struct {
	long long draw_us, buffer_us, clear_us, previous_us;
	long long stage_start, stage_us[5];
	unsigned draws, frames;
} profile;
static PFNGLDRAWARRAYSPROC native_draw_arrays;
static PFNGLDRAWELEMENTSPROC native_draw_elements;
static PFNGLDRAWARRAYSINSTANCEDPROC native_draw_arrays_instanced;
static PFNGLBUFFERDATAPROC native_buffer_data;
static PFNGLCLEARPROC native_clear;

void PS5_RenderStage(unsigned stage)
{
	long long now = Sys_Microseconds();
	if (stage > 0 && stage <= 5)
		profile.stage_us[stage - 1] += now - profile.stage_start;
	profile.stage_start = now;
}

static void APIENTRY profile_draw_arrays(GLenum mode, GLint first, GLsizei count)
{
	long long start = Sys_Microseconds();
	native_draw_arrays(mode, first, count);
	profile.draw_us += Sys_Microseconds() - start;
	++profile.draws;
}

static void APIENTRY profile_draw_elements(GLenum mode, GLsizei count, GLenum type, const void *indices)
{
	long long start = Sys_Microseconds();
	native_draw_elements(mode, count, type, indices);
	profile.draw_us += Sys_Microseconds() - start;
	++profile.draws;
}

static void APIENTRY profile_draw_arrays_instanced(GLenum mode, GLint first, GLsizei count, GLsizei instances)
{
	long long start = Sys_Microseconds();
	native_draw_arrays_instanced(mode, first, count, instances);
	profile.draw_us += Sys_Microseconds() - start;
	++profile.draws;
}

static void APIENTRY profile_buffer_data(GLenum target, GLsizeiptr size, const void *data, GLenum usage)
{
	long long start = Sys_Microseconds();
	/* Mesa otherwise reuses same-sized storage via buffer_subdata. The frozen
	 * native driver must drain readers before that write. Explicit orphaning
	 * gives queued draws their own retained storage without changing barriers. */
	if (data && size > 0 && (usage == GL_STREAM_DRAW || usage == GL_DYNAMIC_DRAW))
		native_buffer_data(target, size, NULL, usage);
	native_buffer_data(target, size, data, usage);
	profile.buffer_us += Sys_Microseconds() - start;
}

static void APIENTRY profile_clear(GLbitfield mask)
{
	long long start = Sys_Microseconds();
	native_clear(mask);
	profile.clear_us += Sys_Microseconds() - start;
}

static void profile_frame(long long swap_us)
{
	long long now = Sys_Microseconds();
	long long total = profile.previous_us ? now - profile.previous_us : 0;
	++profile.frames;
	if (profile.frames <= 10 || profile.frames % 60 == 0 || total > 1000000)
	{
		fprintf(stderr, "[yamagi-profile] frame=%u draws=%u total_us=%lld draw_us=%lld buffer_us=%lld clear_us=%lld swap_us=%lld world_us=%lld entities_us=%lld particles_us=%lld alpha_us=%lld post_us=%lld underwater=%d\n",
			profile.frames, profile.draws, total, profile.draw_us, profile.buffer_us, profile.clear_us, swap_us,
			profile.stage_us[0], profile.stage_us[1], profile.stage_us[2], profile.stage_us[3],
			profile.stage_us[4], (r_newrefdef.rdflags & RDF_UNDERWATER) != 0);
		fflush(stderr);
	}
	profile.draw_us = profile.buffer_us = profile.clear_us = 0;
	profile.draws = 0;
	memset(profile.stage_us, 0, sizeof(profile.stage_us));
	profile.previous_us = Sys_Microseconds();
}

#define PS5_REQUIRED_GL_FUNCTIONS(X) \
	X(glActiveTexture) \
	X(glAttachShader) \
	X(glBindBuffer) \
	X(glBindBufferBase) \
	X(glBindBufferRange) \
	X(glBindFramebuffer) \
	X(glBindRenderbuffer) \
	X(glBindTexture) \
	X(glBindVertexArray) \
	X(glBlendEquation) \
	X(glBlendFunc) \
	X(glBufferData) \
	X(glBufferSubData) \
	X(glCheckFramebufferStatus) \
	X(glClear) \
	X(glClearColor) \
	X(glColorMask) \
	X(glCompileShader) \
	X(glCreateProgram) \
	X(glCreateShader) \
	X(glCullFace) \
	X(glDeleteBuffers) \
	X(glDeleteFramebuffers) \
	X(glDeleteProgram) \
	X(glDeleteRenderbuffers) \
	X(glDeleteShader) \
	X(glDeleteTextures) \
	X(glDeleteVertexArrays) \
	X(glDepthFunc) \
	X(glDepthMask) \
	X(glDisable) \
	X(glDisableVertexAttribArray) \
	X(glDrawArrays) \
	X(glDrawArraysInstanced) \
	X(glDrawElements) \
	X(glEnable) \
	X(glEnableVertexAttribArray) \
	X(glFramebufferRenderbuffer) \
	X(glFramebufferTexture2D) \
	X(glGenBuffers) \
	X(glGenFramebuffers) \
	X(glGenRenderbuffers) \
	X(glGenTextures) \
	X(glGenVertexArrays) \
	X(glGenerateMipmap) \
	X(glGetActiveUniformBlockiv) \
	X(glGetIntegerv) \
	X(glGetProgramInfoLog) \
	X(glGetProgramiv) \
	X(glGetShaderInfoLog) \
	X(glGetShaderiv) \
	X(glGetString) \
	X(glGetStringi) \
	X(glGetUniformBlockIndex) \
	X(glGetUniformLocation) \
	X(glLinkProgram) \
	X(glMapBufferRange) \
	X(glPixelStorei) \
	X(glReadPixels) \
	X(glRenderbufferStorage) \
	X(glScissor) \
	X(glShaderSource) \
	X(glStencilFunc) \
	X(glStencilMask) \
	X(glStencilOp) \
	X(glTexImage2D) \
	X(glTexParameteri) \
	X(glTexSubImage2D) \
	X(glUniform1f) \
	X(glUniform1i) \
	X(glUniform2f) \
	X(glUniform4f) \
	X(glUniform4fv) \
	X(glUniformBlockBinding) \
	X(glUnmapBuffer) \
	X(glUseProgram) \
	X(glVertexAttribIPointer) \
	X(glVertexAttribPointer) \
	X(glVertexAttribDivisor) \
	X(glViewport)

static int
ps5_gl3_check_required_functions(void)
{
#define CHECK_GL_FUNCTION(name) \
	if (glad_##name == NULL) { \
		fprintf(stderr, "[ps5-gl3] missing GL entry point: %s\n", #name); \
		return 0; \
	}
	PS5_REQUIRED_GL_FUNCTIONS(CHECK_GL_FUNCTION)
#undef CHECK_GL_FUNCTION
	return 1;
}

void
GL3_EndFrame(void)
{
	GL3_FlushChars();
	if (gl3config.useBigVBO)
	{
		GL3_BindVAO(gl3state.vao3D);
		GL3_BindVBO(gl3state.vbo3D);
		glBufferData(GL_ARRAY_BUFFER, gl3state.vbo3Dsize, NULL, GL_STREAM_DRAW);
		gl3state.vbo3DcurOffset = 0;
	}
	long long swap_start = Sys_Microseconds();
	if (!ps5_egl_swap(&egl_state))
		Com_Error(ERR_FATAL, "PS5 presentation failed");
	profile_frame(Sys_Microseconds() - swap_start);
	ps5_record_present();
}

qboolean
GL3_IsVsyncActive(void)
{
	return vsync_active;
}

void
GL3_SetVsync(void)
{
	int requested = (r_vsync != NULL && r_vsync->value != 0) ? 1 : 0;

	if (!ps5_egl_set_swap_interval(&egl_state, requested))
	{
		Com_Printf("PS5: failed to set swap interval %d\n", requested);
		vsync_active = false;
		return;
	}
	vsync_active = requested != 0;
}

int
GL3_PrepareForWindow(void)
{
	if (gl_msaa_samples != NULL && gl_msaa_samples->value != 0)
	{
		Com_Printf("PS5: MSAA is not part of the initial fixed EGL config; disabling it\n");
		ri.Cvar_SetValue("r_msaa_samples", 0);
	}
	gl3config.stencil = true;
	return 1;
}

int
GL3_InitContext(void *window_token)
{
	const int *size = window_token;
	if (size == NULL || !ps5_egl_open(&egl_state, 0, size[0], size[1]))
		return false;
	if (!gladLoadGLLoader((GLADloadproc)ps5_egl_get_proc_address) ||
		GLVersion.major != 3 || GLVersion.minor < 3 ||
		!ps5_gl3_check_required_functions())
	{
		Com_Printf("PS5: OpenGL 3.3 Core entry-point load failed\n");
		ps5_egl_close(&egl_state);
		return false;
	}
	gl3config.major_version = GLVersion.major;
	gl3config.minor_version = GLVersion.minor;
	gl3config.renderer_string = (const char *)glGetString(GL_RENDERER);
	gl3config.vendor_string = (const char *)glGetString(GL_VENDOR);
	gl3config.version_string = (const char *)glGetString(GL_VERSION);
	gl3config.glsl_version_string = (const char *)glGetString(GL_SHADING_LANGUAGE_VERSION);
	gl3config.debug_output = GLAD_GL_ARB_debug_output != 0;
	gl3config.anisotropic = GLAD_GL_EXT_texture_filter_anisotropic != 0;
	gl3config.stencil = true;
	native_draw_arrays = glad_glDrawArrays;
	native_draw_elements = glad_glDrawElements;
	native_draw_arrays_instanced = glad_glDrawArraysInstanced;
	native_buffer_data = glad_glBufferData;
	native_clear = glad_glClear;
	glad_glDrawArrays = profile_draw_arrays;
	glad_glDrawElements = profile_draw_elements;
	glad_glDrawArraysInstanced = profile_draw_arrays_instanced;
	glad_glBufferData = profile_buffer_data;
	glad_glClear = profile_clear;
	memset(&profile, 0, sizeof(profile));
	GL3_SetVsync();
	return true;
}

void
GL3_GetDrawableSize(int *width, int *height)
{
	if (!ps5_egl_query_size(&egl_state, width, height))
	{
		if (width != NULL)
			*width = 0;
		if (height != NULL)
			*height = 0;
	}
}

void
GL3_ShutdownContext(void)
{
	if (!ps5_egl_close(&egl_state))
	{
		Com_Printf("PS5: EGL shutdown reported an error\n");
		ps5_record_failure();
	}
	else
	{
		/* The static renderer survives vid_restart; GL object names do not. */
		memset(&gl3state, 0, sizeof(gl3state));
	}
	vsync_active = false;
}

int
GL3_GetSDLVersion(void)
{
	return PS5_GL3_PLATFORM_VERSION;
}
