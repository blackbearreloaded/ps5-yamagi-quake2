#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise optional native resolver imports, both absent and available."""
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
header = (root / "src/ps5/ps5_net_compat.h").read_text()
# Rename imports so the host libc cannot accidentally satisfy the absent case.
for name in ("getaddrinfo", "freeaddrinfo", "gai_strerror"):
    header = re.sub(r"\b" + name + r"\b", "test_" + name, header)
harness = r'''
#define _POSIX_C_SOURCE 200809L
#include <netdb.h>
#include <assert.h>
#include <string.h>
extern int test_getaddrinfo(const char *, const char *, const struct addrinfo *, struct addrinfo **);
extern void test_freeaddrinfo(struct addrinfo *);
extern const char *test_gai_strerror(int);
#include "compat.h"
#undef test_getaddrinfo
#undef test_gai_strerror
#ifdef AVAILABLE
static struct addrinfo answer;
int test_getaddrinfo(const char *n, const char *s, const struct addrinfo *h, struct addrinfo **r)
{ assert(!strcmp(n, "host")); *r = &answer; return 0; }
void test_freeaddrinfo(struct addrinfo *r) { assert(r == &answer); }
const char *test_gai_strerror(int e) { return "test error"; }
#endif
int main(void) {
    struct addrinfo *result = (void *)1;
    int error = ps5_getaddrinfo("host", "27910", 0, &result);
#ifdef AVAILABLE
    assert(!error && result == &answer);
    test_freeaddrinfo(result);
    assert(!strcmp(ps5_gai_strerror(1), "test error"));
#else
    assert(error == EAI_SYSTEM && result == 0 && errno == ENOSYS);
    assert(strstr(ps5_gai_strerror(error), "unavailable"));
#endif
}
'''
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)
    (path / "compat.h").write_text(header)
    (path / "test.c").write_text(harness)
    for flags in ([], ["-DAVAILABLE"]):
        subprocess.run(["clang", "-std=gnu11", "-O2", "-fsanitize=address,undefined",
                        *flags, str(path / "test.c"), "-o", str(path / "test")], check=True)
        subprocess.run([str(path / "test")], check=True)
print("Native resolver: missing imports fail normally; available imports work")
