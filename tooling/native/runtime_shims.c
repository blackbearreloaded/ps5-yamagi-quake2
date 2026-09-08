/*
 * PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
 * Copyright (C) 2026 BlackBearReloaded
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Shared helper from BlackBearReloaded's PS5 OpenGL/native app projects.
 */

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern int sceKernelUsleep(uint32_t microseconds);

static char stdout_buffer[65536];
static char stderr_buffer[65536];

__attribute__((constructor)) static void pss_opengl_open_log(void) {
  FILE *stream = freopen("/download0/pss-opengl.log", "w", stdout);
  /* Start a fresh receipt, then make both independent streams append-only. */
  if (stream != NULL)
    stream = freopen("/download0/pss-opengl.log", "a", stdout);
  if (stream != NULL)
    setvbuf(stream, stdout_buffer, _IOFBF, sizeof(stdout_buffer));
  stream = freopen("/download0/pss-opengl.log", "a", stderr);
  if (stream != NULL)
    setvbuf(stream, stderr_buffer, _IOFBF, sizeof(stderr_buffer));
}

__attribute__((noreturn)) void catchReturnFromMain(int status) {
  printf("[pss-opengl-native] gate completed status=%d\n", status);
  fflush(NULL);
  for (;;)
    sceKernelUsleep(100000);
}

void pss_opengl_glapi_tls_context_init(void) __asm__(
    "_ZTH23_mesa_glapi_tls_Context");

void pss_opengl_glapi_tls_context_init(void) {}

__attribute__((noreturn)) void __assert(const char *function, const char *file,
                                        int line, const char *expression) {
  fprintf(stderr, "assertion failed: %s (%s:%d, %s)\n", expression, file, line,
          function);
  abort();
}

int mkstemps(char *template_name, int suffix_length) {
  (void)template_name;
  (void)suffix_length;
  errno = ENOSYS;
  return -1;
}

void openlog(const char *identifier, int option, int facility) {
  (void)identifier;
  (void)option;
  (void)facility;
}

FILE *popen(const char *command, const char *mode) {
  (void)command;
  (void)mode;
  errno = ENOSYS;
  return NULL;
}

int pclose(FILE *stream) {
  (void)stream;
  errno = ENOSYS;
  return -1;
}
