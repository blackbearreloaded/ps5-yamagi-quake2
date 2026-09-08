#!/usr/bin/env python3
# PS5 Yamagi Quake II - Native Quake II port for PlayStation 5.
# Copyright (C) 2026 BlackBearReloaded
# SPDX-License-Identifier: GPL-3.0-or-later

"""Host regression for the actual patched Sys_Realpath; no console or GPU."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
relative = Path("src/backends/unix/system.c")
with tempfile.TemporaryDirectory(prefix="yamagi-realpath-patch-") as folder:
    source = Path(folder) / relative
    source.parent.mkdir(parents=True)
    shutil.copy2(root / "upstream/yquake2" / relative, source)
    source.chmod(0o644)  # Preserve Git's source-file mode across WSL mounts.
    subprocess.run(["git", "apply", f"--include={relative.as_posix()}",
                    str(root / "patches/0001-ps5-static-gl3-lifecycle.patch")], cwd=folder, check=True)
    text = source.read_text()
start = text.index("qboolean\nSys_Realpath(")
end = text.index("\n}\n", start) + 3
function = text[start:end]
harness = r'''
#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE 1
#define YQ2_PS5 1
#include <assert.h>
#include <errno.h>
#include <limits.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
typedef bool qboolean;
static unsigned calls;
static int reject;
static int regular_file;
static char diagnostic[1024];
static const char canonical[] = "/download0/yamagi";
void Com_Printf(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    vsnprintf(diagnostic, sizeof(diagnostic), format, args);
    va_end(args);
}
size_t Q_strlcpy(char *out, const char *in, size_t size)
{
    size_t length = strlen(in);
    if (size) {
        size_t count = length < size - 1 ? length : size - 1;
        memcpy(out, in, count);
        out[count] = 0;
    }
    return length;
}
static int mock_stat(const char *in, struct stat *out)
{
    ++calls;
    assert(!strcmp(in, canonical) || !strcmp(in, "/app0") || !strcmp(in, "/app0/assets"));
    if (reject) { errno = EACCES; return -1; }
    out->st_mode = regular_file ? S_IFREG : S_IFDIR;
    return 0;
}
#define stat(path, info) mock_stat(path, info)
''' + function + r'''
int main(void)
{
    const char *input = "/download0/yamagi/";
    char output[PATH_MAX];
    memset(output, 'X', sizeof(output));
    assert(Sys_Realpath(input, output, sizeof(output)));
    assert(calls == 1 && !strcmp(output, canonical));
    assert(Sys_Realpath(input, output, sizeof(canonical)));
    assert(Sys_Realpath("/app0/", output, sizeof(output)) && !strcmp(output, "/app0"));
    assert(Sys_Realpath("/app0/assets", output, sizeof(output)) && !strcmp(output, "/app0/assets"));
    unsigned valid_calls = calls;
    const char *invalid[] = {"", ".", "/download0/./yamagi", "/app0/../download0", "/app0/assets-other", "/other"};
    for (unsigned i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i)
        assert(!Sys_Realpath(invalid[i], output, sizeof(output)));
    assert(calls == valid_calls);
    memset(output, 'X', sizeof(output));
    assert(!Sys_Realpath(input, output, sizeof(canonical) - 1));
    assert(output[0] == 'X'); /* Reject truncation, do not return a different path. */
    assert(!Sys_Realpath(input, output, 0));
    reject = 1;
    assert(!Sys_Realpath(input, output, sizeof(output)));
    assert(output[0] == 'X');
    reject = 0;
    regular_file = 1;
    assert(!Sys_Realpath(input, output, sizeof(output)) && output[0] == 'X');
    puts("PASS: native search roots, directory checks, unknown paths and output bounds");
    return 0;
}
'''
compiler = os.environ.get("CC") or shutil.which("clang-18") or shutil.which("cc")
if not compiler:
    raise SystemExit("A host C compiler is required")
with tempfile.TemporaryDirectory(prefix="yamagi-realpath-") as folder:
    temporary = Path(folder)
    generated = temporary / "realpath.c"
    executable = temporary / "realpath"
    generated.write_text(harness)
    subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                    str(generated), "-o", str(executable)], check=True)
    subprocess.run([executable], check=True)
