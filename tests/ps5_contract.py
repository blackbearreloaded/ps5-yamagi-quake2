# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path


root = Path(__file__).resolve().parents[1]
egl = (root / "src/ps5/ps5_egl.c").read_text(encoding="utf-8")
gl3 = (root / "src/ps5/ps5_gl3.c").read_text(encoding="utf-8")

assert "EGLNativeWindowType)0, NULL" in egl
assert "EGL_CONTEXT_MAJOR_VERSION_KHR, 3" in egl
assert "EGL_CONTEXT_MINOR_VERSION_KHR, 3" in egl
assert "EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT_KHR" in egl
assert "EGL_DEPTH_SIZE, 24" in egl and "EGL_STENCIL_SIZE, 8" in egl
assert "eglMakeCurrent" in egl and "eglDestroyContext" in egl
assert "gladLoadGLLoader" in gl3 and "ps5_gl3_check_required_functions" in gl3
assert "gl3config.useBigVBO" in gl3 and "ps5_egl_swap" in gl3

print("PASS: PS5 EGL/GL3 adapter contract")
