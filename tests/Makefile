# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

# Compile/link check only. This ELF is not a native folder application.
SHELL := bash
.DEFAULT_GOAL := all
include $(PS5_PAYLOAD_SDK)/toolchain/prospero.mk
include $(PS5_OPENGL_PREFIX)/share/ps5-opengl-core33/ps5-opengl-core33.mk

.PHONY: all
all: build/sdk-consumer.elf build/app_heap.o build/runtime_shims.o

build:
	mkdir -p $@

build/sdk_consumer.o: tests/sdk_consumer.c tests/Makefile | build
	$(CC) -std=c11 -Os -g -Wall -Wextra -Werror $(PS5_OPENGL_PUBLIC_CFLAGS) -c -o $@ $<

build/sdk-consumer.elf: build/sdk_consumer.o
	$(CXX) -o $@ $< $(PS5_OPENGL_LDLIBS) $(PS5_OPENGL_LDFLAGS)

build/%.o: tooling/native/%.c tests/Makefile | build
	$(CC) -std=c11 -Os -g -Wall -Wextra -Werror -c -o $@ $<
